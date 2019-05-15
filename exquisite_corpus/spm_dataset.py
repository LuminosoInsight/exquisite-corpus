import numpy as np
import torch

from pathlib import Path
from torch.utils.data import BatchSampler, DataLoader, Dataset, Sampler


class SpmIdsBatchMaker:
    """
    Wraps an SpmIdsDataset, SpmIdsBatchSampler, and a DataLoader, and uses
    them to produce batches of data on a specified device.  This base class
    returns batches (of the requested size, and of uniform sequence length)
    of items from the underlying dataset as 2D tensors (where each row is
    a single item from the dataset, that is, a sequence of SentencePiece ids).
    The exact format of the returned batches may be tweaked by deriving
    subclasses of this class which override the collate_batch and place_batch
    methods.  (For example in spm_language_model_utils we define a subclass
    for use in training language models which overrides these methods to
    produces batches along with labels/targets for training a language
    model.)

    Typical usage for this class:

        batch_maker = SpmIdsBatchMaker(
                        <path-to-dataset>,
                        min_length=2,
                        batch_size=256,
                        n_data_loader_workers=10
                      )
        for batch in batch_maker.run():
            <do-something-with-the-batch-here>
    """

    def __init__(
        self,
        npy_directory,
        min_length=1,
        max_length=np.inf,
        datatype=np.int16,
        mmap=False,
        batch_size=1,
        drop_last=False,
        randomize=True,
        random_state=101,
        n_data_loader_workers=0,
        target_device=torch.device("cuda:0"),
    ):
        """
        Constructs a batch maker containing an SpmIdsDataset,
        SpmIdsBatchSampler, and a DataLoader, which will generate batches of
        data from a directory of .npy files of SentencePiece ids.

        Arguments:
            npy_directory:
                A path (pathlib.Path or string) at which the directory of .npy
                files is located.  Required.
            min_length:
                Any .npy file in the directory whose array contains fewer than
                min_length columns (and so represents sequences of fewer than
                min_length tokens) will be excluded from the data exposed by
                this dataset.  Defaults to 1.
            max_length:
                Any .npy file whose array contains more than max_length columns
                will also be excluded.  Defaults to np.inf, meaning no data
                will be excluded.
            datatype:
                A numpy datatype to which the tokens (SentencePiece ids) will
                be converted when they are returned.  That is, items of this
                dataset will be 1D numpy arrays of this datatype.  So this type
                should be chosen large enough to represent all the tokens
                present in the .npy files.  Defaults to np.int16, which will
                reasonable sized SentencePiece vocabularies.
            mmap:
                A Boolean flag.  If True, the .npy files will be loaded (by
                numpy.load) memory-mapped, which can save time and space if
                not all of the data will be accessed.  Defaults to False (since
                for the common use-case of training a model all of the data is
                likely to be accessed).
            batch_size:
                The number of items to return in each batch.  Defaults to 1.
            drop_last:
                A Boolean flag.  Depending on the batch size and the number of
                items of each sequence length in the dataset, for some sequence
                lengths after generating as many batches of the requested size
                as possible some data may be left over.  If drop_last is True,
                this data will not be returned by the sampler (so all batches
                will have exactly the requested size).  If it is False, then
                the left-over data will be returned by the sampler in batches
                smaller than the requested size.  Default is False.
            randomize:
                A Boolean flag.  If True, iterating over this object will
                yield batches in a (pseudo-)random order of sequence lengths,
                and with the sequences of each length in (pseudo-)random order.
                Iterating multiple times over the entire dataset (by repeatedly
                exhausting this iteration) will yield different orderings of the
                data.  If False, the batches will be produced in the order of
                the underlying dataset.  Defaults to True.
            random_state:
                Either a numpy.random.RandomState or an integer (which will be
                used to seed a RandomState).  Used to initialize the pseudo-
                random generator used if randomize is True.  Optional (defaults
                to a reasonable fixed value for seeding, so even with
                randomize=True the order in which batches are returned is
                deterministic).
            n_data_loader_workers:
                The number of child processes launched to generate the batches.
                The default is zero, which means all batches are generated in
                the same (parent) process.  This is good for debugging, but
                to effectively utilize a GPU when multiple CPU cores are
                available, it is advisable to use a number close to the number
                of CPU cores (say, 10 on Luminoso research PC's).
            target_device:
                The torch.device on which to put the data batches.  For use in
                training or evaluating a model on a single device (or which
                otherwise expects data on a specific device), set this parameter
                to that device.  Defaults to torch.device("cuda:0"), which is
                normally the fastest available GPU.
       """
        self.dataset = SpmIdsDataset(
            npy_directory, min_length, max_length, datatype, mmap
        )
        self.batch_sampler = SpmIdsBatchSampler(
            self.dataset, batch_size, drop_last, randomize, random_state
        )
        self.target_device = target_device
        pin_memory = self.target_device != torch.device("cpu")
        self.dataloader = DataLoader(
            self.dataset,
            batch_sampler=self.batch_sampler,
            num_workers=n_data_loader_workers,
            pin_memory=pin_memory,
            collate_fn=self.collate_batch,
        )

    def __len__(self):
        """
        Returns the number of batches that will be generated.

        Arguments:  none.
        """
        return len(self.batch_sampler)

    def __iter__(self):
        """
        An iterator that yields the collated batches of data from the dataset.
        Batches will be placed on the target device (by calling the place_batch
        method; the type of the returned batches is determined by that method
        which in turn gets the batches from the collate_batch method).

        Note that this iterator will be exhausted after a single complete pass
        through the entire underlying dataset (i.e. one epoch); however it is
        possible to iterate through the dataset multiple times, and if
        randomize=True was set in the constructor then each run will yield
        the data items in a different order, even without reseeding the
        underlying batch sampler.
        """
        for batch in self.dataloader:
            yield self.place_batch(batch)

    def place_batch(self, batch):
        """
        Move a collated batch as returned by the collate_batch method on the
        CPU to the target device.  The base class implementation handles
        batches which are tensors.  You may override the collate_batch method
        to return batches of another type, but if you do you must
        correspondingly override this method to accept that type.

        Arguments:
            batch:
                A collated batch as returned by collate_batch.

        Returns the batch moved to the target device.
        """
        # It would be nice to be able to do this in collate_batch, and avoid
        # having a separate place_batch method.  But collate_batch runs in
        # the dataloader child processes, which don't have the cuda context,
        # so they can't move data onto a GPU.
        return batch.to(self.target_device)

    def collate_batch(self, raw_batch):
        """
        The collation function used by the dataloader.  It must accept a raw
        batch in the form of a list of 1D numpy arrays (all of the same length),
        and (unless place_batch is overriden) produce a tensor.  (Each array in
        the input list is one item from the underlying dataset, that is to say
        one sequence of SentencePiece ids.)  The base class implementation
        returns the tensor obtained by vertically stacking the raw input arrays.

        Arguments:
            raw_batch:
                A list of 1D numpy arrays, all of the same length (that is,
                a list of sequences from the underlying dataset).

        Returns a single tensor containing all the items of the batch.
        """
        return torch.tensor(np.vstack(raw_batch))


class SpmIdsDataset(Dataset):
    """
    A subclass of Pytorch's Dataset class that exposes a the output of
    split_sentencepiece_ids and sentencepiece_id_converter.  (Principally,
    this means a directory full of .npy files containing matrices whose rows
    are the sequences of SentencePiece id's corresponding to a set of input
    sentences; we assume each such .npy file corresponds to a distinct length
    of input sentences.)  Only sentences with sequence length greater than
    zero are taken to be data items.

    SpmIdsDatasets load data from disk lazily, only bringing one of their
    .npy files into memory on demand (and evicting any previously-loaded
    file).

    Note:  It is possible to use standard BatchSamplers and RandomSamplers
    with an SpmIdsDataset, however, the resulting batches may not have the
    property that all sentences in a batch have the same sequence length.
    To get uniform sequence lengths in each batch, use an SpmIdsBatchSampler.
    In particular, if you want to use an SpmIdsDataset with a DataLoader and
    get uniform sequence length batches, construct the DataLoader with the
    batch_sampler argument equal to an instance of SpmIdsBatchSampler.
    """

    def __init__(
        self,
        npy_directory,
        min_length=1,
        max_length=np.inf,
        datatype=np.int16,
        mmap=False,
    ):
        """
        Construct a dataset from a directory of .npy files representing
        sequences of SentencePiece tokens (ids).  Each .npy file should contain
        a 2D array whose entries are SentencePiece ids.

        Arguments:
            npy_directory:
                A path (pathlib.Path or string) at which the directory of .npy
                files is located.  Required.
            min_length:
                Any .npy file in the directory whose array contains fewer than
                min_length columns (and so represents sequences of fewer than
                min_length tokens) will be excluded from the data exposed by
                this dataset.  Defaults to 1.
            max_length:
                Any .npy file whose array contains more than max_length columns
                will also be excluded.  Defaults to np.inf, meaning no data
                will be excluded.
            datatype:
                A numpy datatype to which the tokens (SentencePiece ids) will
                be converted when they are returned.  That is, items of this
                dataset will be 1D numpy arrays of this datatype.  So this type
                should be chosen large enough to represent all the tokens
                present in the .npy files.  Defaults to np.int16, which will
                reasonable sized SentencePiece vocabularies.
            mmap:
                A Boolean flag.  If True, the .npy files will be loaded (by
                numpy.load) memory-mapped, which can save time and space if
                not all of the data will be accessed.  Defaults to False (since
                for the common use-case of training a model all of the data is
                likely to be accessed).
        """
        self.datatype = datatype
        self.mmap_mode = "r" if mmap else None
        npy_root_path = Path(npy_directory)
        self.npy_paths = {}  # map item lengths to corresponding npy files
        self.item_counts = {}  # map item lengths to number of corresponding items

        # We need to compute the maximum length for which there really are any
        # items.  We initialize it to a value less than any valid length, so
        # that the first (if any) item encountered will have greater length.
        self.max_item_length = -1

        self.total_item_count = 0
        for npy_path in npy_root_path.glob("*.npy"):
            # Load the file to get the shape; best to just mmap as
            # we don't need any of the entries.
            item_count, item_length = np.load(npy_path, mmap_mode="r").shape
            if item_length < min_length or item_length > max_length:
                continue
            self.npy_paths[item_length] = npy_path
            self.item_counts[item_length] = item_count
            self.total_item_count += item_count
            if item_length > self.max_item_length and item_count > 0:
                self.max_item_length = item_length
        self.available_item_lengths = sorted(
            item_length
            for item_length, item_count in self.item_counts.items()
            if item_count > 0
        )

        # Present the data to the world (e.g. via __getitem__) as if it were
        # stored as a list in increasing order of item length.
        self.item_index_to_length = np.empty((self.total_item_count,), dtype=np.int16)
        self.item_index_to_position = np.empty((self.total_item_count,), dtype=np.int64)
        cumulative_count = 0
        for item_length in self.available_item_lengths:
            item_count = self.item_counts[item_length]
            next_count = cumulative_count + item_count
            self.item_index_to_length[cumulative_count:next_count] = item_length
            self.item_index_to_position[cumulative_count:next_count] = np.arange(
                item_count
            )
            cumulative_count = next_count

        # Initialize the current item length and load data (of that length).
        # Set _items by hand rather than letting the current_item_length
        # setter do it, since the setter would try to access _items (via
        # the getter).
        if self.total_item_count < 1:
            self._items = np.empty((0, 0), dtype=self.datatype)
        else:
            item_length = self.available_item_lengths[0]
            self._items = np.load(
                self.npy_paths[item_length], mmap_mode=self.mmap_mode
            ).astype(self.datatype)
            self.current_item_length = item_length

    def __len__(self):
        """
        The length of an SpmIdsDataset is the total number of encoded sequences
        in its .npy files (subject to its minimum and maximum length
        restrictions.
        """
        return self.total_item_count

    def __getitem__(self, i_item):
        """
        Returns the item (a 1D numpy array of SentencePiece ids) at the
        requested position.  The items are ordered by increasing sequence
        length.
        """
        item_length = self.item_index_to_length[i_item]
        position = self.item_index_to_position[i_item]
        self.current_item_length = item_length
        return self._items[position]

    @property
    def current_item_length(self):
        """
        The (current) length of individual items returned by the dataset.
        """
        return self._items.shape[1]

    @current_item_length.setter
    def current_item_length(self, new_len):
        if new_len not in self.available_item_lengths:
            raise ValueError("Invalid requested length {}.".format(new_len))
        if new_len == self.current_item_length:
            return
        self._items = np.load(self.npy_paths[new_len], mmap_mode=self.mmap_mode).astype(
            self.datatype, copy=False
        )


class SpmIdsBatchSampler(BatchSampler):
    """
    An SpmIdsBatchSampler does for an SpmIdsDataset what BatchSamplers do for
    other datasets, namely provides an iterator yielding (mini-)batches of
    indices.  But the batches returned by an SpmIdsBatchSampler will not cross
    length boundaries; in other words every batch will consist of sequences of
    the same length.  Because RandomSamplers would not respect this length
    uniformity requirement, SpmIdsBatchSamplers also include facilities for
    randomizing the batches they return.  The order of the sequence lengths of
    the batches may be randomized, as well as the order of the sequences of
    each length.  However, sequence lengths will not be interleaved; all
    batches consisting of sequences of one length will be returned before any
    batches consisting of sequences of any other length.
    """

    def __init__(
        self, dataset, batch_size=1, drop_last=False, randomize=True, random_state=101
    ):
        """
        Construct an SpmIdsBatchSampler from an SpmIdsDataset.

        Arguments:
            dataset:
                The underlying SpmIdsDataset.  Required.
            batch_size:
                The number of items to return in each batch.  Defaults to 1.
            drop_last:
                A Boolean flag.  Depending on the batch size and the number of
                items of each sequence length in the dataset, for some sequence
                lengths after generating as many batches of the requested size
                as possible some data may be left over.  If drop_last is True,
                this data will not be returned by the sampler (so all batches
                will have exactly the requested size).  If it is False, then
                the left-over data will be returned by the sampler in batches
                smaller than the requested size.  Default is False.
            randomize:
                A Boolean flag.  If True, iterating over this object will
                yield batches in a (pseudo-)random order of sequence lengths,
                and with the sequences of each length in (pseudo-)random order.
                Iterating multiple times over the entire dataset (by repeatedly
                exhausting this iteration) will yield different orderings of the
                data.  If False, the batches will be produced in the order of
                the underlying dataset.  Defaults to True.
            random_state:
                Either a numpy.random.RandomState or an integer (which will be
                used to seed a RandomState).  Used to initialize the pseudo-
                random generator used if randomize is True.  Optional (defaults
                to a reasonable fixed value for seeding, so even with
                randomize=True the order in which batches are returned is
                deterministic).
        """
        # The BatchSampler constructor demands a valid Sampler, so make one.
        sampler = Sampler(None)
        super().__init__(sampler, batch_size, drop_last)
        self.dataset = dataset
        self.randomize = randomize
        if isinstance(random_state, int):
            self.random_state = np.random.RandomState(seed=random_state)
        else:
            self.random_state = random_state
        self.item_length_to_first_index = {}
        cumulative_count = 0
        for item_length in self.dataset.available_item_lengths:
            self.item_length_to_first_index[item_length] = cumulative_count
            cumulative_count += self.dataset.item_counts[item_length]

    def __iter__(self):
        """
        Iterate through the dataset's items, making batches of uniform sequence
        length.  Yields lists of indices into the dataset (as required by use
        with DataLoaders).
        """
        available_lengths = self.dataset.available_item_lengths
        if len(available_lengths) < 1:
            return
        if self.randomize:
            available_lengths = self.random_state.permutation(available_lengths)
        for item_length in available_lengths:
            item_count = self.dataset.item_counts[item_length]
            first_index = self.item_length_to_first_index[item_length]
            if self.randomize:
                indices = first_index + self.random_state.permutation(item_count)
            else:
                indices = first_index + np.arange(item_count)
            batch_start = 0
            batch_end = self.batch_size
            while batch_end <= item_count:
                batch = indices[batch_start:batch_end].tolist()
                yield batch
                batch_start = batch_end
                batch_end = batch_start + self.batch_size
            if batch_start < item_count and not self.drop_last:
                batch = indices[batch_start:item_count].tolist()
                yield batch

    def __len__(self):
        """
        Return the number of batches (as do other BatchSamplers).
        """
        if self.drop_last:
            result = sum(
                self.dataset.item_counts[item_length] // self.batch_size
                for item_length in self.dataset.available_item_lengths
            )
            return result
        else:
            result = sum(
                (self.dataset.item_counts[item_length] + self.batch_size - 1)
                // self.batch_size
                for item_length in self.dataset.available_item_lengths
            )
            return result
