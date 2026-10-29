#!/usr/bin/env python3
"""Compare two independently generated reports, without rerunning physics."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reports.validate_report import sha, verify_files


def compare(reference, rebuild, output):
    for directory in (reference, rebuild, output.parent):
        if not directory.is_relative_to(ROOT):
            raise ValueError("Comparison paths must remain in this project")
    left = verify_files(reference)
    right = verify_files(rebuild)
    if left != right:
        raise ValueError("Independent report input audits differ")
    names = [
        "HgCdTe_Engineering_Assessment.pdf",
        "numerics.tex",
        "report_inputs.json",
        "verification_matrix.json",
    ] + ["figures/" + name for name in sorted(left["figures"])]
    records = {}
    for name in names:
        original = sha(reference / name)
        reproduced = sha(rebuild / name)
        if original != reproduced:
            raise ValueError("Independent rebuild differs: " + name)
        records[name] = {"sha256": original, "byte_identical": True}
    for directory in (reference, rebuild):
        validation = json.loads((directory / "report_validation.json").read_text())
        if not validation["passed"] or validation["pdf_sha256"] != records[names[0]]["sha256"]:
            raise ValueError("Missing or stale PDF validation")
    result = {
        "passed": True,
        "reference": str(reference.relative_to(ROOT)),
        "independent_rebuild": str(rebuild.relative_to(ROOT)),
        "baseline_archive_commit": left["integrity"]["baseline_commit"],
        "figure_count": len(left["figures"]),
        "files": records,
        "simulation_executed": False,
        "full_g3b_qualified": False,
    }
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"PASS: byte-identical PDF, {len(left['figures'])} figures, tables and input audit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=ROOT / "reports/generated")
    parser.add_argument("--rebuild", type=Path, default=ROOT / "outputs/report-reproduced")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/generated/reproducibility_check.json")
    args = parser.parse_args()
    compare(args.reference.resolve(), args.rebuild.resolve(), args.output.resolve())
