#!/usr/bin/python
# 
import csv
import sys
import os
import argparse
from datetime import datetime
from columnar import columnar
#
# Default directory where gradebook CSV files are stored
DEFAULT_REPORT_DIR = "/var/lib/canvas-mgmt/reports/enrollments/"
#
# Columns that uniquely identify an enrollment
KEY_COLS = ["student sis", "course id", "section id", "term sis"]
#
# Columns to compare for changes
COMPARE_COLS = [
    "current score",
    "final score",
    "unposted current score",
    "unposted final score",
    "override score",
    "current grade",
    "final grade",
    "unposted current grade",
    "unposted final grade",
    "override grade",
]
#
def normalize_headers(headers: list[str]) -> dict[str, str]:
    """Return a mapping of lowercased-stripped header -> original header."""
    return {h.strip().lower(): h for h in headers}
#
def load_csv(filepath: str) -> tuple[list[str], dict[tuple, dict]]:
    """
    Load a CSV file.
    Returns (original_headers, rows_by_key) where rows_by_key maps
    the composite key tuple to the row dict.
    """
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            print(f"ERROR: Could not read headers from {filepath}")
            sys.exit(1)
        #
        norm = normalize_headers(list(reader.fieldnames))
        missing_keys = [k for k in KEY_COLS if k not in norm]
        if missing_keys:
            print(f"ERROR: {filepath} is missing key column(s): {missing_keys}")
            sys.exit(1)
        #
        rows_by_key: dict[tuple, dict] = {}
        duplicate_count = 0
        for row in reader:
            # Build a normalized version of the row keyed by lowercased col name
            norm_row = {k.strip().lower(): v.strip() if v else "" for k, v in row.items()}
            key = tuple(norm_row.get(k, "") for k in KEY_COLS)
            if key in rows_by_key:
                duplicate_count += 1
            rows_by_key[key] = norm_row
        #
        if duplicate_count:
            print(f"WARNING: {filepath} contains {duplicate_count} duplicate enrollment key(s). "
                  "Only the last occurrence is kept.")
        #
        return list(reader.fieldnames), rows_by_key
#
def compare(old_rows: dict, new_rows: dict) -> list[dict]:
    """
    Compare two row dicts keyed by enrollment tuple.
    Returns a list of change records.
    """
    changes = []
    all_keys = set(old_rows) | set(new_rows)
    #
    for key in sorted(all_keys):
        student_sis, course_id, section_id, term_sis = key
        row_ref = (old_rows if key in old_rows else new_rows)[key]
        base = {
            "student sis": student_sis,
            "course id": course_id,
            "course sis": row_ref.get("course sis", ""),
            "section id": section_id,
            "section sis": row_ref.get("section sis", ""),
            "term sis": term_sis,
        }
        #
        if key not in old_rows:
            changes.append({**base, "change type": "added", "field": "(enrollment)", "old value": "", "new value": ""})
            continue
        #
        if key not in new_rows:
            changes.append({**base, "change type": "removed", "field": "(enrollment)", "old value": "", "new value": ""})
            continue
        #
        old = old_rows[key]
        new = new_rows[key]
        for col in COMPARE_COLS:
            old_val = old.get(col, "")
            new_val = new.get(col, "")
            if old_val != new_val:
                changes.append({
                    **base,
                    "change type": "modified",
                    "field": col,
                    "old value": old_val,
                    "new value": new_val,
                })
    #
    return changes
#
def print_changes(changes: list[dict]) -> None:
    """Print a grid summary of changes to the terminal using columnar."""
    if not changes:
        print("\nNo changes detected between the two files.")
        return
    #
    print(f"\n  CHANGES DETECTED: {len(changes)} field change(s)\n")
    #
    headers = ["student sis", "course id", "course sis", "section id", "section sis", "term sis", "change type", "field", "old value", "new value"]
    data = [
        [
            c["student sis"],
            c["course id"],
            c["course sis"],
            c["section id"],
            c["section sis"],
            c["term sis"],
            c["change type"],
            c["field"],
            c["old value"],
            c["new value"],
        ]
        for c in changes
    ]
    #
    table = columnar(data, headers, no_borders=True)
    print(table)
#
def write_csv_report(changes: list[dict], output_path: str) -> None:
    """Write the changes to a CSV file."""
    fieldnames = [
        "student sis", "course id", "course sis", "section id", "section sis", "term sis",
        "change type", "field", "old value", "new value",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(changes)
    print(f"Report written to: {output_path}")
#
def main():
    parser = argparse.ArgumentParser(
        description="Compare two Canvas gradebook CSVs and report grade/score changes."
    )
    parser.add_argument("old_csv", nargs="?", default=None, help="Path to the older/baseline CSV file")
    parser.add_argument("new_csv", nargs="?", default=None, help="Path to the newer CSV file to compare against")
    parser.add_argument(
        "-o", "--output",
        help="Output CSV report path. Defaults to gradebook_changes_<timestamp>.csv in the same directory as new_csv.",
        default=None,
    )
    args = parser.parse_args()
    #
    if not args.old_csv:
        print()
        filename = input(f"  > Enter filename of the older/baseline CSV ({DEFAULT_REPORT_DIR}): ").strip()
        args.old_csv = os.path.join(DEFAULT_REPORT_DIR, filename)
        print()
    if not args.new_csv:
        print()
        filename = input(f"  > Enter filename of the newer CSV ({DEFAULT_REPORT_DIR}): ").strip()
        args.new_csv = os.path.join(DEFAULT_REPORT_DIR, filename)
        print()
    #
    if not os.path.isfile(args.old_csv):
        print(f"ERROR: File not found: {args.old_csv}")
        sys.exit(1)
    if not os.path.isfile(args.new_csv):
        print(f"ERROR: File not found: {args.new_csv}")
        sys.exit(1)
    #
    print(f"Loading old CSV: {args.old_csv}")
    _, old_rows = load_csv(args.old_csv)
    print(f"  {len(old_rows)} enrollment(s) loaded.")
    #
    print(f"Loading new CSV: {args.new_csv}")
    _, new_rows = load_csv(args.new_csv)
    print(f"  {len(new_rows)} enrollment(s) loaded.")
    #
    changes = compare(old_rows, new_rows)
    #
    print_changes(changes)
    #
    if args.output:
        output_path = args.output
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.dirname(os.path.abspath(args.new_csv))
        output_path = os.path.join(output_dir, f"gradebook_changes_{ts}.csv")
    #
    write_csv_report(changes, output_path)
#
if __name__ == "__main__":
    main()
