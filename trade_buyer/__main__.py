"""Command-line entry point."""
import argparse
import logging
from pathlib import Path

from .deduplicate import deduplicate
from .exporters import export_excel
from .importers import import_buyers


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Trade Buyer Intelligence System — authorized local data processing")
    parser.add_argument("inputs", nargs="+", type=Path, help="CSV or XLSX files")
    parser.add_argument("--output", required=True, type=Path, help="Destination .xlsx report")
    parser.add_argument("--allow-samples", action="store_true", help="Explicitly permit labeled synthetic fixtures")
    parser.add_argument("--log-file", type=Path, default=Path("output/errors.log"))
    args = parser.parse_args(argv)
    try:
        if args.output.suffix.lower() != ".xlsx":
            raise ValueError("Output must end in .xlsx")
        if args.output.resolve() in {path.resolve() for path in args.inputs}:
            raise ValueError("Output must not overwrite an input")
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        if args.log_file.resolve() in {p.resolve() for p in [*args.inputs, args.output]}:
            raise ValueError("Log file must differ from inputs and output")
        logging.basicConfig(filename=args.log_file, level=logging.INFO,
                            format="%(asctime)s %(levelname)s %(message)s", force=True)
        records, rejected = [], 0
        for path in args.inputs:
            imported, invalid = import_buyers(path, args.allow_samples)
            records.extend(imported)
            rejected += invalid
        if not records:
            raise ValueError("No valid records; inspect the error log")
        buyers, duplicates = deduplicate(records)
        export_excel(buyers, args.output)
        print(f"Exported {len(buyers)} buyers; merged {duplicates} duplicates; rejected {rejected} rows. Report: {args.output}")
        return 2 if rejected else 0
    except Exception as error:
        logging.error("Processing failed: %s", error)
        print(f"Error: {error}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
