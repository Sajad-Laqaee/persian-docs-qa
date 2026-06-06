import re
import math
import pickle
from collections import Counter
from typing import List, Dict
from hazm import Normalizer, word_tokenize


class PersianTokenizer:
    def __init__(self):
        self.normalizer = Normalizer()
        self.stopwords = {
            "از", "به", "در", "که", "و", "یا", "را", "با", "برای",
            "این", "آن", "است", "می", "شود", "شد", "کرد", "های", "هایش",
        }

    def tokenize(self, text: str) -> List[str]:
        text = self.normalizer.normalize(text)
        tokens = word_tokenize(text)
        out = []
        for t in tokens:
            t = t.replace("\u200c", " ").strip()
            t = re.sub(r"[^\w]", "", t)
            if not t or len(t) <= 1 or t in self.stopwords:
                continue
            out.append(t)
        return out


class PersianBM25Encoder:
    """BM25 sparse encoder برای متون فارسی."""

    def __init__(self):
        self.idf_scores: Dict[str, float] = {}
        self.vocab: Dict[str, int] = {}
        self.k1 = 1.5
        self.b = 0.75
        self.avgdl = 0
        self.tokenizer = PersianTokenizer()

    def build_vocab_from_texts(self, texts: List[str]):
        all_tokens = Counter()
        doc_count = len(texts)
        total_length = 0

        for text in texts:
            tokens = self.tokenizer.tokenize(text)
            total_length += len(tokens)
            all_tokens.update(set(tokens))

        self.avgdl = total_length / doc_count if doc_count > 0 else 0
        self.vocab = {token: idx for idx, token in enumerate(all_tokens.keys())}

        for token, doc_freq in all_tokens.items():
            idf = math.log((doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
            self.idf_scores[token] = idf

    def encode_document(self, text: str) -> Dict[int, float]:
        tokens = self.tokenizer.tokenize(text)
        token_counts = Counter(tokens)
        doc_length = len(tokens)

        sparse_vector = {}
        for token, count in token_counts.items():
            if token in self.vocab:
                idx = self.vocab[token]
                idf = self.idf_scores.get(token, 1.0)
                tf = count
                score = idf * (tf * (self.k1 + 1)) / (
                    tf + self.k1 * (1 - self.b + self.b * doc_length / self.avgdl)
                ) if self.avgdl > 0 else 0.0
                sparse_vector[idx] = score
        return sparse_vector

    def encode_query(self, query: str) -> Dict[int, float]:
        tokens = self.tokenizer.tokenize(query)
        token_counts = Counter(tokens)

        sparse_vector = {}
        for token, count in token_counts.items():
            if token in self.vocab:
                idx = self.vocab[token]
                idf = self.idf_scores.get(token, 1.0)
                score = idf * (count * (self.k1 + 1)) / (count + self.k1)
                sparse_vector[idx] = score
        return sparse_vector

    def save(self, path: str):
        with open(path, "wb") as f:
            pickle.dump({
                "vocab": self.vocab,
                "idf_scores": self.idf_scores,
                "avgdl": self.avgdl,
                "k1": self.k1,
                "b": self.b,
            }, f)

    def load(self, path: str):
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.vocab = data["vocab"]
        self.idf_scores = data["idf_scores"]
        self.avgdl = data["avgdl"]
        self.k1 = data["k1"]
        self.b = data["b"]