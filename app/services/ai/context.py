"""Сборка контекста LLM: система + окно последних сообщений с бюджетом токенов (§6.3)."""

from __future__ import annotations


def approx_tokens(text: str) -> int:
    """Грубая оценка: ~4 символа на токен (кириллица — консервативно)."""
    return max(len(text) // 4, 1)


def build_context(
    system_prompt: str,
    history: list[tuple[str, str]],  # [(role, content)] хронологически
    context_window: int,
    token_budget: int,
) -> list[dict[str, str]]:
    """Последние N сообщений, обрезанные под бюджет; budget считается «хвостом»."""
    tail = history[-context_window:]
    used = approx_tokens(system_prompt)
    kept: list[dict[str, str]] = []
    for role, content in reversed(tail):
        cost = approx_tokens(content)
        if used + cost > token_budget:
            break
        used += cost
        kept.append({"role": role, "content": content})
    kept.reverse()
    return [{"role": "system", "content": system_prompt}, *kept]