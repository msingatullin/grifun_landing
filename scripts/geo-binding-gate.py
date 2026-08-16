#!/usr/bin/env python3
"""Verify visible and structured Ryazan binding without changing SEO ownership."""
from __future__ import annotations

import json
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
articles = json.loads((ROOT / "seo-article-plan-batch-50.json").read_text(encoding="utf-8"))["articles"]
errors = []
def normalized(value: str) -> str:
    visible = html.unescape(re.sub(r"<[^>]+>", " ", value))
    return " ".join(re.findall(r"[a-zа-яё0-9]+", visible.casefold()))

for article in articles:
    source = (ROOT / "blog/articles" / f"{article['slug']}.html").read_text(encoding="utf-8")
    can = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', source, re.I)
    schemas = []
    for raw in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', source, re.I | re.S):
        try: schemas.append(json.loads(raw))
        except json.JSONDecodeError: errors.append(f"{article['slug']}:invalid-jsonld")
    services = [x for x in schemas if isinstance(x, dict) and x.get("@type") == "Service"]
    area_names = {y.get("name") for x in services for y in x.get("areaServed", []) if isinstance(y, dict)}
    checks = {
        "visible_region": "Рязани и Рязанской области" in source and 'data-geo-area="ryazan-region"' in source,
        "service_schema": len(services) == 1,
        "area_served": {"Рязань", "Рязанская область"} <= area_names,
        "regional_cta": "Работы в Рязани и Рязанской области" in source,
        "canonical_unchanged": bool(can) and can.group(1) == article["target_url"],
        "primary_unchanged": normalized(article["primary_query"]) in normalized(source),
    }
    for name, passed in checks.items():
        if not passed: errors.append(f"{article['slug']}:{name}")
print(json.dumps({"status": "ok" if not errors else "blocked", "articles": len(articles), "errors": errors}, ensure_ascii=False))
raise SystemExit(bool(errors))
