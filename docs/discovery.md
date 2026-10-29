# Authorized discovery integrations

## Current live collection result

**Genuine buyers collected: 0. Independently verified buyers: 0.**

During development, documentation requests to `www.trade.gov`, `ised-isde.canada.ca`, and `www.importyeti.com` were denied by the environment's HTTP proxy (403). These are candidate documentation destinations, not validated buyer sources or enabled connectors. No restrictions were bypassed, and no source terms, datasets, contacts, or buyer activity could be verified from them. ImportYeti is not assumed to offer free API access. There is no ready-to-use live provider in this release. A permitted source must be selected and its schema mapped before live discovery can collect buyers. No credentials or paid subscription are required for local imports.

This release supplies the integration framework requested when no permitted live source is available. Tests are offline fixtures and never count toward real buyer totals.

## Commands

```sh
python -m trade_buyer.discovery --source-config /path/to/source.json --output output/discovered.xlsx
# Authorized JSON exports can be processed without network access:
python -m trade_buyer.discovery --source-config /path/to/source.json --records-file /path/to/export.json --import-file /path/to/authorized.csv --output output/merged.xlsx
```

`--import-file` is repeatable and accepts the existing CSV/XLSX import schema. It uses the same company normalization, exact deduplication and material classification as discovery. Samples are not allowed in the discovery command. Exit statuses match the existing CLI (0 success, 2 rejected records, 1 fatal failure/no records). Existing output files are replaced. Logs contain record indexes and validation reasons, not API bodies or contact data. Fatal errors are logged by category to avoid leaking credentials in endpoint URLs.

## Source permission configuration

Create a configuration **only after checking the source's license/terms and automated-access permission**. This illustrative configuration is intentionally disabled and points to a reserved invalid domain; it is not a functioning provider:

```json
{
  "name": "REPLACE with authorized source name",
  "kind": "trade_records",
  "endpoint": "https://example.invalid/documented-api",
  "terms_url": "https://example.invalid/terms",
  "permission_basis": "REPLACE with applicable license or explicit permission reference",
  "authorization": "public_license",
  "automated_access_permitted": false
}
```

Allowed kinds are `trade_records`, `company_directory`, `api`; authorization is `public_license` or `permission_granted`. Set automated access true only when supported by reviewed terms. This is an operator attestation, not an automatic legal or license check. The program never retrieves terms pages or assumes robots.txt grants a license. Configure network access to the selected API's exact hostname through environment settings only after source selection. A proxy denial must be resolved through supported settings; do not change routing to bypass it.

## Provider response contract

A source adapter or authorized export must return a JSON object with `records` containing objects with:

| Field | Requirement |
| --- | --- |
| `company_name`, `country` | Required, nonempty source values |
| `products_purchased` | Required target-product description; for leads this represents interest only and is not exported as documented purchases |
| `source_url` | Required HTTPS record evidence URL |
| `record_date` | Required ISO source-record date, not in the future |
| `buyer_role` | `buyer`, `importer`, or `lead`; sellers excluded |
| `buyer_evidence` | Source quotation or transaction reference supporting purchasing; optional for unconfirmed leads |
| `business_email` | Optional explicitly listed public business contact; never guessed |
| `email_public` | Must be boolean true if an email is supplied |
| `website` | Optional HTTPS business website supplied by the source |

Provider adapters must faithfully map source fields, check applicable permissions and determine whether an email is a public business contact. The software validates syntax and required attestations; it does not verify mailbox delivery, company identity, truthfulness of an upstream record, or permission automatically. Missing contacts remain blank. It does not crawl company sites or harvest additional emails.

`documented_buyer_activity` requires a buyer/importer role and nonempty source evidence. Other accepted rows are `unconfirmed_lead`. A directory listing by itself is not buyer verification. The status is an evidence-presence label, not an independent fact-check. `verified_on` records the UTC ingestion/retrieval date, not the date of independent company verification. `record_date` retains the historical evidence date. Historical purchases do not establish current demand. Legacy CSV/Excel imports remain unconfirmed even if an input column asserts a verified status.

Reports expose status, products, emails, websites, dates, and detailed provenance in the existing Buyers and Sources sheets. Merging preserves source-level contact/evidence relationships. The company summary is documented if any source has documented activity; other source statuses remain visible.

## Provider extension and limits

`discover(config, fetcher=...)` separates transport/provider adapters from validation, merging and export. An adapter can transform a documented open API or future licensed API response into this contract. It must not generate missing buyer facts. Test adapters with fixtures labeled as tests, and separately validate live access before claiming any real collection.

The built-in transport performs a single HTTPS JSON GET with TLS verification, a named user agent, a 30-second timeout and a 5 MB response limit. Redirects, HTML responses and declared pagination are refused. There are no retries after rate limits/authentication failures and no automatic URL traversal. Use documented single-page queries or authorized exports; pagination/authentication for a particular provider must be implemented to its published rules. No API credentials should be placed in source control or CLI arguments. The initial transport has no provider-specific authentication flow.

Optional CSV/XLSX columns `verified_on`, `products_purchased`, `business_email`, `website`, `buyer_evidence`, `record_date`, `terms_url`, `permission_basis`, and `source_kind` preserve supplied provenance. An imported email also requires `email_public=true`. Unknown columns continue to be ignored. Existing sample and basic import commands remain compatible.
