# Trade Buyer Intelligence System

A Python 3.12 command-line application for organizing authorized, publicly available international aluminum scrap, copper scrap, and metal ingot buyer data. Imports local CSV and Excel files, normalizes company names, detects duplicates, classifies materials, preserves source provenance, and exports formatted Excel reports.

## Install

From the repository root, with Python 3.12 installed:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the sample

```sh
python -m trade_buyer sample_data/buyers.csv --allow-samples --output output/sample-report.xlsx
python -m trade_buyer --help
```

The included records are **synthetic software fixtures**, conspicuously labeled `SYNTHETIC SAMPLE`. They do not represent actual companies, buyers, contacts, or verified commercial interest. The example merges three input rows into two sample entities. Samples are rejected unless explicitly enabled.

Import one or several authorized datasets:

```sh
python -m trade_buyer authorized.csv authorized.xlsx --output output/buyers.xlsx --log-file output/errors.log
```

Only `.csv` (UTF-8, optional BOM) and `.xlsx` are supported. Excel imports use the active worksheet; put literal values in cells rather than formulas. Existing output reports are replaced; inputs cannot be overwritten. Exit statuses: `0` complete success, `2` report produced with rejected rows, `1` fatal failure (including no valid rows). Malformed headers fail the import. Row validation failures are logged with filename and row number and skipped. Fatal input failures prevent report generation. Logs append across runs.

## Input schema and authorization

The first row must contain unique column names, including all these required fields. Additional columns are accepted but not retained.

| Column | Meaning |
| --- | --- |
| `company_name` | Original company name |
| `country` | Country; use consistent spellings across inputs |
| `materials` | Material description, e.g. `aluminum scrap; copper scrap` |
| `source_name` | Name of the originating publication or authorized dataset |
| `source_url` | HTTP(S) evidence URL for real records; sample URN for fixtures |
| `collected_on` | ISO date, preferably `YYYY-MM-DD` |
| `authorization` | `public_license`, `permission_granted`, or `synthetic_sample` |
| `record_type` | `real` or `synthetic` |

Real records require a source URL and the operator's explicit assertion of a public license or granted permission. These fields document assertions, not independently verified permission or buyer status. Confirm that source terms and applicable privacy rules permit collection and reuse; retain supporting permission evidence outside this tool. Do not import private, restricted, or unlicensed data. Public visibility alone is not authorization.

The local import command makes **no web requests and performs no scraping**. The optional discovery command performs only explicitly authorized JSON API requests (see below). It cannot bypass access restrictions or determine site terms. Only import lawfully obtained files from authorized sources. No actual buyer records are supplied or invented. Source URLs are stored as evidence, not visited.

## Processing and output

- Unicode normalization, case folding, punctuation cleanup, and removal of common trailing English legal suffixes produce a search key; the original name remains available.
- Exact normalized name plus case-insensitive country plus record type determines a duplicate. Sources and material categories merge without losing distinct provenance. Country aliases and fuzzy matches are intentionally left for review. Distinct companies can share names, so review merged entities before commercial use.
- Explicit phrases identify `aluminum_scrap` (including aluminium), `copper_scrap`, and `metal_ingot`. Multiple labels are possible. Other descriptions receive `unclassified`. Classification describes supplied material text, not verified purchasing activity.
- Reports contain `Buyers` and `Sources` sheets joined by a report-local buyer ID, with filters, frozen headers, and source counts. All distinct source attestations are retained. Formula-like imported text is escaped to prevent spreadsheet formula execution.
- Export reports are for review; they are not input templates. Use the schema above for subsequent imports. Preserve original files separately for audit and later reprocessing.

## Architecture

`trade_buyer/models.py` defines records and provenance; `importers.py` validates local files; `normalize.py` normalizes names and classifies materials; `deduplicate.py` merges entities; `exporters.py` creates reports; `__main__.py` orchestrates the CLI and logging. Processing is in memory, appropriate for modest research datasets rather than bulk national registries. No database, server, API keys, or external services are required.

## Tests

```sh
python -m unittest discover -s tests -v
```

Tests use temporary files and synthetic fixtures, covering normalization, classification, deduplication, provenance retention, authorization rejection, CSV/Excel ingestion, safe Excel exports, and CLI success/error/partial-success behavior. They do not contact websites.

## Phase 2: authorized buyer discovery

See [discovery setup and source contract](docs/discovery.md) for the JSON API connector, authorized local JSON exports, CSV/Excel integration, public business contacts, source evidence, and documented-activity versus unconfirmed-lead labels.

```sh
python -m trade_buyer.discovery --help
```

**Live result: 0 genuine buyers collected, 0 independently verified buyers.** Candidate source documentation was blocked by the environment network policy. No live provider is enabled or claimed to work; this release completes the import/integration framework pending an accessible, permitted source. Test fixtures are not real buyer results.
