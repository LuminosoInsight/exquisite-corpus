import click
import itertools
import numpy as np
import sys
import torch
import torch.nn as nn
import tqdm

from exquisite_corpus.spm_ids_translator import SpmIdsTranslator
from exquisite_corpus.spm_language_model_utils import (
    SpmIdsBatchMakerForLanguageModels as BatchMaker,
    SpmIdsLossFunctionForLanguageModels,
)
from pathlib import Path


class SpmIdsLanguageModel(nn.Module):
    """
    Since this is just to illustrate how one might set up a language model
    using SentencePiece ids, we use a very simple model rather than a good one.

    Namely, this model consists of an embedding to encode SentencePiece ids as
    vectors which are fed to an RNN whose outputs are decoded by a linear
    layer back to SentencePiece ids, followed by a log softmax to produce
    log probabilities of each id as output.
    """

    def __init__(
        self, n_tokens=8000, n_dims=300, hidden_size=300, num_layers=5, dropout=0.5
    ):
        """
        Construct a model containing a vector embedding of SentencePiece
        tokens, a recursive neural network, a linear decoding layer, and a
        log softmax layer.

        Arguments:
            n_tokens:
                The number of SentencePiece tokens in the vocabulary of the
                model.  Default is 8000.
            n_dims:
                The number of features (dimensions) to use in the vector
                embedding used to encode the SentencePiece tokens.  Defaults
                to 300.
            hidden_size:
                The size of the hidden state of the RNN.  Defaults to 300.
            num_layers:
                The number of layers in the RNN.  Defaults to 5.
            dropout:
                The dropout factor applied between the layers of the RNN.
                Defaults to 0.5.
       """
        super().__init__()
        self.encoder = nn.Embedding(n_tokens, n_dims)
        self.rnn = nn.GRU(
            input_size=n_dims,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )  # torch requires dropout = 0 if num_layers < 2
        self.decoder = nn.Linear(in_features=hidden_size, out_features=n_tokens)
        self.log_softmax = nn.LogSoftmax(dim=2)

    def forward(self, input):
        """
        Application of the model delegates to this method, which defines how
        predictions are computed from the inputs.  Runs the inputs through
        the encoder, RNN, decoder, and softmax layers in sequence.  An output
        prediction is produced for every sequence position following the first
        for each item in the input batch.

        The hidden states are initialized to zeros (at the start of each
        batch of input; they are carried over within the computation of the
        output for the batch, of course).

        Arguments:
            input:
                A batch of input sequences, i.e. a 2D tensor of SentencePiece
                ids, each row of which is a sequence of ids.

        Returns a 3D FloatTensor (of log probabilities) whose first index refers
        to positions within a batch, whose second refers to positions within the
        sequences comprising the batch, and whose third refers to predicted
        SentencePiece ids.
        """
        batch_size = input.size(0)  # because we use batch_first=True
        hidden_states = torch.zeros(
            self.rnn.num_layers, batch_size, self.rnn.hidden_size
        ).to(input.device, non_blocking=True)
        output = input.to(torch.int64)  # encoder needs LongTensor input
        output = self.encoder(output)
        output, hidden_states = self.rnn(output, hidden_states)
        output = self.decoder(output)
        output = self.log_softmax(output)
        return output


class ModelManager:
    """
    Objects that own SpmIdsLanguageModels and provide convenience methods
    for their training and use.
    """

    def __init__(self, model=None, device=torch.device("cuda:0"), **kwargs):
        """
        Model managers are constructed from an SpmIdsLanguageModel and a
        torch.device.

        Arguments:
            model:
                An SpmIdsLanguageModel.  If none is given, one will be
                constructed with default parameters.
            device:
                A torch.device (defaults to torch.device("cuda:0"), which
                is normally the fastest available GPU).  The model will be
                moved to this device.  (The device attribute of the model
                manager may be changed later to move the model to a different
                device.)  May also be given as a string, which will be
                converted to a torch.device (e.g. "cpu" may be given instead
                of torch.device("cpu")).
        """
        self.model = model
        self.device = device

    @property
    def device(self):
        """
        Return the currently selected device, on which the model and its
        parameters are placed.
        """
        return self._device

    @device.setter
    def device(self, new_device):
        """
        Set the currently selected device.  If the device chages, move the
        model and its parameters to the new device.
        """
        if isinstance(new_device, str):
            new_device = torch.device(new_device)
        if new_device != torch.device("cpu") and not torch.cuda.is_available():
            print("Warning:  cuda not available so setting device to CPU.")
            self._device = torch.device("cpu")
        else:
            self._device = new_device
        self.model.to(self._device)

    def train(
        self,
        train_dataset_path,
        validation_dataset_path=None,
        save_path=None,
        min_length=2,
        n_epochs=np.inf,
        n_batches_between_saves=1000,
        n_batches_between_validations=25000,
        batch_size=256,
        n_data_loader_workers=10,
        lr=0.05,
    ):
        """
        Train the model.  No value is returned, but the model's parameters
        will be updated by the training.  Checkpoints of the model's state
        can be saved periodically during the training process.

        Arguments:
            train_dataset_path:
                The location of the training data (a directory of .npy files
                containing SentencePiece ids).  This parameter is required.
            validation_dataset_path:
                The location of data used to periodically compute and report
                validation loss (another directory of .npy files).  If not
                supplied validation loss computation will be skipped.
            save_path:
                A location on disk at which checkpoints will be saved
                periodically during training.  These checkpoints can be used
                later to reconstruct a ModelManager containing the model with
                its state (i.e. parameter values) as of the point during
                training at which the checkpoint was created.  If not supplied
                no checkpoints will be saved.
            min_length:
                Sequences (sentences) of SentencePiece id tokens in the training
                (and validation) datasets shorter than this number of tokens
                will be ignored.  Must be at least 2 (the default value), as
                a sequence of length 2 produces one prediction and one ground-
                truth label.
            n_epochs:
                The number of training epochs.  The model will be trained on the
                entire training dataset (in randomized order) once per epoch.
                If not specified, training will continue until interrupted
                (e.g. by SIGKILL).
            n_batches_between_saves:
                Interval (number of training data batches) between successive
                checkpoint saves.  (Ignored if save_path is not supplied.)
                Defaults to 1000.
            n_batches_between_validations:
                Interval (number of training data batches) between successive
                calculations of validation data loss.  Defaults to 25000.
            batch_size:
                The number of sequences (sentences/items from the training and
                validation datasets) in each batch sent to the model.  Defaults
                to 256.
            n_data_loader_workers:
                The number of child worker processes created for batch
                generation.  A value of zero means batches will be created
                in the main training process.  Higher values are likely to
                provide better CPU and GPU utilization during training; the
                default is 10.
            lr:
                The learning rate, which will be passed to a torch optimizer
                used to update the model parameters during training.  Defaults
                to 0.05.
        """
        self.model.train()

        train_batch_maker = BatchMaker(
            train_dataset_path,
            min_length=min_length,
            batch_size=batch_size,
            target_device=self.device,
            n_data_loader_workers=n_data_loader_workers,
        )
        if validation_dataset_path is None:
            validation_batch_maker = None
        else:
            validation_batch_maker = BatchMaker(
                validation_dataset_path,
                min_length=min_length,
                batch_size=batch_size,
                randomize=False,
                target_device=self.device,
                n_data_loader_workers=n_data_loader_workers,
            )

        optimizer = torch.optim.SGD(self.model.parameters(), lr=lr)
        loss_function = SpmIdsLossFunctionForLanguageModels()

        # tqdm progress bars can handle total lengths up to about 1e18.
        with tqdm.tqdm(
            desc="Epochs", total=(n_epochs if n_epochs < 1e18 else None)
        ) as epoch_progress_bar:
            validation_loss = "N/A"
            running_mean_training_loss = "N/A"
            epoch_mean_training_loss = "N/A"
            epoch_progress_bar.set_postfix(
                dict(epoch=1, last_epoch_loss="N/A", last_epoch_validation_loss="N/A")
            )
            epoch_progress_bar.update()
            epoch_iterator = (
                range(1, n_epochs + 1)
                if n_epochs < np.inf
                else itertools.count(start=1)
            )
            for i_epoch in epoch_iterator:
                n_data_points = 0
                total_training_loss = 0.0

                with tqdm.tqdm(
                    desc="Training batches", total=len(train_batch_maker), leave=False
                ) as batch_progress_bar:
                    for i_batch, (batch, labels) in enumerate(
                        train_batch_maker, start=1
                    ):
                        # Train on one batch.
                        self.model.zero_grad()
                        prediction = self.model(batch)
                        loss = loss_function(prediction, labels)
                        loss.backward()
                        nn.utils.clip_grad_norm_(self.model.parameters(), 1)
                        optimizer.step()

                        # Update the running training loss.  If a reduction
                        # other than "mean" is used in the loss function, it
                        # will be necessary to adjust the following accounting.
                        n_labels = labels.numel()
                        total_training_loss += loss.item() * n_labels
                        n_data_points += n_labels

                        # Periodically make a checkpoint of the trained model.
                        if i_batch % n_batches_between_saves == 0:
                            self.save(save_path)

                        # Periodically update validation loss.
                        if (
                            i_batch % n_batches_between_validations == 0
                        ) and validation_batch_maker is not None:
                            with torch.autograd.no_grad(), tqdm.tqdm(
                                total=len(validation_batch_maker),
                                desc="Validation batches",
                                leave=False,
                            ) as vdtn_progress_bar:
                                n_validation_points = 0
                                validation_loss = 0.0
                                self.model.eval()
                                for i_vdtn_batch, (batch, labels) in enumerate(
                                    validation_batch_maker, start=1
                                ):
                                    prediction = self.model(batch)
                                    loss = loss_function(prediction, labels)
                                    # Again we assume the loss has a 'mean' reduction.
                                    n_labels = labels.numel()
                                    validation_loss += loss.item() * n_labels
                                    n_validation_points += n_labels
                                    vdtn_progress_bar.set_postfix(
                                        dict(
                                            running_validation_loss=(
                                                validation_loss / n_validation_points
                                            )
                                        )
                                    )
                                    vdtn_progress_bar.update()
                                validation_loss /= n_validation_points  # overall mean
                                self.model.train()

                        # Finalize the batch.
                        running_mean_training_loss = total_training_loss / n_data_points
                        batch_progress_bar.set_postfix(
                            dict(
                                loss=running_mean_training_loss,
                                validation_loss=validation_loss,
                            )
                        )
                        batch_progress_bar.update()

                # Finalize the epoch.
                if save_path is not None:
                    self.save(save_path)
                epoch_mean_training_loss = total_training_loss / n_data_points
                epoch_progress_bar.set_postfix(
                    dict(
                        epochs=i_epoch,
                        last_epoch_loss=epoch_mean_training_loss,
                        last_epoch_validation_loss=validation_loss,
                    )
                )
                epoch_progress_bar.update()

        print("Finished {} training epochs.".format(n_epochs))
        print("Final full epoch training loss {:.5g}.".format(epoch_mean_training_loss))
        print("Final validation loss {:.5g}.".format(validation_loss))

    def test(
        self, test_dataset_path, batch_size=256, n_data_loader_workers=10, min_length=2
    ):
        """
        Simple test method that just computes the model's perplexity on
        a test dataset.  Assumes that the model outputs are log prababilities.
        Prints running values for the perplexity during the computation, and
        the final perplexity over the entire dataset, which is also returned.

        Arguments:
            test_dataset_path:
                The location of the data used to compute test statistics
                (required; a directory of .npy files containing SentencePiece
                ids).
            batch_size:
                The number of sequences (sentences/items from the training and
                validation datasets) in each batch sent to the model.  Defaults
                to 256.
            n_data_loader_workers:
                The number of child worker processes created for batch
                generation.  A value of zero means batches will be created
                in the main training process.  Higher values are likely to
                provide better CPU and GPU utilization during training; the
                default is 10.
            min_length:
                Sequences (sentences) of SentencePiece id tokens in the test
                dataset shorter than this number of tokens
                will be ignored.  Must be at least 2 (the default value), as
                a sequence of length 2 produces one prediction and one ground-
                truth label.
       """
        self.model.eval()
        batch_maker = BatchMaker(
            test_dataset_path,
            min_length=min_length,
            batch_size=batch_size,
            randomize=False,
            target_device=self.device,
            n_data_loader_workers=n_data_loader_workers,
        )
        n_labels = torch.tensor(0, dtype=torch.int64, device=self.device)
        minus_log_prob_sum = torch.tensor(0.0, dtype=torch.float32, device=self.device)
        nll_loss = SpmIdsLossFunctionForLanguageModels(reduction="sum")
        with torch.autograd.no_grad(), tqdm.tqdm(
            total=len(batch_maker)
        ) as progress_bar:
            for batch, labels in batch_maker:
                log_probs = self.model(batch)
                minus_log_prob_sum += nll_loss(log_probs, labels)
                n_labels += labels.numel()
                perplexity = (minus_log_prob_sum / n_labels).exp().item()
                progress_bar.set_postfix(dict(perplexity=perplexity))
                progress_bar.update()
        perplexity = (minus_log_prob_sum / n_labels).exp().item()
        print("Perplexity on {} is {:.5g}.".format(test_dataset_path, perplexity))
        return perplexity

    def save(self, path):
        """
        Save the state of the model (but not the device) to a pickle file
        at the given location.

        Arguments:
            path:
                The location at which to save the model (required).
        """
        model_kwargs = dict(
            n_tokens=self.model.encoder.num_embeddings,
            n_dims=self.model.encoder.embedding_dim,
            hidden_size=self.model.rnn.hidden_size,
            num_layers=self.model.rnn.num_layers,
            dropout=self.model.rnn.dropout,
        )
        model_state_dict = self.model.state_dict()

        # Save the kwargs and state_dict to the given location.
        # Because the save can fail (e.g. if the user kills us during
        # the save), first back up any existing saved checkpoint, and
        # if the save fails for any reason restore from the backup.

        path = Path(path)
        bak = path.with_name(path.name + ".bak")
        if path.exists():
            path.rename(bak)
        try:
            torch.save([model_kwargs, model_state_dict], str(path))
        except:  # noqa: E722
            path.unlink()
            if bak.exists():
                bak.rename(path)
            raise  # atone for the sin of a nekkid except by re-raising
        else:
            if bak.exists():
                bak.unlink()

    @classmethod
    def load(cls, path, device=torch.device("cuda:0")):
        """
        Create a model manager from model state previously saved to a file
        at the given location.  The model will be placed on the specified
        device.

        Arguments:
            path:
                The location from which to restore the model (required).
            device:
                The torch.device on which to place the restored model.
                (Defaults to cuda:0).

        Returns a model manager owning the restored model.
        """
        # In the past we've seen issues with excessive GPU memory consumption
        # when loading models direct to GPU, so we load to CPU first then move.
        model_kwargs, model_state_dict = torch.load(str(path), map_location="cpu")
        model = SpmIdsLanguageModel(**model_kwargs)
        model.load_state_dict(model_state_dict)
        result = cls(model=model, device=device)
        return result


@click.command(help="Command-line tool to train or test SentencePiece language Models.")
@click.option(
    "--train",
    "task",
    flag_value="train",
    default=True,
    help="Train a new or existing model.  This is the default behavior.",
)
@click.option(
    "--test",
    "task",
    flag_value="test",
    help="Evaluate an existing model on test data.  (Mutually exclusive with --train.)",
)
@click.option(
    "--data-root",
    "-d",
    type=click.Path(exists=True, file_okay=False, path_type=str),
    help=(
        "Directory in which inputs will be looked for and outputs stored. "
        "If not specified, the current working directory and its parent will "
        "be searched for a directory named 'data' containing a subdirectory "
        "named 'sentencepiece'."
    ),
)
@click.option(
    "--device",
    default="cuda:0",
    help=(
        "The device (specified as a string, e.g. 'cpu', 'cuda:0', "
        "'cuda:1') on which to place the model for training or testing.  "
        "Defaults to 'cuda:0'."
    ),
)
def spm_naive_language_model(task="train", data_root=None, device="cuda:0"):
    # If no data root directory was specified, look for data/sentencpiece in
    # the current working directory and its parent.  That covers the obvious
    # places from which this tool is likely to be run.

    if data_root is None:
        cwd = Path.cwd()
        data_root = cwd / "data/sentencepiece"
        if not data_root.exists():
            data_root = (cwd / "..").resolve() / "data/sentencepiece"
            if not data_root.exists():
                print(
                    "Could not find data/sentencepiece in the current "
                    "working directory or its parent.  Either run this "
                    "tool from the directory containing data/sentencepiece "
                    "or use the --data-root option to specify the path to "
                    "data/sentencepiece."
                )
                sys.exit(-1)
    else:
        data_root = Path(data_root)

    # Look for the input data sets.

    spm_model_path = data_root / "en.model"
    if not spm_model_path.exists():
        print(
            "Could not find a SentencePiece model at {}.  Please put a trained "
            "model there.".format(spm_model_path)
        )
        sys.exit(-1)

    if task == "train":
        train_dataset_path = data_root / "en.spm_ids_training"
        if not train_dataset_path.exists():
            print(
                "Could not find training data at {}. Please put a training "
                "dataset there.".format(train_dataset_path)
            )
            sys.exit(-1)

        validation_dataset_path = data_root / "en.spm_ids_validation"
        if not validation_dataset_path.exists():
            validation_dataset_path = None  # skip validation
            print("Could not find validation data; skipping validation.")
    else:
        test_dataset_path = data_root / "en.spm_ids_testing"
        if not test_dataset_path.exists():
            print(
                "Could not find test data at {}.  Please put a test dataset "
                "there.".format(test_dataset_path)
            )
            sys.exit(-1)

    # If we can find a model at the conventional path, use it; otherwise create
    # a new one.

    save_path = data_root / "en.spm_lang_model.pt"
    if save_path.exists():
        print("Loading model from {}.".format(save_path))
        model_mgr = ModelManager.load(save_path, device=device)
    else:
        print("Making a new model.")
        translator = SpmIdsTranslator(spm_model_path)
        model = SpmIdsLanguageModel(n_tokens=translator.number_of_ids())
        model_mgr = ModelManager(model=model, device=device)

    # Do training or testing as requested.

    if task == "train":
        print("Training model.")
        model_mgr.train(
            train_dataset_path=train_dataset_path,
            validation_dataset_path=validation_dataset_path,
            save_path=save_path,
        )
    else:  # task == "test"
        print("Testing model.")
        model_mgr.test(test_dataset_path=test_dataset_path)


if __name__ == "__main__":
    spm_naive_language_model()
