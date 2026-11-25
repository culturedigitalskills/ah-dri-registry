#!/usr/bin/env python3
"""Validate the registry and build the static API and browse page.

Reads:   data/resources/*.yml, data/tools/*.yml, data/ai-services/*.yml,
         data/vocabularies.yml, schema/*.schema.json, schema/fields.yml
Writes:  site/  (published to GitHub Pages by the GitHub Action)

    site/index.html                       browse page
    site/api/v1/index.json                list of endpoints
    site/api/v1/<collection>.json         all entries in a collection
    site/api/v1/<collection>/<id>.json    one entry
    site/api/v1/<collection>.csv          spreadsheet download
    site/api/v1/vocabularies.json         controlled vocabularies
    site/api/v1/schema/*.schema.json      JSON Schemas
    site/api/v1/eosc/resources.json       draft EOSC Service Profile v5.0 mapping
    site/api/v1/report.json               completeness report

Usage:
    python scripts/build.py              # validate and build
    python scripts/build.py --validate   # validate only

The build stops with an error if an entry breaks the schema, if an ID does
not match its file name, if two entries share an ID, or if a reference
points to an entry that does not exist. Missing core fields and
"[to be confirmed]" markers are reported but do not stop the build.
"""
import csv
import datetime as dt
import io
import json
import shutil
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
API = SITE / "api" / "v1"
BASE_URL = "https://culturedigitalskills.github.io/ah-dri-registry"
TBC = "[to be confirmed]"

LICENCE = {
    "data": "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)",
    "code": "MIT",
    "attribution": "A&H DRI Registry, DRI community contributors",
}


def load_yaml(path):
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def normalise(value):
    """Turn YAML dates into ISO strings so they validate and serialise."""
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()[:10]
    if isinstance(value, list):
        return [normalise(v) for v in value]
    if isinstance(value, dict):
        return {k: normalise(v) for k, v in value.items()}
    return value


def main():
    validate_only = "--validate" in sys.argv
    fields = load_yaml(ROOT / "schema" / "fields.yml")
    vocabs = load_yaml(ROOT / "data" / "vocabularies.yml")

    errors, warnings = [], []
    collections = {}  # coll_name -> list of records
    for coll_name, coll in fields.items():
        slug = coll_name.replace("_", "-")
        schema = json.loads((ROOT / "schema" / f"{slug}.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        records, seen = [], set()
        for path in sorted((ROOT / coll["folder"]).glob("*.yml")):
            rel = path.relative_to(ROOT)
            try:
                rec = normalise(load_yaml(path) or {})
            except yaml.YAMLError as exc:
                errors.append(f"{rel}: not valid YAML ({exc})")
                continue
            # Drop empty values that an editor may have left behind
            rec = {k: v for k, v in rec.items() if v not in (None, "", [])}
            for err in sorted(validator.iter_errors(rec), key=lambda e: list(e.path)):
                where = ".".join(str(p) for p in err.path) or "(entry)"
                errors.append(f"{rel}: {where}: {err.message}")
            rid = rec.get("id")
            if rid and rid != path.stem:
                errors.append(f"{rel}: id '{rid}' does not match the file name '{path.stem}'")
            if rid in seen:
                errors.append(f"{rel}: duplicate id '{rid}'")
            seen.add(rid)
            records.append(rec)
        collections[coll_name] = records

    # References between collections
    for coll_name, coll in fields.items():
        for f in coll["fields"]:
            if f["type"] != "reference":
                continue
            targets = {r.get("id") for r in collections[f["collection"]]}
            for rec in collections[coll_name]:
                vals = rec.get(f["key"], [])
                vals = vals if isinstance(vals, list) else [vals]
                for v in vals:
                    if v not in targets:
                        errors.append(
                            f"{fields[coll_name]['folder']}/{rec.get('id')}.yml: {f['key']}: "
                            f"'{v}' is not an id in {fields[f['collection']]['folder']}"
                        )

    # Completeness report (warnings only)
    report = {}
    for coll_name, coll in fields.items():
        core = [f["key"] for f in coll["fields"] if f.get("core")]
        entries = []
        for rec in collections[coll_name]:
            missing = [k for k in core if k not in rec]
            tbc = [k for k, v in rec.items() if isinstance(v, str) and TBC in v]
            if missing or tbc:
                entries.append({"id": rec.get("id"), "missing_core_fields": missing, "to_be_confirmed": tbc})
                if missing:
                    warnings.append(f"{coll_name}/{rec.get('id')}: missing core fields: {', '.join(missing)}")
        report[coll_name.replace("_", "-")] = {
            "entries": len(collections[coll_name]),
            "entries_needing_attention": entries,
        }

    for w in warnings:
        print(f"note: {w}")
    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  ERROR {e}")
        sys.exit(1)
    counts = ", ".join(f"{len(v)} {k.replace('_', ' ')}" for k, v in collections.items())
    print(f"\nValid: {counts}.")
    if validate_only:
        return

    build_site(fields, vocabs, collections, report)
    print(f"Built {SITE.relative_to(ROOT)}/")


def order(rec, coll):
    keys = [f["key"] for f in coll["fields"]]
    return {k: rec[k] for k in keys if k in rec}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def to_csv(records, coll):
    keys = [f["key"] for f in coll["fields"]]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=keys, extrasaction="ignore")
    w.writeheader()
    for rec in records:
        w.writerow({k: "; ".join(v) if isinstance(v, list) else v for k, v in rec.items()})
    return buf.getvalue()


def eosc_export(resources, fields, vocabs):
    """Draft mapping of resources to EOSC Service Profile v5.0 element names.

    Only fields with an EOSC equivalent are included, and controlled values
    are converted to EOSC vocabulary IDs. Admin fields an EOSC submission
    needs (logo, contacts, TRL) must be supplied by each provider.
    """
    ids = {name: {str(v["label"]): v.get("eosc_id") for v in vals} for name, vals in vocabs.items()}
    out = []
    for r in resources:
        e = {
            "abbreviation": r.get("short_name"),
            "name": r.get("name"),
            "resourceOrganisation": r.get("provider"),
            "webpage": r.get("webpage"),
            "description": r.get("description"),
            "tagline": r.get("tagline"),
            "logo": r.get("logo_url"),
            "categories": [{
                "category": "category-access_physical_and_einfrastructures-compute",
                "subcategory": ids["eosc_subcategory"].get(r.get("eosc_subcategory")),
            }] if r.get("eosc_subcategory") else None,
            "scientificDomains": [{"scientificDomain": ids["scientific_domain"].get(r.get("scientific_domain"))}] if r.get("scientific_domain") else None,
            "targetUsers": [ids["target_users"].get(r.get("target_users"))] if r.get("target_users") else None,
            "accessModes": [ids["access_mode"].get(r.get("access_mode"))] if r.get("access_mode") else None,
            "accessTypes": [ids["access_type"].get(r.get("access_type"))] if r.get("access_type") else None,
            "orderType": ids["order_type"].get(r.get("order_type")),
            "trl": ids["trl"].get(r.get("trl")),
            "lifeCycleStatus": ids["life_cycle_status"].get(r.get("life_cycle_status")),
            "geographicalAvailabilities": r.get("geographical_availability"),
            "languageAvailabilities": r.get("language_availability"),
            "resourceGeographicLocations": r.get("server_location"),
            "certifications": r.get("certifications"),
            "termsOfUse": r.get("terms_of_use_url"),
            "privacyPolicy": r.get("privacy_policy_url"),
            "userManual": r.get("user_manual_url"),
            "trainingInformation": r.get("training_url"),
            "pricing": r.get("pricing_url"),
            "helpdeskEmail": r.get("helpdesk_email"),
            "securityContactEmail": r.get("security_contact_email"),
            "publicContacts": [r["public_contact_email"]] if r.get("public_contact_email") else None,
            "x-registry-id": r.get("id"),
        }
        out.append({k: v for k, v in e.items() if v is not None})
    return {
        "note": "Draft mapping to EOSC Service Profile v5.0 element names and vocabulary IDs. "
                "Free-text fields are not yet split into EOSC's structured formats "
                "(e.g. country codes for geographical availability). Check before submitting to EOSC.",
        "profile": "https://eosc-service-profile.readthedocs.io/en/5.0/",
        "resources": out,
    }


def build_site(fields, vocabs, collections, report):
    if SITE.exists():
        shutil.rmtree(SITE)
    API.mkdir(parents=True)
    generated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    endpoints = {}
    for coll_name, coll in fields.items():
        slug = coll_name.replace("_", "-")
        recs = sorted((order(r, coll) for r in collections[coll_name]), key=lambda r: r["name"].lower())
        write_json(API / f"{slug}.json", {
            "collection": slug,
            "title": coll["label"],
            "description": coll.get("description", ""),
            "generated": generated,
            "licence": LICENCE,
            "count": len(recs),
            "items": recs,
        })
        for r in recs:
            write_json(API / slug / f"{r['id']}.json", r)
        (API / f"{slug}.csv").write_text(to_csv(recs, coll), encoding="utf-8")
        (API / "schema").mkdir(exist_ok=True)
        shutil.copy(ROOT / "schema" / f"{slug}.schema.json", API / "schema" / f"{slug}.schema.json")
        endpoints[slug] = {
            "all": f"{BASE_URL}/api/v1/{slug}.json",
            "one": f"{BASE_URL}/api/v1/{slug}/{{id}}.json",
            "csv": f"{BASE_URL}/api/v1/{slug}.csv",
            "schema": f"{BASE_URL}/api/v1/schema/{slug}.schema.json",
        }
    write_json(API / "vocabularies.json", vocabs)
    write_json(API / "eosc" / "resources.json", eosc_export(
        sorted(collections["resources"], key=lambda r: r["name"].lower()), fields, vocabs))
    write_json(API / "report.json", {"generated": generated, "collections": report})
    write_json(API / "index.json", {
        "name": "A&H DRI Registry API",
        "version": "v1",
        "description": "Compute, tools and AI services for UK arts and humanities researchers.",
        "generated": generated,
        "licence": LICENCE,
        "source": "https://github.com/culturedigitalskills/ah-dri-registry",
        "endpoints": endpoints,
        "vocabularies": f"{BASE_URL}/api/v1/vocabularies.json",
        "eosc_export": f"{BASE_URL}/api/v1/eosc/resources.json",
        "report": f"{BASE_URL}/api/v1/report.json",
    })
    shutil.copy(ROOT / "web" / "index.html", SITE / "index.html")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")


if __name__ == "__main__":
    main()
