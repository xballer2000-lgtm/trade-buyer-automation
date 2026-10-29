"""Excel reports with full provenance and spreadsheet formula protection."""
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font
from .models import Buyer


def safe_cell(value: str) -> str:
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def export_excel(buyers: list[Buyer], path: Path) -> None:
    book = Workbook()
    sheet = book.active
    sheet.title = "Buyers"
    sheet.append(["buyer_id", "company_name", "normalized_name", "country", "classification", "record_type", "source_count", "products_purchased", "business_emails", "websites", "verified_on", "verification_status"])
    sources = book.create_sheet("Sources")
    sources.append(["buyer_id", "source_name", "source_url", "collected_on", "authorization", "record_type", "verified_on", "products_purchased", "business_email", "website", "buyer_evidence", "record_date", "terms_url", "permission_basis", "source_kind", "verification_status"])
    for index, buyer in enumerate(buyers, 1):
        sheet.append([index, safe_cell(buyer.company_name), safe_cell(buyer.normalized_name),
                      safe_cell(buyer.country), ";".join(sorted(buyer.materials)),
                      buyer.sources[0].record_type, len(buyer.sources), *[safe_cell("; ".join(sorted({getattr(source, field) for source in buyer.sources if getattr(source, field)}))) for field in ("products_purchased", "business_email", "website", "verified_on")],
                      "documented_buyer_activity" if any(s.verification_status == "documented_buyer_activity" for s in buyer.sources) else "unconfirmed_lead"])
        for source in buyer.sources:
            sources.append([index, *[safe_cell(value) for value in
                           (source.name, source.url, source.collected_on, source.authorization, source.record_type, source.verified_on, source.products_purchased, source.business_email, source.website, source.buyer_evidence, source.record_date, source.terms_url, source.permission_basis, source.source_kind, source.verification_status)]])
    for tab in book:
        tab.freeze_panes = "A2"
        tab.auto_filter.ref = tab.dimensions
        for cell in tab[1]:
            cell.font = Font(bold=True)
        for column in tab.columns:
            tab.column_dimensions[column[0].column_letter].width = 26
    path.parent.mkdir(parents=True, exist_ok=True)
    book.save(path)
