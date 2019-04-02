import copy
import torch
import torch.cuda.comm as comm
import torch.nn as nn


class DataParallelizedModule(nn.Module):
    """
    Similarly to nn.DataParallel, this class of modules serves to wrap
    other modules and run them in parallel over multiple gpus, splitting
    training (or testing/application) batches between the gpus (over the
    given dimension of the batch, which is assumed to correspond to data
    points within the batch).

    Unlike nn.DataParallel, all of the wrapped module's parameters will be
    copied to all gpus during construction of the wrapper, and only gradient
    data will be copied from gpu to gpu during training (no data should need
    to be copied between gpus during forward application).  However, training
    should only use loss functions that can be expressed as averages over all
    data points of a batch of some per-data-point loss.  Each training batch
    must be presented as a tuple of tensors all of which have equal sizes (or
    at least sizes in fixed proportions) in dimension 0 (corresponding to the
    points in the batch).  Also, the set of parameters of the wrapped module
    is assumed not to change (of course their values can change) over the
    lifetime of the wrapper object.

    Note that during training of a wrapped module, it is necessary to call
    the wrapper's broadcast_gradients method immediately following the
    backpropagation of gradients (i.e. typically right after calling
    .backward on some loss tensor), in order to share corrections to the
    computed gradients between the gpus.

    Specifically, if L is the average loss over an entire (mini-)batch, of
    size n data points, that batch is scattered over k gpus as chunks of
    sizes n_0, ..., n_(k-1) (with sum equal to n), and L_i is the average loss
    over the i-th chunk, then L = w_0 * L_0 + ... + w_k-1 * L_(k-1), where
    w_i = n_i / n, and so for any parameter p

        dL/dp = w_0 dL_0/dp + ... + w_(k-1) * dL_(k-1)/dp.

    The broadcast_gradients method collects the individual pieces of gradient
    data dL_i/dp from all the gpus, computes the unified gradient data dL/dp
    (for every parameter) and updates the gradients on every gpu.
    """

    def __init__(
        self,
        module,
        device=torch.device("cuda:0"),
        copy_fn=copy.deepcopy,
        dim=0,
        calls_between_synchronizations=1000,
    ):
        """
        Construct a parallelizing wrapper for the given module (an instance
        of nn.Module).  The module will be moved to the given device (if
        not already there) and copies will be made using the given copy
        function (which should accept a module and return a copy of the
        module suitable for placement on a gpu; the default is copy.deepcopy)
        and moved to all other available gpus.
        """
        super().__init__()
        self.dim = dim  # save teh dimension on which to scatter input

        # If the requested device is the cpu, or there is only one gpu,
        # don't parallelize.
        if (
            device == torch.device("cpu")
            or not torch.cuda.is_available()
            or torch.cuda.device_count() < 2
        ):
            self.module_copies = [module]
            self.devices = [device]
            module.to(device)
            self.add_module("child:{0}", module)
            self.chunk_sizes = torch.zeros(1, dtype=torch.int64)
            self.call_count = 0
            self.calls_between_synchronizations = calls_between_synchronizations
            return

        device_ids = list(range(torch.cuda.device_count()))
        devices = [torch.device("cuda:{}".format(d_id)) for d_id in device_ids]
        if device not in devices:
            device = devices[0]
        self.module_copies = [module]  # put the original copy first
        self.devices = [device]  # the original copy will end up on this device

        # Register the child as a submodule of the wrapper, so that the
        # autograd machinery will update its parameters when the forward
        # method of the wrapper is called.
        self.add_module("child:{}".format(device.index), module)

        # Save a list of all available devices (with the one corresponding to
        # the original wrapped module first).
        for dev in devices:
            if dev != device:
                self.devices.append(dev)

        # Make a copy for each additional device, put it on the corresponding
        # device, and register it as a submodule.
        for dev in self.devices[1:]:
            module.cpu()  # in case the copy_fn moved it
            module_copy = copy_fn(module)
            module_copy.to(dev)  # in case the copy_fn didn't move the copy
            self.module_copies.append(module_copy)
            self.add_module("child:{}".format(dev.index), module_copy)

        # Put the original copy on the requested device.
        module.to(device)

        # During forward evaluation of the wrapper it is necessary to keep
        # track of the sizes of the chunks of the input batch(es) that are
        # handed off to each child.  So we create a 1D tensor holding those
        # sizes.
        self.chunk_sizes = torch.zeros(len(self.module_copies), dtype=torch.int64)

        # Keep track of a count of backward calls (used to periodically
        # resynchronize the children).
        self.call_count = 0
        self.calls_between_synchronizations = calls_between_synchronizations

    def __del__(self):
        """
        Ensure that any memory allocated on GPU's is freed when this
        module is no longer referenced.
        """
        for child in self.module_copies[1:]:
            del child
        torch.cuda.empty_cache()

    @property
    def device(self):
        """
        The nominal device of a parallelized module is the first device used.
        """
        return self.devices[0]

    def forward(self, *args):
        """
        Scatter the supplied args (assumed to be a list of tensors) across
        the child modules, and gather their outputs (assumed to be single
        tensors) back to the first gpu.  Also, accumulate the sizes of the
        scattered chunks (for later use in updating parameter gradients).
        """
        # We assume the input argument tensors have proportional sizes in
        # the splitting dimension, so any of them can be used as representative
        # of the size of the input batch, and it chunks as representative of
        # the sizes of the chunks
        representative = 0

        if len(self.module_copies) <= 1:
            return self.module_copies[0](*args)

        device_ids = [device.index for device in self.devices]

        # Scatter each arg across the (multiple) devices.  For each arg,
        # calling comm.scatter gives us a tuple of chunks, one chunk on each
        # device.  We populate a list (with length equal to the number of
        # devices) whose entries are lists (with length equal to the number
        # of args) of the chunks on each device.
        chunk_lists = list(list() for i_device in device_ids)
        for arg in args:
            chunks = comm.scatter(arg, device_ids)
            for i_child, chunk in enumerate(chunks):
                chunk_lists[i_child].append(chunk)

        # In order to apply the child modules to the appropriate collections
        # of arg chunks, convert each list of chunks on one device to a tuple.
        chunks = list(tuple(chunk_list) for chunk_list in chunk_lists)

        # Now we can apply the children modules to the chunks of data.  We
        # collect the outputs in a list, and also update the running tally
        # of the sizes of the chunks processed by each child.
        outputs = []
        for i_child, (module, chunk) in enumerate(zip(self.module_copies, chunks)):
            chunk_size = chunk[representative].size()[self.dim]
            self.chunk_sizes[i_child] += chunk_size
            output = module(*chunk)
            outputs.append(output)
        assert len(self.module_copies) == len(outputs)

        # Finally, we put the separate outputs of the children together into
        # a unified (concatenated) output, and place it on the first device.
        output = comm.gather(outputs, destination=self.devices[0].index)
        return output

    def zero_grad(self):
        """
        In addition to the ordinary zeroing of gradient data, reset the
        chunk size data. and periodically resync the children's params.
        """
        self.call_count += 1
        if self.call_count >= self.calls_between_synchronizations:
            self.call_count = 0
            self.synchronize_module_copies()

        super().zero_grad()
        self.chunk_sizes = torch.zeros(len(self.module_copies), dtype=torch.int64)

    def broadcast_gradients(self):
        """
        Compute a single value, for all the child modules, of the gradient
        of each module parameter (as a convex combination of the gradients
        in the individual children, with coefficients proportional to the
        batch chunk sizes from the forward computation), and distribute these
        common gradients back to all the children.
        """
        if len(self.module_copies) <= 1:
            return

        # Compute the coefficients of the convex combination, proportional to
        # the sizes of the chunks of the batch that were processed by each
        # child.
        weights = self.chunk_sizes.to(torch.float32)
        weights /= weights.sum()
        weights = [weights[i_device].item() for i_device in range(len(self.devices))]

        # Update each parameter's gradients on all children.
        for i_param, param in enumerate(self.module_copies[0].parameters()):
            if param.grad is None:
                continue
            param_copies = [param]

            # Collect the other children's copies of this parameter in a list.
            for other_module in self.module_copies[1:]:
                other_module_params = list(other_module.parameters())
                param_copies.append(other_module_params[i_param])

            # Find the sum, over all child modules, of the gradient for this
            # parameter in the child, multiplied by the corresponding weights
            # (as determined above by the relative sizes of the batch chunks
            # processed by each child), and place it on the first device.
            param_grad = comm.reduce_add(
                list(
                    param_copy.grad.mul_(weight)
                    for param_copy, weight in zip(param_copies, weights)
                ),
                destination=self.devices[0].index,
            )

            # Now send the weighted sum to all the child modules on their
            # devices, replacing their values of the parameter's gradient.
            for i_param_copy, param_copy in enumerate(param_copies):
                if param_copy.grad.layout == torch.sparse_coo:
                    # Explicitly assigning to a sparse grad is verboten, so
                    # work around that by calling 'backward'.
                    update = param_grad.to(self.devices[i_param_copy]) - param_copy.grad
                    param_copy.backward(update)
                    assert (
                        param_copy.grad - param_grad.to(self.devices[i_param_copy])
                    ).coalesce().values().flatten().abs().max().item() < 1e-6
                else:
                    param_copy.grad = param_grad.to(self.devices[i_param_copy])

    def synchronize_module_copies(self, tolerance=5e-6):
        """
        In principle, if broadcast_gradients is called on every training step,
        the child modules should always agree on all parameters.  In practice,
        some optimizers sometimes introduce slight discrepancies (e.g.
        optim.SGD with sparse gradients, which does not coalesce such gradients
        at every step).  This method can be called periodically to reset the
        parameters of all children to the values of the first child (the
        original module), and to print warnings if the parameters have diverged
        by more than the given (absolute) tolerance.
        """
        model = self.module_copies[0]
        for child, device in zip(self.module_copies[1:], self.devices[1:]):
            for param, child_param in zip(model.parameters(), child.parameters()):
                param_data_cpu = param.data.cpu()
                child_param_data_cpu = child_param.data.cpu()
                difference = (
                    (param_data_cpu - child_param_data_cpu).flatten().abs().max()
                )
                if difference > tolerance:
                    print(
                        "Parameter difference {} exceeds tolerance.".format(difference)
                    )
                # Copy the param to the child (but first free up space).
                child_param.data = child_param.data.new_empty((0,))
                child_param.data = param_data_cpu.to(device)
            # (Re)flatten the data in any RNN's inside the chilren.
            child.apply(
                lambda m: m.flatten_parameters()
                if hasattr(m, "flatten_parameters")
                else None
            )
