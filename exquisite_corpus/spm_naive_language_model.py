import click
import json
import numpy as np
import sys
import torch
import torch.nn as nn

from exquisite_corpus.spm_dataset import SpmIdsBatchSampler, SpmIdsDataset
from pathlib import Path
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
        self.log_softmax = nn.LogSoftmax(dim=1)

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
        # Take the last feature of the feature sequence computed by the RNN.
        if self.rnn.batch_first:
            output = output[:, -1, :].squeeze(dim=1)
        else:
            output = output[-1, :, :].squeeze(dim=0)
        output = self.decoder(output)
        output = self.log_softmax(output)
        if return_hidden:
            new_hidden_states = new_hidden_states.view(hidden_states.size())
            return output, new_hidden_states
        else:
            return output


def make_loss_function():
    """
    Returns a callable that computes losses from predictions and labels.
    This simple implementation just provides negative log likelihood loss,
    but could be seasoned to taste.
    """
    return nn.NLLLoss()


class ModelManager:
    """
    Objects that own torch models (modules) and provide convenience methods
    for their training and use.
    """

    def __init__(self, model=None, device=torch.device("cuda:0"), **kwargs):
        if model is None:
            self.model = LanguageModel(**kwargs)
        else:
            self.model = model
        self.device = device

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
        labels = torch.LongTensor(np.vstack([x[-1] for x in raw_batch])).squeeze(dim=1)
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
        n_data_loader_threads=0,
        lr=0.05,
        device=torch.device("cuda:0"),
    ):
        self.device = device
        self.model.train()
        if min_length < 2:
            raise ValueError("Cannot train with sentences shorter than 2 tokens.")
        train_data = SpmIdsDataset(train_dataset_path, min_length=min_length)
        sampler = SpmIdsBatchSampler(train_data, batch_size=batch_size)
        pin_memory = self.device != torch.device("cpu")
        data_loader = DataLoader(
            train_data,
            batch_sampler=sampler,
            pin_memory=pin_memory,
            num_workers=n_data_loader_threads,
            collate_fn=self.collate_batch_with_labels,
        )
        if validation_dataset_path is None:
            validation_data = None
        else:
            validation_data = SpmIdsDataset(
                validation_dataset_path, min_length=min_length
            )
            validation_sampler = SpmIdsBatchSampler(
                validation_data, batch_size=batch_size, randomize=False
            )
            validation_data_loader = DataLoader(
                validation_data,
                batch_sampler=validation_sampler,
                pin_memory=pin_memory,
                num_workers=n_data_loader_threads,
                collate_fn=self.collate_batch_with_labels,
            )

        optimizer = torch.optim.SGD(self.model.parameters(), lr=lr)
        loss_function = make_loss_function()
        n_data_points = 0
        i_epoch = 0
        while i_epoch < n_epochs:  # 'for i_epoch in range(np.inf)' would fail
            i_epoch += 1
            print("Starting training epoch {}.".format(i_epoch))
            total_training_loss = 0.0
            for i_batch, (batch, labels) in enumerate(data_loader, start=1):
                batch = batch.to(self.device, non_blocking=True)
                labels = labels.to(self.device, non_blocking=True)
                self.model.zero_grad()
                prediction = self.model(batch)
                loss = loss_function(prediction, labels)
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), 1)
                optimizer.step()

                # If a reduction other than 'mean' is used in the loss fucntion,
                # it would be necessary to thange the following accounting.
                n_points_in_batch = labels.size(0)
                total_training_loss += loss.item() * n_points_in_batch
                n_data_points += n_points_in_batch

                if i_batch % n_batches_between_messages == 0:
                    print(
                        "Mean training loss at batch {} is {}.".format(
                            i_batch, total_training_loss / n_data_points
                        )
                    )

                if i_batch % n_batches_between_saves == 0:
                    print("Saving model to {}.".format(save_path))
                    self.save(save_path)

                if (
                    i_batch % n_batches_between_validations == 0
                ) and validation_data is not None:
                    print("Computing validation loss.")
                    with torch.autograd.no_grad():
                        n_validation_points = 0
                        validation_loss = 0.0
                        self.model.eval()
                        for i_vdtn_batch, (batch, labels) in enumerate(
                            validation_data_loader, start=1
                        ):
                            batch = batch.to(self.device, non_blocking=True)
                            labels = labels.to(self.device, non_blocking=True)
                            prediction = self.model(batch)
                            loss = loss_function(prediction, labels)
                            # Again we assume the loss has a 'mean' reduction.
                            n_points_in_batch = labels.size(0)
                            validation_loss += loss.item() * n_points_in_batch
                            n_validation_points += n_points_in_batch
                            if i_vdtn_batch % n_batches_between_messages == 0:
                                print(
                                    "At {} labels running loss is {}.".format(
                                        n_validation_points,
                                        validation_loss / n_validation_points,
                                    )
                                )
                        validation_loss /= n_validation_points  # overall mean
                        self.model.train()
                        print("Mean validation loss is {}.".format(validation_loss))

            if save_path is not None:
                print("Saving model to {}.".format(save_path))
                self.save(save_path)

        print("Finished {} training epochs.".format(n_epochs))
        if save_path is not None:
            print("Saving model to {}.".format(save_path))
            self.save(save_path)

    def test(
        self,
        test_dataset_path,
        batch_size=256,
        n_data_loader_threads=0,
        device=torch.device("cuda:0"),
        min_length=2,
    ):
        """
        Simple test method that just computes the perplexity on
        a test dataset.  Assumes that the model outputs are log prababilities.
        """
        self.device = device
        self.model.eval()
        test_data = SpmIdsDataset(test_dataset_path, min_length=min_length)
        sampler = SpmIdsBatchSampler(test_data, batch_size=batch_size)
        pin_memory = self.device != torch.device("cpu")
        data_loader = DataLoader(
            test_data,
            batch_sampler=sampler,
            pin_memory=pin_memory,
            num_workers=n_data_loader_threads,
            collate_fn=self.collate_batch_with_labels,
        )
        n_labels = 0
        log_prob_sum = 0.0
        with torch.autograd.no_grad():
            for batch, labels in data_loader:
                batch = batch.to(self.device, non_blocking=True)
                labels = labels.to(self.device, non_blocking=True)
                log_probs = self.model(batch)
                # Find the 1D (row-major) indices (as required by torch.take)
                # in the 2D log probability tensor corresponding to the labels.
                indices = (
                    log_probs.size(1)
                    * torch.arange(log_probs.size(0), device=self.device)
                    + labels
                )
                log_prob_sum += log_probs.take(indices).sum().item()
                n_labels += labels.size(0)
                perplexity = pow(0.5, log_prob_sum / n_labels)
                print(
                    "Processed {} labels; running perplexity is {}.".format(
                        n_labels, perplexity
                    )
                )
        perplexity = pow(0.5, log_prob_sum / n_labels)
        print("Perplexity on {} is {}.".format(test_dataset_path, perplexity))
        return perplexity

    def save(self, path):
        # Move to CPU then save (to match loading).
        device = self.device
        self.device = torch.device("cpu")
        mgr_kwargs = dict(
            device=device,
            n_tokens=self.model.encoder.num_embeddings,
            n_dims=self.model.encoder.embedding_dim,
            sparse=self.model.encoder.sparse,
            hidden_size=self.model.rnn.hidden_size,
            num_layers=self.model.rnn.num_layers,
            bias=self.model.rnn.bias,
            dropout=self.model.rnn.dropout,
            bidirectional=self.model.rnn.bidirectional,
        )
        model_state = self.model.state_dict()
        torch.save([mgr_kwargs, model_state], str(path))
        self.device = device  # put the model back on the right device

    @classmethod
    def load(cls, path):
        # In the past we've seen issues with excessive GPU memory consumption
        # when loading models direct to GPU, so we load to CPU first then move.
        mgr_kwargs, model_state = torch.load(str(path))
        device = mgr_kwargs.get("device", torch.device("cpu"))
        mgr_kwargs.update(device=torch.device("cpu"))  # load to cpu
        result = cls(**mgr_kwargs)
        result.model.load_state_dict(model_state)
        result.device = device  # move to saved device if any
        return result


def main(model_path=None, model_kwargs=None, task="train", task_kwargs=None):
    if model_path is not None:
        model_path = Path(model_path)
    model_kwargs = model_kwargs or {}
    task_kwargs = task_kwargs or {}
    if model_path is not None and model_path.exists():
        print("Loading model from {}.".format(model_path))
        model_mgr = ModelManager.load(model_path)
    elif model_kwargs is not None:
        print("Making a new model from kwargs {}.".format(model_kwargs))
        model_mgr = ModelManager(**model_kwargs)
    else:
        print("Error; must specify an existing model or give kwargs to make a new one.")
    if task == "train":
        print("Training model with kwargs {}.".format(task_kwargs))
        model_mgr.train(**task_kwargs)
    elif task == "test":
        print("Testing model with kwargs {}.".format(task_kwargs))
        model_mgr.test(**task_kwargs)
    else:
        print("Unknown task {}.".format(task))


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
train a new model with a vocabulary of 8000 SentencePiece tokens
training sentences shorter than 5 tokens will be discarded.
Every 5 epochs a checkpoint of the model will be saved at the given
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
        "n_epochs_between_saves": 5,
        "min_length": 5,
        "batch_size": 256,
        "n_data_loader_threads": 10
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
        "n_data_loader_threads": 10,
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
    main(**config)


if __name__ == "__main__":
    spm_naive_language_model()
