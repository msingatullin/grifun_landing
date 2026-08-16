#!/usr/bin/env python3
"""Add the gated Grifun batch to the blog index and sitemap idempotently."""
from __future__ import annotations

import html
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
plan = json.loads((ROOT / "seo-article-plan-batch-50.json").read_text(encoding="utf-8"))
index_path = ROOT / "blog/index.html"; index = index_path.read_text(encoding="utf-8")
cards = []
for a in plan["articles"]:
    href = f"./articles/{a['slug']}.html"
    if href not in index:
        cards.append(f'    <article><p class="tag">Практика Grifun</p><h2><a href="{href}">{html.escape(a["title"])}</a></h2><p>{html.escape(a["intent"].removeprefix("informational:").strip().capitalize())}.</p></article>')
if cards:
    index = index.replace("  </section>", "\n".join(cards) + "\n  </section>", 1)
    index_path.write_text(index, encoding="utf-8")

ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(ROOT / "sitemap.xml"); urlset = tree.getroot(); ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
existing = {node.text for node in urlset.findall(f"{ns}url/{ns}loc")}
added = 0
for a in plan["articles"]:
    if a["target_url"] in existing:
        continue
    node = ET.SubElement(urlset, f"{ns}url")
    ET.SubElement(node, f"{ns}loc").text = a["target_url"]
    ET.SubElement(node, f"{ns}lastmod").text = "2026-08-16"
    ET.SubElement(node, f"{ns}changefreq").text = "monthly"
    ET.SubElement(node, f"{ns}priority").text = "0.7"
    added += 1
ET.indent(tree, space="  "); tree.write(ROOT / "sitemap.xml", encoding="utf-8", xml_declaration=True)
print(json.dumps({"status": "ok", "index_additions": len(cards), "sitemap_additions": added}, ensure_ascii=False))
