import numpy as np
import sentencepiece as spm


class SpmIdsTranslator:
    """
    Providers of encoding/decoding services between spm ids and text.
    """

    def __init__(self, model_path, id_dtype=np.int16):
        """
        Constructor for SpmIdsTranslator.

        Arguments:
            model_path:
                The path (pathlib.Path or string) to a trained SentencePiece model.
            id_dtype:
                Optional (with default np.int16), a numpy integer type big
                enough to hold any id in the model's vocabulary.
        """
        self.spm_processor = spm.SentencePieceProcessor()
        self.spm_processor.Load(str(model_path))
        self.id_dtype = id_dtype
        self.start_symbol = self.spm_processor["<s>"]
        self.end_symbol = self.spm_processor["</s>"]
        # Number of ids should not exceed 2 raised to the number of bits in
        # the requested data type, which in turn is 8 bits per byte times
        # the size of the data type in bytes.
        if self.number_of_ids() > pow(2, 8 * np.dtype(self.id_dtype).itemsize):
            raise ValueError(
                "Too many ids ({}) for requested data type {}.".format(
                    self.number_of_ids(), self.id_dtype
                )
            )

    def number_of_ids(self):
        """
        Returns the number of distinct ids (tokens) of the trained model.

        Arguments:  None.
        """
        return len(self.spm_processor)

    def one_to_ids(self, text, add_start_symbol=True, add_end_symbol=True):
        """
        Translate a string to a numpy array of spm ids.

        Arguments:
            text:
                The string to translate (required).
            add_start_symbol:
                Optional (default True).  If True, the start-of-sequence
                symbol is prepended to the output.
            add_end_symbol:
                Optional (default True).  If True, the end-of-sequence symbol
                is appended to the output.

        Returns the translation of the string.
        """
        ids = self.spm_processor.EncodeAsIds(text)
        if add_start_symbol:
            ids = [self.start_symbol] + ids
        if add_end_symbol:
            ids += [self.end_symbol]
        return np.array(ids, dtype=self.id_dtype)

    def many_to_ids(self, texts, add_start_symbol=True, add_end_symbol=True):
        """
        Generate numpy arrays of spm ids from an iterable of strings.

        Arguments:
            texts:
                The iterable of strings to be translated.
            add_start_symbol:
                Optional (default True).  If True, the start-of-sequence
                symbol is prepended to each output.
            add_end_symbol:
                Optional (default True).  If True, the end-of-sequence symbol
                is appended to each output.

        Yields the translations of the strings.
        """
        prefix = [self.start_symbol] if add_start_symbol else []
        suffix = [self.end_symbol] if add_end_symbol else []
        for text in texts:
            ids = prefix + self.spm_processor.EncodeAsIds(text) + suffix
            yield np.array(ids, dtype=self.id_dtype)

    def one_to_text(self, id_seq):
        """
        Translate an iterable of spm ids to the corresponding text.

        Arguments:
            id_seq:
                The iterable of spm ids to be translated.

        Returns the (string) translation of the ids.
        """
        return self.spm_processor.DecodeIds([int(i) for i in id_seq])

    def many_to_texts(self, id_seqs):
        """
        Generate strings from an iterable of sequences of spm ids.

        Arguments:
            id_seqs:
                The iterable of individual sequences of spm ids.

        Yields the translations of the individual sequences.
        """
        for id_seq in id_seqs:
            yield self.spm_processor.DecodeIds([int(i) for i in id_seq])
