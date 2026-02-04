#!/usr/bin/env python3
#examcard_pdf2excel_V3.py
#20260126
"""


Requirements: 
pip install pdfplumber pandas openpyxl
e.g. /opt/homebrew/bin/python3 -m pip install --break-system-packages pdfplumber pandas openpyxl
Run one file:
python protocol_pdf_to_table.py adult_head_Sweet_20260126_dev_20260126142121171_13.pdf --outdir out
Run multiple files in a directory:
python protocol_pdf_to_table.py ./pdfs --outdir out

Batch convert GE-style protocol PDFs into a full parameter table.

Outputs per PDF:
- <input_stem>_ALL_PARAMS.xlsx
- <input_stem>_ALL_PARAMS.csv

Features:
- First column: Scan Run # (1..N)
- Every encountered parameter becomes a column
- Missing values filled with "na" (never blank)
- Protocol name extracted from the page header
  * Works for PDFs where extracted titles are normal AND where titles are character-reversed.
- Includes a Metadata sheet in XLSX with the original "Protocol: ..." header line (when found)

Designed to handle:
- fMRI-style protocol PDFs (some with reversed title extraction artifacts)
- MRS-style protocol PDFs (Press/Steam CSI etc., normal titles)
- ASL/pCASL/eASL PDFs (Post Label Delay, eASL-specific keys)
- Vascular/cine/TOF keys and DTI/diffusion keys seen in related protocol exports
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import pandas as pd
import pdfplumber


# -------------------------
# Parsing helpers
# -------------------------

def is_section_header(s: str) -> bool:
    """Heuristic for all-caps section headers like 'IMAGING PARAMETERS'."""
    s = s.strip()
    if not s or len(s) < 3:
        return False
    return bool(re.fullmatch(r"[A-Z0-9#/() \-]+", s)) and any(c.isalpha() for c in s)


def reverse_str(s: str) -> str:
    return s[::-1]


def collapse_title_lines(title_lines: List[str]) -> List[str]:
    """
    Title blocks often look like:
      <title> - <title>
    sometimes split across multiple lines. This collapses the duplication.
    """
    title_lines = [x for x in title_lines if x and x != "-"]
    if "-" in title_lines:
        dash = title_lines.index("-")
        left = [x for x in title_lines[:dash] if x != "-"]
        right = [x for x in title_lines[dash + 1:] if x != "-"]
        if left and right and left == right:
            return left
        return [x for x in title_lines if x != "-"]
    return title_lines


def fix_protocol_name_typos(s: str) -> str:
    """
    Fix common OCR/extraction typos and reversed text in protocol names.
    """
    # Fix common reversals and typos (case-insensitive where needed)
    fixes = {
        "CIMPSipe": "epiSPMIC",     # Reversed/mangled epiSPMIC
        "3BM": "MB3",               # Reversed multiband
        "1BM": "MB1",               # Reversed multiband 1
        "2BM": "MB2",               # Reversed multiband 2
        "NOMIHS": "NOSHIM",         # Reversed shim off
        "FFOMIHS": "SHIMOFF",       # Reversed shim off (variant)
        "tset": "test",             # Reversed test
        "tsop": "post",             # Reversed post
        "kcehcgnimit": "timingcheck",  # Reversed timingcheck
    }
    
    for typo, correct in fixes.items():
        s = s.replace(typo, correct)
    
    # Fix reversed dimension notation: mm2 -> 2mm, mm3 -> 3mm, mm5.2 -> 2.5mm
    s = re.sub(r'mm(\d+)\.(\d+)', lambda m: f"{m.group(2)}.{m.group(1)}mm", s)  # mm5.2 -> 2.5mm
    s = re.sub(r'mm(\d+)(?![0-9.])', lambda m: f"{m.group(1)}mm", s)  # mm2 -> 2mm, mm3 -> 3mm
    
    return s


def title_plausibility_score(s: str) -> int:
    """
    Score how plausible a protocol title string is.
    Higher score => more likely the "correct" orientation.
    """
    if not s:
        return -10

    score = 0
    s_stripped = s.strip()

    # Titles often start with a digit (e.g., "3-Plane") or uppercase (e.g., "fMRI", "Ax_", "3D", "Press").
    if s_stripped and s_stripped[0].isdigit():
        score += 4
    if s_stripped and s_stripped[0].isupper():
        score += 3

    # Common tokens in these protocols (boost if present).
    tokens = [
        "Localizer", "fMRI", "Ax_", "3D", "SAG", "T1", "MP-RAGE",
        "Press", "Steam", "CSI", "TR", "slices", "mmiso", "TI",
        "ASL", "pCASL", "eASL"
    ]
    for t in tokens:
        if t in s:
            score += 2

    # Reversed-looking artifacts often include obviously reversed substrings.
    reversed_artifacts = ["rezilacoL", "osimm", "IRMf"]
    for bad in reversed_artifacts:
        if bad in s:
            score -= 4

    # Penalize if it looks mostly lowercase letters at the start (often reversed output starts like "rezilacoL")
    if len(s_stripped) >= 6 and s_stripped[:6].islower():
        score -= 2

    return score


def extract_protocol_name_and_lines(page) -> Tuple[Optional[str], Optional[str], List[str]]:
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

    protocol_name = None
    if protocol_header:
        try:
            pidx = lines.index(protocol_header)
        except ValueError:
            pidx = None

        if pidx is not None:
            title_raw: List[str] = []
            for ln in lines[pidx + 1:]:
                # Stop when we hit section header area
                if "IMAGING PARAMETERS" in ln or "SCAN TIMING" in ln or ln in ("SCAN RANGE", "ACQ TIMING"):
                    break
                if is_section_header(ln):
                    break
                title_raw.append(ln)

            title_raw = collapse_title_lines(title_raw)

            if title_raw:
                # Candidate A: normal orientation
                cand_normal = " ".join(title_raw).strip()
                cand_normal = re.sub(r"\s+", " ", cand_normal)

                # Candidate B: reversed-character fix
                cand_reversed = " ".join(reversed([reverse_str(x) for x in title_raw])).strip()
                cand_reversed = re.sub(r"\s+", " ", cand_reversed)

                if title_plausibility_score(cand_reversed) > title_plausibility_score(cand_normal):
                    protocol_name = cand_reversed
                else:
                    protocol_name = cand_normal

    return protocol_name, protocol_header, lines


def split_line_into_pairs(line: str, known_keys: List[str]) -> List[Tuple[str, str]]:
    """
    Many lines contain multiple key/value pairs, e.g.:
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

    # Choose longest key per start position
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


# -------------------------
# Main parse function
# -------------------------

def parse_protocol_pdf(pdf_path: Path) -> Tuple[pd.DataFrame, str]:
    """
    Parse a protocol PDF into a DataFrame with:
      - Scan Run #
      - Protocol Name
      - all parameters as columns
      - missing -> 'na'

    Returns: (df, protocol_header_string)
    """

    # Combined known_keys: fMRI + MRS + ASL/pCASL/eASL + vascular/cine/TOF + diffusion/DTI additions
    known_keys = sorted({
        # ---- Core imaging parameters ----
        "Imaging Mode", "Pulse Sequence", "Imaging Options", "PSD Name",
        "Phase", "Slice", "HyperSense", "HyperBand Slice", "IDEAL",
        "FOV", "Slice Thickness", "Slice Spacing", "Overlap Locations",
        "Number of Slices", "Location per Slab", "Location per Acquisition",

        # ---- Acquisition timing ----
        "Freq", "Phase Encoding", "Phase", "Phase FOV", "Freq DIR", "Fat Shift DIR", "NEX",
        "# of Acq. Before Pause", "# of Acquisition",
        "Auto Shim", "Phase Correction",
        "RF Drive Mode", "Excitation Mode",

        # ---- Scan timing ----
        "Flip Angle", "TE", "TR", "TI",
        "Number of Echoes", "Number of Shots",
        "Receiver Bandwidth", "Recovery Time",

        # ---- Enhance / recon / diffusion / contrast ----
        "Filter Choice",
        "Recon All Images On", "Recon All Images",
        "Multi b-values", "Multi NEX Values", "# Synthetic b-values", "Synthetic b-value",
        "Contrast Yes/No",

        # ---- fMRI & tricks ----
        "PSD Trigger",
        "Brain Wave Real Time", "Paradigm String", "Paradigm UID",
        "Initial State Control",
        "# of Repetitions REST", "# of Repetitions ACTIVE",
        "# of Dummy Acquisition",
        "Pause On/Off", "Auto Subtract", "Auto SCIC",

        # ---- SAT ----
        "Tag Type", "Fat/Water Saturation",

        # ---- Multi-phase ----
        "Slice per Location", "Phase Acquisition Order",
        "Delay after Acquisition", "Delay after Acquisition without AV",
        "Trigger Delay without AV",
        "Mask Phase", "Mask Pause", "Preserve", "Seperate Series",

        # ---- ASSET / acceleration (MRS/others) ----
        "Acceleration Factor",
        "Slice Acceleration Factor", "Phase Acceleration Factor",

        # ---- Gating/trigger / ASL-specific ----
        "Auto Trigger Type",
        "Post Label Delay",              # pCASL/ASL baseline
        "Delay Time after Mask",         # eASL
        "Phase Image",                   # eASL

        # ---- Vascular / cine / TOF ----
        "# of Collapse Images",
        "# of Projection Images",
        "Flow Analysis",
        "Additional Flow Images",
        "Flow Recon Type",
        "Velocity Encoding",
        "Trigger Type",
        "# of Cardiac Phases to Reconstruct",

        # ---- Diffusion / DTI extras ----
        "Optimized TE",
        "Diffusion Directions",
        "Diffusion Directions Tensor",
        "Number of Diffusion Directions",
        "Number of T2 Images",
        "Dual Spin Echo",
        "Diffusion Tenser Processing Output",  # spelling as seen in some exports
        "NEX For T2",
        "Real Time Field Adjustment",

        # ---- Min fields ----
        "TR Minimum",
        "TE Minimum",
        "TE Min Full",

        # ---- User CVs (expand as needed) ----
        "User CV0", "User CV1", "User CV3", "User CV4", "User CV6",
        "User CV10", "User CV11", "User CV18",
        "User CV Mask2",

        # ---- Notes ----
        "Protocol Notes",
    }, key=len, reverse=True)

    protocol_data: Dict[str, Dict[str, str]] = {}
    protocol_order: List[str] = []
    protocol_header_line = ""

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            pname, header_line, lines = extract_protocol_name_and_lines(page)
            if header_line and not protocol_header_line:
                protocol_header_line = header_line

            if not pname:
                continue
            
            # Apply typo fixes to protocol name
            pname = fix_protocol_name_typos(pname)

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

                # Collect key/value pairs (supports multiple pairs per line)
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
    """
    Write:
      - <out_base>_ALL_PARAMS.xlsx
      - <out_base>_ALL_PARAMS.csv

    Sheet name must be <= 31 chars in Excel; we use truncated stem.
    """
    xlsx_out = out_base.with_name(out_base.name + "_ALL_PARAMS.xlsx")
    csv_out = out_base.with_name(out_base.name + "_ALL_PARAMS.csv")

    sheet_name = (out_base.name[:31] or "Sheet1")

    with pd.ExcelWriter(xlsx_out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        meta = pd.DataFrame({
            "Field": ["Original PDF Header"],
            "Value": [protocol_header if protocol_header else "na"]
        })
        meta.to_excel(writer, index=False, sheet_name="Metadata")

    df.to_csv(csv_out, index=False)
    return xlsx_out, csv_out


# -------------------------
# CLI
# -------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", help="PDF file(s) or a directory containing PDFs")
    ap.add_argument("--outdir", default="out", help="Output directory (default: ./out)")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

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
