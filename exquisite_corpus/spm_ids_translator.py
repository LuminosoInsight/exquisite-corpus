import numpy as np
import sentencepiece as spm


class SpmIdsTranslator:
    """
    Providers of encoding/decoding services between spm ids and text.
    """

    def __init__(self, model_path, id_dtype=np.int16):
        """
        Constructor for SpmIdsTranslator.  Required argument: model_path, a
        string giving the path to a trained SentencePiece model.  Optional
        argument:  id_dtype (default np.int16), a numpy integer type big
        enough to hold any id in the model's vocabulary.
        """
        self.spm_processor = spm.SentencePieceProcessor()
        self.spm_processor.Load(model_path)
        self.id_dtype = id_dtype

    def one_to_ids(self, text):
        """
        Translate a string to a numpy array of spm ids.
        """
        return np.array(self.spm_processor.EncodeAsIds(text), dtype=self.id_dtype)

    def many_to_ids(self, texts):
        """
        Generate numpy arrays of spm ids from an iterable of strings.
        """
        for text in texts:
            yield np.array(self.spm_processor.EncodeAsIds(text), dtype=self.id_dtype)

    def one_to_text(self, id_seq):
        """
        Translate an iterable of spm ids to the corresponding text.
        """
        return self.spm_processor.DecodeIds([int(i) for i in id_seq])

    def many_to_texts(self, id_seqs):
        """
        Generate strings from an iterable of sequences of spm ids.
        """
        for id_seq in id_seqs:
            yield self.spm_processor.DecodeIds([int(i) for i in id_seq])
