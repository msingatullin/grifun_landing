#!/usr/bin/env python3
"""Generate and persist Grifun blog articles from the NotebookLM topic backlog."""
from __future__ import annotations
import html, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "data" / "grifun-topic-backlog-500.json"
OUT = ROOT / "blog" / "articles"
LOG = ROOT / "data" / "grifun-article-publishing.log"
OUT.mkdir(parents=True, exist_ok=True)

def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")

def make_article(topic: dict) -> str:
    prompt = f"""Напиши практическую русскоязычную HTML-статью для блога Grifun.
Тема: {topic.get('title')}
Описание: {topic.get('description')}
Проблема читателя: {topic.get('problem')}
Результат: {topic.get('result')}
Категория: {topic.get('category')}

Верни только полный HTML-документ без Markdown. Не выдумывай клиентов, кейсы, цены, результаты
или цифры. Структура: title, description, canonical, Article JSON-LD, заголовок, лид, 3-5
подзаголовков, пошаговая диагностика, критерии проверки, типовые ошибки, краткий вывод.
Пиши для владельца бизнеса и технического специалиста в России, конкретно и без рекламной воды.
В конце добавь ссылку на /blog/ и контакты Grifun."""
    result = subprocess.run(["codex", "exec", "-c", "model_reasoning_effort=low", "--ephemeral", "--sandbox", "read-only", "--skip-git-repo-check", "-C", str(ROOT), prompt], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-1000:])
    text = re.sub(r"^```(?:html)?\s*|\s*```$", "", result.stdout.strip(), flags=re.I | re.S)
    if not re.match(r"<!doctype html>", text, re.I) or "<article" not in text or "<h1" not in text:
        raise ValueError("generated output is not a complete article")
    return text + "\n"

topics = json.loads(BACKLOG.read_text())
with LOG.open("a") as log:
    log.write(f"START topics={len(topics)}\n")
    for index, topic in enumerate(topics, 1):
        name = slug(topic["slug"])
        target = OUT / f"{name}.html"
        if target.exists():
            continue
        try:
            target.write_text(make_article(topic))
            log.write(f"[{index}/{len(topics)}] OK {name}\n")
            log.flush()
        except Exception as error:
            log.write(f"[{index}/{len(topics)}] FAILED {name}: {error}\n")
            log.flush()
            continue
print(f"GRIFUN_ARTICLES: {len(list(OUT.glob('*.html')))}")
