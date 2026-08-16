#!/usr/bin/env python3
"""Add a visible and structured Ryazan service-area binding to the 50 articles."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
articles = json.loads((ROOT / "seo-article-plan-batch-50.json").read_text(encoding="utf-8"))["articles"]

SERVICES = {
    "cctv": ("Обследование и работы по видеонаблюдению", "Для объектов в Рязани и Рязанской области проверка начинается с исходной схемы, зон обзора, кабельных трасс, питания, сети и требований к архиву. Состав работ определяется по фактическому состоянию конкретного объекта."),
    "network": ("Обследование и работы по СКС и сетям", "Для объектов в Рязани и Рязанской области учитываются планировка, длины и состояние линий, помеховая обстановка, размещение узлов и требования к доступности. Решение формируется после проверки исходных данных объекта."),
    "access": ("Обследование и работы по СКУД", "Для объектов в Рязани и Рязанской области обследование учитывает точки прохода, режимы доступа, существующие контроллеры, кабельные линии и необходимые связи с другими инженерными системами."),
    "fire": ("Техническое обследование пожарной сигнализации", "Для объектов в Рязани и Рязанской области исходные данные собираются по прибору, шлейфам, питанию и журналу событий. Работы выполняются только в согласованном составе и в пределах необходимых допусков."),
    "server": ("Обследование и обслуживание ИТ-инфраструктуры", "Для организаций Рязани и Рязанской области обследование начинается с инвентаризации узлов, критичных сервисов, доступов, резервного копирования и наблюдаемых сбоев. Доступы и секреты в первичной заявке не запрашиваются."),
}

changed = 0
for article in articles:
    path = ROOT / "blog/articles" / f"{article['slug']}.html"; source = path.read_text(encoding="utf-8")
    if 'data-geo-area="ryazan-region"' in source:
        continue
    match = re.search(r'data-funnel-cluster="([^"]+)"', source)
    if not match or match.group(1) not in SERVICES:
        raise SystemExit(f"funnel cluster missing: {path}")
    cluster = match.group(1); service_name, context = SERVICES[cluster]
    block = f"""
        <div class="geo-binding" data-geo-area="ryazan-region">
          <h3>Работы в Рязани и Рязанской области</h3>
          <p>{html.escape(context)}</p>
        </div>
"""
    marker = '        <div class="funnel-actions">'
    if marker not in source:
        raise SystemExit(f"funnel actions missing: {path}")
    source = source.replace(marker, block + marker, 1)
    schema = {
        "@context": "https://schema.org", "@type": "Service", "name": service_name,
        "provider": {"@type": "Organization", "name": "Grifun", "url": "https://www.grifun.ru/"},
        "areaServed": [
            {"@type": "City", "name": "Рязань"},
            {"@type": "AdministrativeArea", "name": "Рязанская область"},
        ],
        "mainEntityOfPage": article["target_url"],
        "url": article["target_url"],
    }
    script = '<script id="grifun-service-area" type="application/ld+json">' + json.dumps(schema, ensure_ascii=False, separators=(",", ":")) + "</script>\n"
    source = source.replace("</head>", script + "</head>", 1)
    path.write_text(source, encoding="utf-8"); changed += 1
print(json.dumps({"status": "ok", "changed": changed}, ensure_ascii=False))
