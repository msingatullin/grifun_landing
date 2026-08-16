#!/usr/bin/env python3
"""Validate that every batch article participates in the Grifun client funnel."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
plan = json.loads((ROOT / "seo-article-plan-batch-50.json").read_text(encoding="utf-8"))["articles"]
errors = []
campaigns = set()
for article in plan:
    path = ROOT / "blog/articles" / f"{article['slug']}.html"; source = path.read_text(encoding="utf-8")
    campaign = article["slug"]
    checks = {
        "contextual_funnel": 'id="client-next-step"' in source and 'data-funnel-cluster=' in source,
        "lead_path": f"utm_campaign={campaign}" in source and "#contact" in source,
        "service_path": 'href="/#services"' in source,
        "telegram_path": 'href="https://t.me/msrzn007"' in source,
        "next_step": "Следующий шаг:" in source,
        "related_pages": len(re.findall(r'<a href="/blog/articles/[^"#]+\.html">', source)) >= 2,
    }
    campaigns.add(campaign)
    for name, passed in checks.items():
        if not passed: errors.append(f"{article['slug']}:{name}")
print(json.dumps({"status": "ok" if not errors else "blocked", "articles": len(plan), "unique_campaigns": len(campaigns), "errors": errors}, ensure_ascii=False))
raise SystemExit(bool(errors))
