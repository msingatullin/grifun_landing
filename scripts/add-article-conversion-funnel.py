#!/usr/bin/env python3
"""Attach a contextual, measurable B2B conversion path to the 50 SEO articles."""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
plan = json.loads((ROOT / "seo-article-plan-batch-50.json").read_text(encoding="utf-8"))["articles"]

GROUPS = {
    "cctv": {
        "match": ("видеонаблю", "poe", "камер", "архив"),
        "title": "Нужно проверить или развить видеонаблюдение на объекте?",
        "body": "Grifun может обследовать камеры, линии, питание, сеть и архив, затем зафиксировать найденные ограничения и состав работ без замены оборудования наугад.",
        "prep": "Укажите тип объекта, число камер и проблему; если есть — приложите схему или фотографии оборудования.",
        "button": "Обсудить обследование видеонаблюдения",
    },
    "network": {
        "match": ("скс", "кабел", "wifi", "vlan", "сет", "оптовол", "витой"),
        "title": "Нужна диагностика СКС, Wi‑Fi или локальной сети?",
        "body": "Grifun может обследовать трассы и активное оборудование, локализовать узкое место и подготовить проверяемый перечень работ для монтажа или исправления сети.",
        "prep": "Укажите площадь и назначение объекта, число рабочих мест или точек доступа и наблюдаемые симптомы.",
        "button": "Обсудить обследование сети",
    },
    "access": {
        "match": ("скуд", "доступ", "рабочего времени"),
        "title": "Нужно обследовать или модернизировать СКУД?",
        "body": "Grifun поможет проверить точки прохода, контроллеры, права доступа и связи с видеонаблюдением, а затем отделить настройку от работ, требующих модернизации.",
        "prep": "Укажите число дверей и пользователей, тип идентификаторов и задачу: новый монтаж, неисправность или интеграция.",
        "button": "Обсудить задачу по СКУД",
    },
    "fire": {
        "match": ("пожар", "шлейф"),
        "title": "Нужна техническая проверка пожарной сигнализации?",
        "body": "Grifun может собрать исходные данные по шлейфам, питанию и повторяющимся неисправностям и определить состав обследования в пределах согласованных допусков.",
        "prep": "Укажите тип объекта, оборудование, текст события на приборе и когда возникает неисправность или ложное срабатывание.",
        "button": "Обсудить техническую проверку",
    },
    "server": {
        "match": ("сервер", "резервн", "администратор", "инфраструктур", "аутсорсинг", "ит ", "мониторинг"),
        "title": "Нужно привести ИТ‑инфраструктуру в контролируемое состояние?",
        "body": "Grifun может провести инвентаризацию, проверить доступы, мониторинг и резервное копирование, затем подготовить приоритетный перечень рисков и работ.",
        "prep": "Укажите число серверов и рабочих мест, критичные сервисы и текущую проблему; доступы в первом сообщении не передавайте.",
        "button": "Обсудить ИТ‑обследование",
    },
}


def group(query: str) -> str:
    low = query.casefold()
    if "скуд" in low:
        return "access"
    scores = {name: sum(token in low for token in data["match"]) for name, data in GROUPS.items()}
    return max(scores, key=scores.get)


clusters: dict[str, list[dict]] = {name: [] for name in GROUPS}
for article in plan:
    clusters[group(article["primary_query"])].append(article)

css = """
  <style id="grifun-funnel-style">
    .funnel-box{margin:40px 0 8px;padding:28px;border:1px solid #cbd8dc;border-radius:14px;background:#f5f9fa}
    .funnel-box h2{margin-top:0}.funnel-next{padding-left:20px}.funnel-actions{display:flex;flex-wrap:wrap;gap:12px;margin:22px 0}
    .funnel-actions a{display:inline-block;padding:12px 16px;border-radius:8px;background:#176b78;color:#fff;text-decoration:none;font-weight:700}
    .funnel-actions a.secondary{background:#fff;color:#176b78;border:1px solid #176b78}.funnel-related{margin-bottom:0}
    @media(max-width:600px){.funnel-box{padding:20px}.funnel-actions a{width:100%;box-sizing:border-box;text-align:center}}
  </style>
"""

changed = 0
for article in plan:
    path = ROOT / "blog/articles" / f"{article['slug']}.html"
    source = path.read_text(encoding="utf-8").replace('/#contacts', '/#contact')
    if 'id="client-next-step"' in source:
        continue
    name = group(article["primary_query"]); data = GROUPS[name]; peers = clusters[name]
    pos = next(i for i, item in enumerate(peers) if item["slug"] == article["slug"])
    related = [peers[(pos + step) % len(peers)] for step in (1, 2) if len(peers) > step]
    campaign = article["slug"]
    contact = f"/?utm_source=grifun_blog&amp;utm_medium=content&amp;utm_campaign={campaign}&amp;utm_content=cta#contact"
    related_html = " · ".join(
        f'<a href="/blog/articles/{item["slug"]}.html">{html.escape(item["title"])}</a>' for item in related
    )
    block = f"""
      <section class="funnel-box" id="client-next-step" data-funnel-cluster="{name}">
        <h2>{html.escape(data['title'])}</h2>
        <p>{html.escape(data['body'])}</p>
        <p><strong>Следующий шаг:</strong> {html.escape(data['prep'])}</p>
        <div class="funnel-actions">
          <a href="{contact}" data-funnel-action="lead">{html.escape(data['button'])}</a>
          <a class="secondary" href="/#services" data-funnel-action="services">Посмотреть услуги Grifun</a>
          <a class="secondary" href="https://t.me/msrzn007" target="_blank" rel="noopener" data-funnel-action="telegram">Написать в Telegram</a>
        </div>
        <p class="funnel-related"><strong>По теме:</strong> {related_html}</p>
      </section>
"""
    if "</article>" not in source or "</head>" not in source:
        raise SystemExit(f"required marker missing: {path}")
    source = source.replace("</head>", css + "</head>", 1)
    source = source.replace("</article>", block + "    </article>", 1)
    path.write_text(source, encoding="utf-8")
    changed += 1
print(json.dumps({"status": "ok", "changed": changed, "clusters": {k: len(v) for k, v in clusters.items()}}, ensure_ascii=False))
