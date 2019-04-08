import click
import json
import numpy as np
import sys
import time
import torch
import torch.multiprocessing as mp
import torch.nn as nn

from exquisite_corpus.spm_dataset import SpmIdsBatchSampler, SpmIdsDataset
from pathlib import Path
from torch.nn.parallel import DistributedDataParallel
from torch.utils.data import DataLoader


class LanguageModel(nn.Module):
    """
    Since this is just to illustrate how one might set up a language model
    using SentencePiece ids, we use a very simple model rather than a good one.
    """

    def __init__(
        self,
        n_tokens,
        n_dims=300,
        hidden_size=500,
        num_layers=1,
        bias=True,
        dropout=0.0,
        bidirectional=False,
        sparse=False,
    ):
        super().__init__()
        self.encoder = nn.Embedding(n_tokens, n_dims, sparse=bool(sparse))
        self.rnn = nn.GRU(
            input_size=n_dims,
            hidden_size=hidden_size,
            num_layers=num_layers,
            bias=bool(bias),
            batch_first=True,
            dropout=dropout,
            bidirectional=bool(bidirectional),
        )
        n_rnn_out_features = hidden_size * (2 if bidirectional else 1)
        self.decoder = nn.Linear(in_features=n_rnn_out_features, out_features=n_tokens)
        self.log_softmax = nn.LogSoftmax(dim=2)

    def forward(self, input, hidden_states=None, return_hidden=False):
        batch_size = input.size(0 if self.rnn.batch_first else 1)
        n_directions = 2 if self.rnn.bidirectional else 1
        full_num_layers = self.rnn.num_layers * n_directions
        if hidden_states is None:
            hidden_states = torch.zeros(
                full_num_layers, batch_size, self.rnn.hidden_size
            ).to(input.device, non_blocking=True)
        output = input
        output = self.encoder(output)
        output, new_hidden_states = self.rnn(
            output,
            hidden_states.view(full_num_layers, batch_size, self.rnn.hidden_size),
        )
        output = self.decoder(output)
        output = self.log_softmax(output)
        if return_hidden:
            new_hidden_states = new_hidden_states.view(hidden_states.size())
            return output, new_hidden_states
        else:
            return output


class LossFunction(nn.Module):
    """
    Module to compute the aggregate (over all elements of a batch, and all
    sequence positions within each element) loss.
    """

    def __init__(self, reduction="mean"):
        super().__init__()
        self.loss_fn = nn.NLLLoss(reduction=reduction)

    def forward(self, input, target):
        return self.loss_fn(input.view(target.numel(), -1), target.view(-1))


class ModelManager:
    """
    Objects that own torch models (modules) and provide convenience methods
    for their training and use.
    """

    def __init__(
        self,
        model=None,
        device=torch.device("cuda:0"),
        use_multiple_gpus=False,
        **kwargs
    ):
        if model is None:
            self.model = LanguageModel(**kwargs)
        else:
            self.model = model
        self.device = device
        self.use_multiple_gpus = use_multiple_gpus

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, new_device):
        if isinstance(new_device, str):
            new_device = torch.device(new_device)
        if new_device != torch.device("cpu") and not torch.cuda.is_available():
            print("Warning:  cuda not available so setting device to CPU.")
            self._device = torch.device("cpu")
        else:
            self._device = new_device
        self.model.to(self._device)

    def collate_batch_with_labels(self, raw_batch):
        """
        Take a raw batch (as returned by a DataLoader and SpmIdsBatchSampler),
        collate it, and split off labels.
        """
        data = torch.LongTensor(np.vstack([x[:-1] for x in raw_batch]))
        labels = torch.LongTensor(np.vstack([x[1:] for x in raw_batch]))
        return data, labels

    def train(
        self,
        train_dataset_path,
        validation_dataset_path=None,
        save_path=None,
        min_length=2,
        n_epochs=np.inf,
        n_batches_between_saves=1000,
        n_batches_between_messages=50,
        n_batches_between_validations=25000,
        batch_size=256,
        n_data_loader_workers=0,
        lr=0.05,
        device=None,
        use_multiple_gpus=None,
    ):
        if device is not None:
            self.device = device
        if use_multiple_gpus is not None:
            self.use_multiple_gpus = use_multiple_gpus

        loss_function = LossFunction()

        if self.use_multiple_gpus:
            model = DistributedDataParallel(self.model, device_ids=[self.device.index])
            loss_function = DistributedDataParallel(
                loss_function, device_ids=[self.device.index]
            )
            # Each batch of data will be shared/sharded among the gpus.
            n_devices = torch.cuda.device_count()
            share_index = self.device.index
        else:
            model = self.model
            n_devices = 1
            share_index = 0

        model.train()
        if min_length < 2:
            raise ValueError("Cannot train with sentences shorter than 2 tokens.")
        train_data = SpmIdsDataset(train_dataset_path, min_length=min_length)
        sampler = SpmIdsBatchSampler(
            train_data,
            batch_size=batch_size,
            n_shares=n_devices,
            share_index=share_index,
        )
        pin_memory = self.device != torch.device("cpu")
        data_loader = DataLoader(
            train_data,
            batch_sampler=sampler,
            pin_memory=pin_memory,
            num_workers=n_data_loader_workers,
            collate_fn=self.collate_batch_with_labels,
        )
        if validation_dataset_path is None:
            validation_data = None
        else:
            validation_data = SpmIdsDataset(
                validation_dataset_path, min_length=min_length
            )
            validation_sampler = SpmIdsBatchSampler(
                validation_data,
                batch_size=batch_size,
                n_shares=n_devices,
                share_index=share_index,
                randomize=False,
            )
            validation_data_loader = DataLoader(
                validation_data,
                batch_sampler=validation_sampler,
                pin_memory=pin_memory,
                num_workers=n_data_loader_workers,
                collate_fn=self.collate_batch_with_labels,
            )

        optimizer = torch.optim.SGD(model.parameters(), lr=lr)
        start_time = time.time()
        n_data_points = 0
        i_epoch = 0
        while i_epoch < n_epochs:  # 'for i_epoch in range(np.inf)' would fail
            i_epoch += 1
            self.print("Starting training epoch {}.".format(i_epoch))
            total_training_loss = 0.0
            for i_batch, (batch, labels) in enumerate(data_loader, start=1):
                batch = batch.to(self.device, non_blocking=True)
                labels = labels.to(self.device, non_blocking=True)
                model.zero_grad()
                prediction = model(batch)
                loss = loss_function(prediction, labels)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1)
                optimizer.step()

                # If a reduction other than 'mean' is used in the loss fucntion,
                # it would be necessary to thange the following accounting.
                n_labels = labels.numel() * n_devices
                total_training_loss += loss.item() * n_labels
                n_data_points += n_labels

                if i_batch % n_batches_between_messages == 0:
                    self.print(
                        "Mean training loss at epoch {}, batch {} is {}; "
                        "training time {} sec.".format(
                            i_epoch,
                            i_batch,
                            total_training_loss / n_data_points,
                            time.time() - start_time,
                        )
                    )

                if i_batch % n_batches_between_saves == 0:
                    self.print("Saving model to {}.".format(save_path))
                    self.save(save_path)

                if (
                    i_batch % n_batches_between_validations == 0
                ) and validation_data is not None:
                    self.print("Computing validation loss.")
                    with torch.autograd.no_grad():
                        n_validation_points = 0
                        validation_loss = 0.0
                        model.eval()
                        for i_vdtn_batch, (batch, labels) in enumerate(
                            validation_data_loader, start=1
                        ):
                            batch = batch.to(self.device, non_blocking=True)
                            labels = labels.to(self.device, non_blocking=True)
                            prediction = model(batch)
                            loss = loss_function(prediction, labels)
                            # Again we assume the loss has a 'mean' reduction.
                            n_labels = labels.numel() * n_devices
                            validation_loss += loss.item() * n_labels
                            n_validation_points += n_labels
                            if i_vdtn_batch % n_batches_between_messages == 0:
                                self.print(
                                    "Epoch {}, {} labels running loss is {}; "
                                    "training time {} sec.".format(
                                        i_epoch,
                                        n_validation_points,
                                        validation_loss / n_validation_points,
                                        time.time() - start_time,
                                    )
                                )
                        validation_loss /= n_validation_points  # overall mean
                        model.train()
                        self.print(
                            "Mean validation loss is {}.".format(validation_loss)
                        )

            if save_path is not None:
                self.print("Saving model to {}.".format(save_path))
                self.save(save_path)

        self.print("Finished {} training epochs.".format(n_epochs))
        if save_path is not None:
            self.print("Saving model to {}.".format(save_path))
            self.save(save_path)

    def test(
        self,
        test_dataset_path,
        batch_size=256,
        n_data_loader_workers=0,
        min_length=2,
        device=None,
        use_multiple_gpus=None,
    ):
        """
        Simple test method that just computes the perplexity on
        a test dataset.  Assumes that the model outputs are log prababilities.
        """
        if device is not None:
            self.device = device
        if use_multiple_gpus is not None:
            self.use_multiple_gpus = use_multiple_gpus

        nll_loss = LossFunction(reduction="sum")

        if self.use_multiple_gpus:
            model = DistributedDataParallel(self.model, device_ids=[self.device.index])
            nll_loss = DistributedDataParallel(nll_loss, device_ids=[self.device.index])
            # Each batch of data will be shared/sharded among the gpus.
            n_devices = torch.cuda.device_count()
            share_index = self.device.index
        else:
            model = self.model
            n_devices = 1
            share_index = 0

        model.eval()
        test_data = SpmIdsDataset(test_dataset_path, min_length=min_length)
        sampler = SpmIdsBatchSampler(
            test_data,
            batch_size=batch_size,
            n_shares=n_devices,
            share_index=share_index,
            randomize=False,
        )
        pin_memory = self.device != torch.device("cpu")
        data_loader = DataLoader(
            test_data,
            batch_sampler=sampler,
            pin_memory=pin_memory,
            num_workers=n_data_loader_workers,
            collate_fn=self.collate_batch_with_labels,
        )
        n_labels = torch.tensor(0, dtype=torch.int64, device=self.device)
        minus_log_prob_sum = torch.tensor(0.0, dtype=torch.float32, device=self.device)
        with torch.autograd.no_grad():
            for batch, labels in data_loader:
                batch = batch.to(self.device, non_blocking=True)
                labels = labels.to(self.device, non_blocking=True)
                log_probs = model(batch)
                minus_log_prob_sum += nll_loss(log_probs, labels)
                n_labels += labels.numel() * n_devices
                perplexity = (minus_log_prob_sum / n_labels).exp().item()
                self.print(
                    "Processed {} labels; running perplexity is {}.".format(
                        n_labels, perplexity
                    )
                )
        perplexity = (minus_log_prob_sum / n_labels).exp().item()
        self.print("Perplexity on {} is {}.".format(test_dataset_path, perplexity))
        return perplexity

    def print(self, msg):
        if self.use_multiple_gpus and self.device.index != 0:
            return
        print(msg)

    def is_sparse(self):
        return self.model.encoder.sparse

    def save(self, path):
        if self.use_multiple_gpus and self.device.index != 0:
            return  # only one process should save
        # we deliberately don't save device or use_multiple_gpus
        mgr_kwargs = dict(
            n_tokens=self.model.encoder.num_embeddings,
            n_dims=self.model.encoder.embedding_dim,
            sparse=self.model.encoder.sparse,
            hidden_size=self.model.rnn.hidden_size,
            num_layers=self.model.rnn.num_layers,
            bias=self.model.rnn.bias,
            dropout=self.model.rnn.dropout,
            bidirectional=self.model.rnn.bidirectional,
        )
        model_state_dict = self.model.state_dict()
        torch.save([mgr_kwargs, model_state_dict], str(path))

    @classmethod
    def load(cls, path, device=torch.device("cuda:0"), use_multiple_gpus=False):
        # In the past we've seen issues with excessive GPU memory consumption
        # when loading models direct to GPU, so we load to CPU first then move.
        mgr_kwargs, model_state_dict = torch.load(str(path), map_location="cpu")
        mgr_kwargs.update(device=torch.device("cpu"))  # load to cpu
        mgr_kwargs.update(use_multiple_gpus=use_multiple_gpus)
        result = cls(**mgr_kwargs)
        result.model.load_state_dict(model_state_dict)
        result.device = device  # move to requested or saved device if any
        return result


def task_worker(device_id, model_path, model_kwargs, task, task_kwargs):
    if device_id < 1:  # if there are multiple workers only let the first print

        def print_once(msg):
            print(msg)

    else:

        def print_once(msg):
            pass

    if device_id == -1:
        # multiple gpus not in use
        use_multiple_gpus = False
        device = task_kwargs.pop("device", torch.device("cuda:0"))
        if not torch.cuda.is_available():
            print_once("Cuda unavailable; using CPU.")
            device = torch.device("cpu")
    else:
        # multple gpus in use
        use_multiple_gpus = True
        torch.cuda.set_device(device_id)
        device = torch.device("cuda", device_id)
        task_kwargs.pop("device")  # overriden by use_multiple_gpus
        n_gpus = torch.cuda.device_count()
        # Connect to the other workers.
        torch.distributed.init_process_group(
            backend="nccl",
            init_method="tcp://127.0.0.1:27182",
            world_size=n_gpus,
            rank=device_id,
        )

    if model_path is not None and model_path.exists():
        print_once("Loading model from {}.".format(model_path))
        model_mgr = ModelManager.load(
            model_path, device=device, use_multiple_gpus=use_multiple_gpus
        )
    elif model_kwargs is not None:
        print_once("Making a new model from kwargs {}.".format(model_kwargs))
        model_mgr = ModelManager(
            device=device, use_multiple_gpus=use_multiple_gpus, **model_kwargs
        )
    else:
        print_once(
            "Error; must specify an existing model or give kwargs to make a new one."
        )
        return

    if model_mgr.is_sparse() and use_multiple_gpus:
        print_once("Error: cannot use multiple gpus with a sparse model.")
        return

    if task == "train":
        print_once("Training model with kwargs {}.".format(task_kwargs))
        model_mgr.train(**task_kwargs)
    elif task == "test":
        print_once("Testing model with kwargs {}.".format(task_kwargs))
        model_mgr.test(**task_kwargs)
    else:
        print_once("Unknown task {}.".format(task))


_HELP_STRING = """
Script to run a language model for spm ids.  Accepts a single
command-line argument specifying the path to a configuration file;
specify '-' to use stdin.  This file must contain the JSON
representation of a dictionary with some subset of the keys
'model_path', 'model_kwargs', 'task', and 'task_kwargs'.  Either
"model_path (to use an existing model) or model_kwargs (used to
construct a new model manager) must be given.  Valid values for
'task' are 'train' and 'test'.  Any task_kwargs given will be passed
to the corresponding method of a ModelManager object.

For example the following configuration file will train a model saved
at the givnen model_path, if that file exists, or else create and
train a new model with a vocabulary of 8000 SentencePiece tokens.
Training sentences shorter than 5 tokens will be discarded.
Every 500 batches a checkpoint of the model will be saved at the given
save_path (which may but need not be the same as the model_path):

\b
{
    "model_path": "data/sentencepiece/en.spm_lang_model.pt",
    "model_kwargs": {
        "n_tokens": 8000,
        "num_layers": 5,
        "dropout": 0.5,
        "sparse": false
    },
    "task": "train",
    "task_kwargs": {
        "train_dataset_path":
            "data/sentencepiece/en.spm_ids_training",
        "validation_dataset_path":
            "data/sentencepiece/en.spm_ids_validation",
        "save_path": "data/sentencepiece/en.spm_lang_model.pt",
        "n_batches_between_saves": 500,
        "min_length": 5,
        "batch_size": 256,
        "n_data_loader_workers": 10
    }
}

As another example, the following configuration file will perform
a test of the model saved at the given model_path:

\b
{
    "model_path": "data/sentencepiece/en.spm_lang_model.pt",
    "task": "test",
    "task_kwargs": {
        "test_dataset_path":
            "data/sentencepiece/en.spm_ids_testing",
        "min_length": 5,
        "batch_size": 256,
        "n_data_loader_workers": 10,
        "device": "cuda:0"
    }
}

"""


@click.command(help=_HELP_STRING)
@click.argument(
    "config-file",
    type=click.Path(exists=True, dir_okay=False, allow_dash=True, path_type=str),
)
def spm_naive_language_model(config_file):
    if config_file == "-":
        config = json.load(sys.stdin)
    else:
        with open(config_file, "rt", encoding="utf-8") as fp:
            config = json.load(fp)
    model_path = config.get("model_path")
    if model_path is not None:
        model_path = Path(model_path)
    model_kwargs = config.get("model_kwargs", {})
    task = config.get("task")
    if task is None:
        print("Error:  must specify a task.")
        return
    task_kwargs = config.get("task_kwargs", {})
    use_multiple_gpus = task_kwargs.pop("use_multiple_gpus", False)
    multple_gpus_available = torch.cuda.is_available() and torch.cuda.device_count() > 1
    if use_multiple_gpus and not multple_gpus_available:
        print("Multple GPUs requesetd but unavailable.")
        use_multiple_gpus = False
    if use_multiple_gpus:
        n_gpus = torch.cuda.device_count()
        mp.spawn(
            task_worker,
            nprocs=n_gpus,
            args=(model_path, model_kwargs, task, task_kwargs),
        )
    else:
        task_worker(-1, model_path, model_kwargs, task, task_kwargs)


if __name__ == "__main__":
    # To enable multiprocessing DataLoaders along with multiple GPUs, one
    # must set the multiprocessing start method to "spawn" or "forkserver".
    # (Spawn is likely slower but gives better messages if there are errors.)
    # Somehow torch.multiprocessing seems to end up trying to set the
    # start methord more than once (don't ask me how); a work-around is
    # to catch the resulting RuntimeErrors.
    try:
        pass #mp.set_start_method("spawn")
    except RuntimeError:
        pass  # already set
    spm_naive_language_model()
