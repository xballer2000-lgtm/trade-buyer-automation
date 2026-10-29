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
    sheet.append(["buyer_id", "company_name", "normalized_name", "country", "classification", "record_type", "source_count"])
    sources = book.create_sheet("Sources")
    sources.append(["buyer_id", "source_name", "source_url", "collected_on", "authorization", "record_type"])
    for index, buyer in enumerate(buyers, 1):
        sheet.append([index, safe_cell(buyer.company_name), safe_cell(buyer.normalized_name),
                      safe_cell(buyer.country), ";".join(sorted(buyer.materials)),
                      buyer.sources[0].record_type, len(buyer.sources)])
        for source in buyer.sources:
            sources.append([index, *[safe_cell(value) for value in
                           (source.name, source.url, source.collected_on, source.authorization, source.record_type)]])
    for tab in book:
        tab.freeze_panes = "A2"
        tab.auto_filter.ref = tab.dimensions
        for cell in tab[1]:
            cell.font = Font(bold=True)
        for column in tab.columns:
            tab.column_dimensions[column[0].column_letter].width = 26
    path.parent.mkdir(parents=True, exist_ok=True)
    book.save(path)
