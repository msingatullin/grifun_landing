#!/usr/bin/env python3
"""Keep unvalidated baseline articles public but non-indexable until passports exist."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
plan = json.loads((ROOT / "seo-article-plan-batch-50.json").read_text(encoding="utf-8"))
new_slugs = {x["slug"] for x in plan["articles"]}
sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
staged = []
for path in sorted((ROOT / "blog/articles").glob("*.html")):
    if path.stem in new_slugs or f"/blog/articles/{path.name}" in sitemap:
        continue
    source = path.read_text(encoding="utf-8")
    robots = '<meta name="robots" content="noindex,follow">'
    if re.search(r'<meta\s+name=["\']robots["\'][^>]*>', source, re.I):
        source = re.sub(r'<meta\s+name=["\']robots["\'][^>]*>', robots, source, count=1, flags=re.I)
    elif "</head>" in source:
        source = source.replace("</head>", f"  {robots}\n</head>", 1)
    else:
        raise SystemExit(f"no </head> in {path}")
    path.write_text(source, encoding="utf-8")
    staged.append(path.stem)
(ROOT / "baseline-staging-manifest.json").write_text(json.dumps({
    "status": "non_indexable_pending_query_passports",
    "seo": "N/A — staged baseline is intentionally noindex and excluded from sitemap/index",
    "count": len(staged), "slugs": staged,
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": "ok", "staged_noindex": len(staged)}, ensure_ascii=False))
