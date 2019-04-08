import numpy as np

from pathlib import Path
from torch.utils.data import Dataset, BatchSampler, Sampler


class SpmIdsDataset(Dataset):
    """
    A subclass of Pytorch's Dataset class that exposes a the output of
    split_sentencepiece_ids and sentencepiece_id_converter.  (Principally,
    this means a directory full of .npy files containing matrices whose rows
    are the sequences of SentencePiece id's corresponding to a set of input
    sentences; we assume each such .npy file corresponds to a distinct length
    of input sentences.)  Only sentences with sequence length greater than
    zero are taken to be data items.

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
        self.datatype = datatype
        self.mmap_mode = "r" if mmap else None
        npy_root_path = Path(npy_directory)
        self.npy_paths = {}  # map item lengths to corresponding npy files
        self.item_counts = {}  # map item lengths to number of corresponding items
        self.max_item_length = -1  # max length for which there really are any items
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
        return self.total_item_count

    def __getitem__(self, i_item):
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
    randomizing the batches they return.

    Additionally, to ease use with multiple GPUs, the attributes n_shares
    and share_index may be set to share each batch among several consumers
    by splitting it into shards.  Set n_shares to the number of consumers
    (GPUs) and, in code to be executed on the consumers, set shared_index
    to a unique value per consumer (e.g. the device id of a GPU).  Note that
    when n_shares is greater than one the shares returned will have the
    requested batch_size, so the batches that are split among the consumers
    become larger.  Also note that in this use case it is neither necessary
    nor desirable to set different random states on the different consumers;
    giving them all the same random state ensures they get disjoint shards
    of each batch.
    """

    def __init__(
        self,
        dataset,
        batch_size,
        drop_last=False,
        n_shares=1,
        share_index=0,
        randomize=True,
        random_state=101,
    ):
        # The BatchSampler constructor demands a valid Sampler, so make one.
        sampler = Sampler(None)
        # If the requested number of pieces into which each batch will be
        # shared is greater than one, increase the nominal batch sixe so
        # that each share is of the requested batch size.
        self.n_shares = n_shares
        batch_size *= self.n_shares
        super().__init__(sampler, batch_size, drop_last)
        self.share_index = share_index
        if not (0 <= self.share_index < self.n_shares):
            raise ValueError(
                "Share index {} not less than number of shares {}.".format(
                    self.share_index, self.n_shares
                )
            )
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
        available_lengths = self.dataset.available_item_lengths
        if len(available_lengths) < 1:
            return
        if self.randomize:
            available_lengths = self.random_state.permutation(available_lengths)
        share_size = self.batch_size // self.n_shares
        share_start_offset = share_size * self.share_index
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
                share_start = batch_start + share_start_offset
                share_end = share_start + share_size
                share = indices[share_start:share_end].tolist()
                yield share
                batch_start = batch_end
                batch_end = batch_start + self.batch_size
            if batch_start < item_count and not self.drop_last:
                # If batches are being split into more than one share,
                # make all the shares of the final runt batch have the
                # same size by padding the last one if necessary.
                share_size = (
                    item_count - batch_start + self.n_shares - 1
                ) // self.n_shares
                share_start_offset = share_size * self.share_index
                share_start = batch_start + share_start_offset
                share_end = share_start + share_size
                if share_end <= item_count:
                    share = indices[share_start:share_end].tolist()
                else:
                    # Pad by wrapping around to the start of the indices.
                    share = indices[
                        [i % len(indices) for i in range(share_start, share_end)]
                    ].tolist()
                yield share

    def __len__(self):
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
