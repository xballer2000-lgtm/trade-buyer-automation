"""Opt-in authorized JSON API discovery with auditable buyer evidence.

Providers must supply the documented schema directly or through their authorized
export/adapter. This module never scrapes HTML or infers purchases from a name.
"""
import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
import urllib.request
from urllib.parse import urlsplit

from .deduplicate import deduplicate
from .exporters import export_excel
from .models import Buyer, Source
from .importers import import_buyers
from .normalize import classify_materials, normalize_company

MAX_BYTES = 5_000_000
KINDS = {"trade_records", "company_directory", "api"}


def https_url(value):
    if not isinstance(value, str):
        raise ValueError("URL must be text")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Source and website URLs must be HTTPS without credentials")
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Redirect refused; review and configure the authorized endpoint explicitly")


def fetch_json(url):
    """One bounded request; no retries, link traversal, cookies or login bypass."""
    request = urllib.request.Request(https_url(url), headers={
        "User-Agent": "TradeBuyerIntelligence/1.1 (authorized API client)",
        "Accept": "application/json"})
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(request, timeout=30) as response:
        if response.headers.get_content_type() != "application/json":
            raise ValueError("Endpoint did not return application/json")
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Response exceeds 5 MB limit; use a smaller authorized query")
    return json.loads(data)


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError("Source configuration must be an object")
    for name in ("name", "endpoint", "terms_url", "permission_basis", "kind"):
        if not isinstance(config.get(name), str) or not config[name].strip():
            raise ValueError(f"Source requires {name}")
    https_url(config["endpoint"])
    https_url(config["terms_url"])
    if config.get("automated_access_permitted") is not True:
        raise ValueError("Explicit automated-access authorization is required")
    if config["kind"] not in KINDS or config.get("authorization") not in {"public_license", "permission_granted"}:
        raise ValueError("Invalid source kind or authorization")


def parse_record(record, config, verified_on):
    if not isinstance(record, dict):
        raise ValueError("Record must be an object")
    for key in ("company_name", "country", "products_purchased", "source_url", "record_date"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            raise ValueError(f"Record requires {key}")
    from datetime import date
    date.fromisoformat(record["record_date"])
    if record["record_date"] > verified_on:
        raise ValueError("Future-dated buyer evidence")
    if record.get("business_email") and record.get("email_public") is not True:
        raise ValueError("Email requires explicit public business-contact attestation")
    email = record.get("business_email", "")
    if not isinstance(email, str) or (email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)):
        raise ValueError("Invalid business email")
    website = record.get("website", "")
    if website:
        https_url(website)
    name = normalize_company(record["company_name"])
    materials = classify_materials(record["products_purchased"])
    if not name or materials == {"unclassified"}:
        raise ValueError("No normalized company name or target product purchase evidence")
    if record.get("buyer_role") not in {"buyer", "importer", "lead"}:
        raise ValueError("Explicit buyer/importer/lead role required; sellers are excluded")
    evidence = record.get("buyer_evidence", "")
    if not isinstance(evidence, str):
        raise ValueError("Buyer evidence must be text")
    documented = record["buyer_role"] in {"buyer", "importer"} and bool(evidence.strip())
    status = "documented_buyer_activity" if documented else "unconfirmed_lead"
    source = Source(config["name"], https_url(record["source_url"]), verified_on,
                    config["authorization"], "real", verified_on,
                    record["products_purchased"] if documented else "", email, website, evidence,
                    record["record_date"], config["terms_url"], config["permission_basis"], config["kind"], status)
    return Buyer(record["company_name"].strip(), name, record["country"].strip(), materials, [source])


def discover(config, fetcher=fetch_json):
    validate_config(config)
    payload = fetcher(config["endpoint"])
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        raise ValueError("API response requires a records array")
    # Never silently claim completeness for a truncated/paginated response.
    if payload.get("next") or payload.get("next_page"):
        raise ValueError("Paginated response: configure an authorized single-page query or export")
    verified_on = datetime.now(timezone.utc).date().isoformat()
    buyers, rejected = [], 0
    for index, record in enumerate(payload["records"], 1):
        try:
            buyers.append(parse_record(record, config, verified_on))
        except (ValueError, TypeError) as error:
            rejected += 1
            logging.warning("Discovery record %d rejected: %s", index, error)
    return buyers, rejected


def main(argv=None):
    parser = argparse.ArgumentParser(description="Discover buyers from an explicitly authorized JSON API")
    parser.add_argument("--source-config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--records-file", type=Path, help="Authorized local JSON API export; no network request")
    parser.add_argument("--import-file", action="append", type=Path, default=[], help="Merge authorized CSV/XLSX input; repeatable")
    parser.add_argument("--log-file", type=Path, default=Path("output/discovery.log"))
    args = parser.parse_args(argv)
    try:
        if args.output.suffix.lower() != ".xlsx":
            raise ValueError("Output must be .xlsx")
        paths = [p.resolve() for p in (args.source_config, args.output, args.log_file, *args.import_file, *([args.records_file] if args.records_file else []))]
        if len(set(paths)) != len(paths):
            raise ValueError("Configuration, output and log paths must differ")
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(filename=args.log_file, level=logging.INFO, force=True,
                            format="%(asctime)s %(levelname)s %(message)s")
        config = json.loads(args.source_config.read_text(encoding="utf-8"))
        if args.records_file:
            payload = json.loads(args.records_file.read_text(encoding="utf-8"))
            records, rejected = discover(config, lambda _: payload)
        else:
            records, rejected = discover(config)
        for path in args.import_file:
            imported, invalid = import_buyers(path)
            records.extend(imported)
            rejected += invalid
        buyers, merged = deduplicate(records)
        if not buyers:
            raise ValueError(f"No evidence-backed buyers collected; {rejected} records rejected")
        export_excel(buyers, args.output)
        documented = sum(any(s.verification_status == "documented_buyer_activity" for s in b.sources) for b in buyers)
        print(f"Collected {len(buyers)} companies; documented buyer activity: {documented}; "
              f"unconfirmed leads: {len(buyers) - documented}; merged {merged}; rejected {rejected}. "
              "Retrieval date recorded; business identity/contact validity not independently verified.")
        return 2 if rejected else 0
    except Exception as error:
        logging.error("Discovery failed (%s)", type(error).__name__)
        # Avoid exposing signed endpoint URLs or provider credentials in errors.
        print("Discovery failed; check configuration, authorization and network access. "
              f"Error category: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
