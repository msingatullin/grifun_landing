#!/usr/bin/env python3
"""Block Grifun article generation without an evidence-backed SEO passport."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = ROOT / "seo-query-map.json"
FREQUENCY_CLASSES = {"low", "medium", "high"}


def valid_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.netloc == "www.grifun.ru"


def validate(slug: str) -> list[str]:
    try:
        data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read {MAP_PATH.name}: {exc}"]
    passport = data.get("articles", {}).get(slug)
    if not isinstance(passport, dict):
        return [f"{slug}: query passport not found"]
    errors: list[str] = []
    for field in ("primary_query", "intent", "region", "language", "target_url", "pillar_url", "cannibalization_evidence"):
        if not isinstance(passport.get(field), str) or not passport[field].strip():
            errors.append(f"{slug}: missing {field}")
    expected = f"https://www.grifun.ru/blog/articles/{slug}.html"
    if passport.get("target_url") != expected:
        errors.append(f"{slug}: target_url must equal {expected}")
    if not valid_url(passport.get("pillar_url")):
        errors.append(f"{slug}: invalid pillar_url")
    if passport.get("cannibalization_status") != "passed":
        errors.append(f"{slug}: cannibalization_status is {passport.get('cannibalization_status')!r}, expected 'passed'")
    links = passport.get("internal_links")
    if not isinstance(links, list) or not links or not all(valid_url(url) for url in links):
        errors.append(f"{slug}: valid internal_links are required")
    measurements = passport.get("measurements")
    if not isinstance(measurements, list) or not measurements:
        errors.append(f"{slug}: measurements are required")
        return errors
    classes = set()
    queries = set()
    today = dt.date.today()
    for index, row in enumerate(measurements, 1):
        prefix = f"{slug}: measurement #{index}"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        query = row.get("query")
        if isinstance(query, str) and query.strip():
            queries.add(query.strip().casefold())
        else:
            errors.append(f"{prefix} missing query")
        frequency_class = row.get("frequency_class")
        if frequency_class in FREQUENCY_CLASSES:
            classes.add(frequency_class)
        else:
            errors.append(f"{prefix} invalid frequency_class")
        value = row.get("frequency_value")
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"{prefix} invalid frequency_value")
        for field in ("source", "metric", "measurement_period", "region", "match_type", "evidence_ref"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"{prefix} missing {field}")
        try:
            measured = dt.date.fromisoformat(row.get("measured_at"))
            if measured > today or (today - measured).days > 90:
                errors.append(f"{prefix} evidence date outside allowed window")
        except (TypeError, ValueError):
            errors.append(f"{prefix} invalid measured_at")
    if str(passport.get("primary_query", "")).casefold() not in queries:
        errors.append(f"{slug}: primary_query has no measurement")
    for required in FREQUENCY_CLASSES:
        if required not in classes:
            errors.append(f"{slug}: missing {required}-frequency measurement")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    args = parser.parse_args()
    slug = re.sub(r"[^a-z0-9-]+", "-", args.slug.lower()).strip("-")
    errors = validate(slug)
    if errors:
        print("SEO_QUERY_GATE: BLOCKED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"SEO_QUERY_GATE: OK ({slug})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
