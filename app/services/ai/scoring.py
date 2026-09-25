"""Лексический поиск (BM25-lite) для базы знаний на SQLite — без внешних сервисов.

Почему не «игрушечные» эмбеддинги: детерминированный хеш текста не отражает
семантику, поэтому косинусная близость таких векторов — шум. Для FAQ/цен/условий
честный лексический поиск с IDF и учётом длины документа даёт реальную выдачу,
а семантику при желании обеспечивает ChromaDB (встроенная ONNX-модель).

Оценка BM25 (k1=1.5, b=0.75) по токенам с лёгкой нормализацией русских окончаний.
"""

from __future__ import annotations

import math
import re

_TOKEN_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё]+")
_MIN_TOKEN_LEN = 2

# Грубая нормализация: срезаем частотные русские окончания (цена/цены/цену → цен).
_ENDINGS = (
    "ями", "ами", "ого", "его", "ому", "ему", "ыми", "ими", "ей", "ой", "ых", "их",
    "ую", "юю", "ая", "яя", "ое", "ее", "ам", "ям", "ах", "ях", "ов", "ев", "ий",
    "ый", "ые", "ие", "ым", "им", "у", "ю", "а", "я", "ы", "и", "е", "о",
)


def _stem(token: str) -> str:
    """Срезает частотное русское окончание, оставляя корень ≥3 символов.

    Примеры: цена/цены/цену/ценами → цен; капучино → капучин; мы → мы.
    """
    if len(token) < 4:
        return token
    for ending in _ENDINGS:
        if token.endswith(ending) and len(token) - len(ending) >= 3:
            return token[: -len(ending)]
    return token


def tokenize(text: str) -> list[str]:
    """Токены нижнего регистра с нормализацией окончаний."""
    return [
        _stem(match.group(0).lower())
        for match in _TOKEN_RE.finditer(text)
        if len(match.group(0)) >= _MIN_TOKEN_LEN
    ]


class LexicalIndex:
    """BM25-lite индекс по небольшому корпусу (база знаний одного владельца)."""

    K1 = 1.5
    B = 0.75

    def __init__(self, docs: list[str]) -> None:
        self._doc_tokens = [tokenize(doc) for doc in docs]
        self._doc_lens = [len(tokens) for tokens in self._doc_tokens]
        self._avg_len = (sum(self._doc_lens) / len(docs)) if docs else 0.0
        self._df: dict[str, int] = {}
        for tokens in self._doc_tokens:
            for token in set(tokens):
                self._df[token] = self._df.get(token, 0) + 1

    def rank(self, query: str, top_k: int) -> list[tuple[int, float]]:
        """[(index документа, score)] по убыванию score; только score > 0."""
        total = len(self._doc_tokens)
        if total == 0:
            return []
        query_tokens = set(tokenize(query))
        if not query_tokens:
            return []

        scored: list[tuple[int, float]] = []
        for idx, tokens in enumerate(self._doc_tokens):
            if not tokens:
                continue
            freq: dict[str, int] = {}
            for token in tokens:
                freq[token] = freq.get(token, 0) + 1
            score = 0.0
            for token in query_tokens:
                tf = freq.get(token, 0)
                if not tf:
                    continue
                df = self._df.get(token, 0)
                idf = math.log(1 + (total - df + 0.5) / (df + 0.5))
                length_norm = 1 - self.B + self.B * (self._doc_lens[idx] / (self._avg_len or 1))
                score += idf * (tf * (self.K1 + 1)) / (tf + self.K1 * length_norm)
            if score > 0:
                scored.append((idx, score))

        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]
