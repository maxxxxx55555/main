"""Лексический поиск базы знаний: токенизация и релевантность (services/ai/scoring.py)."""

from __future__ import annotations

from app.services.ai.scoring import LexicalIndex, tokenize


def test_tokenize_normalizes_and_filters():
    tokens = tokenize("Капучино, цены и ЦЕНУ! 5")
    assert "капучин" in tokens  # окончание срезано
    assert "цен" in tokens  # разные формы → один корень
    assert all(len(t) >= 2 for t in tokens)  # одиночные символы отброшены
    assert tokens == [t.lower() for t in tokens]


def test_tokenize_ru_morphology_same_stem():
    """Разные падежи одного слова должны совпадать по корню."""
    for form in ("цена", "цены", "цену", "ценами"):
        assert "цен" in tokenize(form)


def test_index_returns_empty_for_empty_corpus():
    assert LexicalIndex([]).rank("любой запрос", top_k=3) == []


def test_index_returns_empty_when_no_match():
    index = LexicalIndex(["мы работаем с 9 до 18"])
    assert index.rank("космический корабль", top_k=3) == []


def test_index_ranks_relevant_document_first():
    docs = [
        "Мы кофейня на Ленина 5. Капучино — 250 рублей, латте — 300.",
        "Работаем ежедневно с 8:00 до 22:00, без выходных.",
        "Доставка по городу при заказе от 500 рублей.",
    ]
    index = LexicalIndex(docs)
    ranked = index.rank("сколько стоит капучино цена", top_k=3)
    assert ranked, "должен быть хотя бы один результат"
    assert ranked[0][0] == 0  # топ — документ с ценой капучино
    assert all(score > 0 for _idx, score in ranked)


def test_index_prefers_shorter_specific_document():
    """BM25 учитывает длину: короткий точный FAQ выше длинного полотна."""
    short = "Цена капучино — 250 рублей."
    long_doc = ("Прочая информация о кофейне. " * 30) + "Капучино упомянут вскользь."
    index = LexicalIndex([long_doc, short])
    ranked = index.rank("капучино цена", top_k=2)
    assert ranked[0][0] == 1  # документ 1 (short) — первый


def test_index_top_k_limits_results():
    docs = [f"кофе вариант {i}" for i in range(10)]
    ranked = LexicalIndex(docs).rank("кофе", top_k=3)
    assert len(ranked) == 3
