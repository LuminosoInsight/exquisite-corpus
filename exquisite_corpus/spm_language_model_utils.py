import numpy as np
import torch
import torch.nn as nn

from exquisite_corpus.spm_dataset import SpmIdsBatchMaker


class SpmIdsBatchMakerForLanguageModels(SpmIdsBatchMaker):
    """
    Subclass of SpmIdsBatchMaker which produces batches of items from its
    underlying dataset along with labels suitable for training a language
    model.  For each sequence of ids in a batch, the corresponding sequence
    of labels is the sequence of following ids which the model is learning
    to predict (so for the sequence i0, i1, i2 the labels are i1, i2, i3,
    which means we must return batches of sequences shorter by one id than
    the actual sequences in the dataset).  The only difference from a plain
    SpmIdsBatchMaker is that the collated batches returned are pairs of tensors,
    the first being the (shortened) data items from the data set and the second
    being the corresponding labels.

    Typical usage for this class (in training a language model):

        model = <some-kind-of-language-model>
        loss_function = SpmIdsLanguageModelLoss()
        optimizer = <some-kind-of-torch-optimizer>
        batch_maker = SpmIdsBatchMakerForLanguageModels(
                        <path-to-dataset>,
                        min_length=2,
                        batch_size=512,
                        n_data_loader_workers=10
                      )
        for _ in range(n_epocs):
            for batch, labels in batch_maker:
                model.zero_grad()
                predictions = model(batch)
                loss = loss_function(predictions, labels)
                loss.backward()
                optimizer.step()
    """

    def __init__(self, npy_directory, min_length=2, *args, **kwargs):
        """
        Constructor for SpmIdsBatchMakerForLanguageModels.

        Arguments:
            The same as for SpmIdsBatchMaker, except that the min_length
            argument must be 2 or more for an SpmIdsBatchMakerForLanguageModels.
        """
        if min_length < 2:
            raise ValueError("min_length {} invalid for language models.")
        super().__init__(npy_directory, min_length, *args, **kwargs)

    def place_batch(self, batch):
        """
        Moves a batch to the target device.

        Arguments:
            batch:
                The batch to be moved (required).  Its type must be a pair of
                tensors (the first representing the data of the batch, and the
                second the corresponding labels).

        Returns a pair of tensors, namely copies of the input data and labels
        on the target device.
        """
        placed_data = batch[0].to(self.target_device)
        placed_labels = batch[1].to(self.target_device)
        return placed_data, placed_labels

    def collate_batch(self, raw_batch):
        """
        Take a raw batch of items (sequences of ids) from the dataset, and
        separate it into a batch of shortened items (the "data") and the
        corresponding labels.

        Arguments:
            raw_batch:
                The batch of sequences of ids (as a list of 1D numpy arrays,
                each a sequence of SentencePiece ids).  Required.

        Returns a pair of 2D tensors.  The first is the batch of sequences
        (one sequence per row), each having its last entry removed, which
        can be passed to a language model as input.  The second is the batch
        of sequences (again one per row), each having its first entry removed,
        which are the ground-truth labels a language model will try to predict.
        """
        data = torch.tensor(np.vstack([x[:-1] for x in raw_batch]))
        labels = torch.tensor(np.vstack([x[1:] for x in raw_batch]))
        return data, labels


class SpmIdsLossFunctionForLanguageModels(nn.Module):
    """
    Module to compute the aggregate NLLLoss of a batch of predictions from a
    language model, which produces for each batch of multiple sequences (of
    uniform length) of tokens, predictions for every sequence of the batch
    and every position within the sequence of the log-probability of each
    possible following token.

    The loss is aggregated over all elements of a batch, and all sequence
    positions within each element.
    """

    def __init__(self, reduction="mean"):
        """
        Initialize by setting up an NLLLoss module with the given reduction
        strategy.  Reduction will be applied over all elements of input batches
        as well as over all sequence positions within each item of a batch.

        Arguments:
            reduction:
                The reduction strategy used to combine losses at all positions
                of each batch item to a single scalar loss.  Any value
                permissible for the "reduction" argument to an nn.NLLLoss
                module may be used (e.g. "mean" or "sum").  Defaults to "mean".
        """
        super().__init__()
        self.loss_fn = nn.NLLLoss(reduction=reduction)

    def forward(self, predictions, labels):
        """
        Given a batch of predictions derived from a batch of data by a
        language model, and a corresponding batch of ground-truth labels,
        compute the NLLLoss for every prediction and combine the collected
        losses to a scalar value (using the reduction set up when this object
        was constructed).

        Arguments:
            predictions:
                The batch of predictions (required).  A 3D FloatTensor whose
                (i,j,k) entry is the predicted log-probability that the i-th
                item of the batch has, at sequence position j, the
                SentencePiece id k.
            labels:
                The batch of ground-truth labels (required).  A 2D tensor whose
                (i,j) entry is the SentencePiece id at sequence position j of
                the i-th item in the data batch.

        Returns the reduced NLLLoss (a zero-D FloatTensor).
        """
        loss = self.loss_fn(
            predictions.view(labels.numel(), -1), labels.to(torch.int64).view(-1)
        )
        return loss
