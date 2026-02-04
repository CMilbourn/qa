#!/usr/bin/env python3
"""
Batch convert protocol-style PDFs into a full parameter table.

Outputs per PDF:
- <input_stem>_ALL_PARAMS.xlsx
- <input_stem>_ALL_PARAMS.csv

Features:
- First column: Scan Run # (1..N)
- Every encountered parameter becomes a column
- Missing values filled with "na"
- Protocol name extracted from the page header (handles reversed-title artifact)
- Includes a Metadata sheet in XLSX with the original "Protocol: ..." header line (when found)

Requirements: 
pip install pdfplumber pandas openpyxl
Run one file:
python protocol_pdf_to_table.py adult_head_Sweet_20260126_dev_20260126142121171_13.pdf --outdir out
Run multiple files in a directory:
python protocol_pdf_to_table.py ./pdfs --outdir out

"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import pandas as pd
import pdfplumber


# ---- Helpers for parsing ----

def is_section_header(s: str) -> bool:
    """Heuristic for all-caps section headers like 'IMAGING PARAMETERS'."""
    s = s.strip()
    if not s or len(s) < 3:
        return False
    return bool(re.fullmatch(r"[A-Z0-9#/() \-]+", s)) and any(c.isalpha() for c in s)


def reverse_str(s: str) -> str:
    return s[::-1]


def extract_protocol_header_and_lines(page) -> Tuple[Optional[str], Optional[str], List[str]]:
    """
    Returns:
      protocol_name (best effort)
      protocol_header_line like 'Protocol: adult_head_...' (if present)
      page lines
    """
    txt = page.extract_text() or ""
    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
    if not lines:
        return None, None, []

    protocol_header = None
    for ln in lines:
        if ln.startswith("Protocol:"):
            protocol_header = ln
            break

    # Find protocol name in the "title area" after Protocol: and before section headers.
    protocol_name = None
    if protocol_header:
        try:
            pidx = lines.index(protocol_header)
        except ValueError:
            pidx = None

        if pidx is not None:
            title_raw: List[str] = []
            for ln in lines[pidx + 1:]:
                # stop when we hit section header area
                if "IMAGING PARAMETERS" in ln or "SCAN TIMING" in ln or ln in ("SCAN RANGE", "ACQ TIMING"):
                    break
                if is_section_header(ln):
                    break
                title_raw.append(ln)

            # Many of these PDFs have title lines extracted with characters reversed (e.g. "rezilacoL").
            # Also the title line appears duplicated around a hyphen: <title> - <title>
            if title_raw:
                # remove a standalone dash and de-duplicate halves if they match
                if "-" in title_raw:
                    dash = title_raw.index("-")
                    left = [x for x in title_raw[:dash] if x != "-"]
                    right = [x for x in title_raw[dash + 1:] if x != "-"]
                    if left and right and left == right:
                        title_raw = left
                    else:
                        title_raw = [x for x in title_raw if x != "-"]

                # reverse each line's characters and reverse the line order
                candidate = " ".join(reversed([reverse_str(x) for x in title_raw])).strip()
                candidate = re.sub(r"\s+", " ", candidate)

                # If that produced something reasonable, use it.
                if len(candidate) >= 3:
                    protocol_name = candidate

    return protocol_name, protocol_header, lines


def split_line_into_pairs(line: str, known_keys: List[str]) -> List[Tuple[str, str]]:
    """
    Some lines contain multiple key/value pairs, e.g.:
      "Imaging Mode 2D TE 80.0"
    We locate known keys in the line and slice values between them.
    """
    pairs: List[Tuple[str, str]] = []
    matches = []

    for k in known_keys:
        for m in re.finditer(r"\b" + re.escape(k) + r"\b", line):
            matches.append((m.start(), m.end(), k))

    if not matches:
        return pairs

    # pick longest key per start position
    matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    filtered = []
    used_starts = set()
    for s, e, k in matches:
        if s in used_starts:
            continue
        used_starts.add(s)
        filtered.append((s, e, k))

    filtered.sort(key=lambda x: x[0])

    for idx, (s, e, k) in enumerate(filtered):
        end = filtered[idx + 1][0] if idx + 1 < len(filtered) else len(line)
        chunk = line[s:end].strip()
        val = chunk[len(k):].strip()
        if val:
            pairs.append((k, val))

    return pairs


def parse_protocol_pdf(pdf_path: Path) -> Tuple[pd.DataFrame, str]:
    """
    Parse a protocol PDF into a DataFrame with:
      - Scan Run #
      - Protocol Name
      - all parameters as columns
      - missing -> 'na'

    Returns df, protocol_header_string (if found else empty)
    """

    # Keys we expect in these PDFs. Add more if your PDFs contain extra fields.
    known_keys = sorted({
        # Headings / common params
        "Imaging Mode", "Pulse Sequence", "Imaging Options", "PSD Name",
        "Phase", "HyperBand Slice", "IDEAL", "FOV", "Slice Thickness", "Slice Spacing",
        "Overlap Locations", "Number of Slices", "Location per Slab",
        "Freq", "Phase FOV", "Freq DIR", "Fat Shift DIR", "NEX",
        "Auto Shim", "Phase Correction", "RF Drive Mode", "Excitation Mode",
        "Flip Angle", "TE", "TR", "TI", "Number of Echoes", "Number of Shots",
        "Receiver Bandwidth", "Recovery Time",
        "Filter Choice",
        "Slice Order", "View Order",
        "Slice per Location", "Phase Acquisition Order",
        "Delay after Acquisition", "Delay after Acquisition without AV",
        "Trigger Delay without AV",
        "Tag Type", "Fat/Water Saturation",
        "PSD Trigger", "Initial State Control",
        "# of Repetitions REST", "# of Repetitions ACTIVE", "# of Dummy Acquisition",
        "Brain Wave Real Time", "Paradigm String", "Paradigm UID",
        "Protocol Notes",
        # Other toggles
        "Pause On/Off", "Auto Subtract", "Auto SCIC",
        "Recon All Images On", "Recon All Images",
        "Contrast Yes/No",
        # User CVs (common in your PDF)
        "User CV0", "User CV1", "User CV6", "User CV10", "User CV11", "User CV Mask2",
        # Misc sometimes present
        "# Synthetic b-values", "Synthetic b-value", "Multi b-values", "Multi NEX Values",
        "Pause After Navigator Prescan", "Pause After Navigator",
    }, key=len, reverse=True)

    protocol_data: Dict[str, Dict[str, str]] = {}
    protocol_order: List[str] = []
    protocol_header_line = ""

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            pname, header_line, lines = extract_protocol_header_and_lines(page)
            if header_line and not protocol_header_line:
                protocol_header_line = header_line

            if not pname:
                # If protocol name extraction fails, skip this page
                continue

            if pname not in protocol_data:
                protocol_data[pname] = {}
                protocol_order.append(pname)

            for ln in lines:
                ln = ln.strip()
                if not ln:
                    continue
                if ln.startswith("Protocol:") or ln.startswith("Page ") or ln.startswith("Property of"):
                    continue
                if is_section_header(ln):
                    continue

                # Multi-line notes: keep appending if repeated
                for k, v in split_line_into_pairs(ln, known_keys):
                    if k == "Protocol Notes":
                        prev = protocol_data[pname].get(k, "")
                        protocol_data[pname][k] = (prev + " " + v).strip() if prev else v
                    else:
                        protocol_data[pname][k] = v

    # Build dataframe
    all_cols = set()
    for pname in protocol_order:
        all_cols.update(protocol_data[pname].keys())

    cols = ["Scan Run #", "Protocol Name"] + sorted(all_cols)

    rows = []
    for idx, pname in enumerate(protocol_order, start=1):
        row = {"Scan Run #": idx, "Protocol Name": pname}
        for c in cols[2:]:
            row[c] = protocol_data[pname].get(c, "na")
        rows.append(row)

    df = pd.DataFrame(rows, columns=cols).fillna("na")

    return df, protocol_header_line or ""


def write_outputs(df: pd.DataFrame, protocol_header: str, out_base: Path) -> Tuple[Path, Path]:
    xlsx_out = out_base.with_name(out_base.name + "_ALL_PARAMS.xlsx")
    csv_out  = out_base.with_name(out_base.name + "_ALL_PARAMS.csv")

    with pd.ExcelWriter(xlsx_out, engine="openpyxl") as writer:
        # Main sheet
        df.to_excel(writer, index=False, sheet_name=out_base.name[:31] or "Sheet1")

        # Metadata sheet with original header line
        meta = pd.DataFrame({
            "Field": ["Original PDF Header"],
            "Value": [protocol_header if protocol_header else "na"]
        })
        meta.to_excel(writer, index=False, sheet_name="Metadata")

    df.to_csv(csv_out, index=False)
    return xlsx_out, csv_out


# ---- CLI ----

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "inputs",
        nargs="+",
        help="PDF file(s) or a directory containing PDFs"
    )
    ap.add_argument(
        "--outdir",
        default="out",
        help="Output directory (default: ./out)"
    )
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Expand inputs into a list of PDFs
    pdfs: List[Path] = []
    for inp in args.inputs:
        p = Path(inp)
        if p.is_dir():
            pdfs.extend(sorted(p.glob("*.pdf")))
        else:
            pdfs.append(p)

    if not pdfs:
        raise SystemExit("No PDFs found.")

    for pdf_path in pdfs:
        df, header = parse_protocol_pdf(pdf_path)
        if df.empty:
            print(f"[WARN] No protocols parsed from: {pdf_path.name}")
            continue

        out_base = outdir / pdf_path.stem
        xlsx_out, csv_out = write_outputs(df, header, out_base)
        print(f"[OK] {pdf_path.name}")
        print(f"     -> {xlsx_out}")
        print(f"     -> {csv_out}")


if __name__ == "__main__":
    main()
