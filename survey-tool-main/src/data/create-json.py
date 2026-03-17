#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
create-json.py
Convert your thesis-style XLSX (final lr.xlsx) into survey-data.json + survey-config.json

Improvements over your current version:
1) Distinguish TRUE empty vs "Not specified":
   - TRUE empty (blank / NaN) becomes "" for String or [] for MultiSelect
   - "not specified" (and similar unknown tokens) becomes explicit value:
       - String: "Not specified"
       - MultiSelect: ["Not specified"]
2) Auto-populate filter value pools in survey-config.json (like the original CSV script did),
   so the UI will NOT look sparse even if the frontend doesn't infer pools.
3) Derivation corpus includes Name + Abstract (+ optional keywords), increasing hit rates.
4) Fix the "Projected,Planar" comma-tag bug (no comma inside a single tag).
5) Keep your existing field lists/grouping/show lists as-is (so project usually needs no other changes).

Usage:
  python create-json.py -i "/path/to/final lr.xlsx" -o "./src/data" --sheet 0
"""

import json
import re
import argparse
from pathlib import Path
from typing import Any, Dict, List, Tuple, Set
import pandas as pd


UNKNOWN_TOKENS = {
    "not specified", "notspecified", "not_specified",
    "na", "n/a", "none", "null", "unknown", "unspecified",
    "-", "—", "–",
}

def is_truly_empty(x: Any) -> bool:
    if x is None:
        return True
    if isinstance(x, float) and pd.isna(x):
        return True
    s = str(x)
    return s.strip() == ""


def is_unknown_token(x: Any) -> bool:
    if is_truly_empty(x):
        return False
    s = str(x).strip().lower()
    return s in UNKNOWN_TOKENS


UNKNOWN_CANON = "Not specified"


NORMALIZE_MAP = {
    "multi-devicce": "Multi-device",
    "multidevice": "Multi-device",
    "single device": "Single device",

    "single user": "Single User",
    "multiuser": "Multi-user",
    "multiple users": "Multi-user",
    "multi-user": "Multi-user",

    "non-planar": "Non-Planar",
    "non-planar.": "Non-Planar",
    "ambient.": "Ambient",
    "hmd (vr)": "HMD (VR)",
    "hmd (vr/ar)": "HMD (VR/AR)",
}

SPLIT_REGEX = re.compile(r"[;,]")  


def norm_token(s: Any) -> str:
    if s is None:
        return ""
    t = str(s).strip()
    if not t:
        return ""
    key = t.lower()
    return NORMALIZE_MAP.get(key, t)


def split_multivalue(cell: Any) -> List[str]:
    """
    MultiSelect parsing with refined missing handling:
      - TRUE empty -> []
      - unknown token -> ["Not specified"]
      - else split on , ;
    """
    if is_truly_empty(cell):
        return []
    if is_unknown_token(cell):
        return [UNKNOWN_CANON]

    raw = str(cell).strip()
    parts = [norm_token(p) for p in SPLIT_REGEX.split(raw)]
    parts = [p for p in parts if p.strip() != ""]
    cleaned: List[str] = []
    seen: Set[str] = set()
    for p in parts:
        if p.strip().lower() in UNKNOWN_TOKENS:
            p = UNKNOWN_CANON
        if p and p not in seen:
            cleaned.append(p)
            seen.add(p)
    return cleaned


def cell_str(cell: Any) -> str:
    """
    String parsing with refined missing handling:
      - TRUE empty -> ""
      - unknown token -> "Not specified"
      - else stripped string
    """
    if is_truly_empty(cell):
        return ""
    if is_unknown_token(cell):
        return UNKNOWN_CANON
    return str(cell).strip()

DERIVE_FROM_COLS = [
    "Name",
    "Abstract",
    "Author Keywords",
    "Type of display",
    "Composition of display",
    "Explanation/Reason for the choice",
    "Application area",
    "Use Case",
    "Data type",
    "Goal of the visualization",
    "Displayed content/Visualization",
    "Human perception of visualization",
    "Known limitations or challenges for visualisation on this type of display",
    "Interaction",
    "Type of interaction",
    "Number of users",
    "Comments and notes",
    "Comments",
]

def row_corpus(row: pd.Series, cols: List[str]) -> str:
    chunks: List[str] = []
    for c in cols:
        if c in row.index:
            v = row[c]
            if not is_truly_empty(v):
                chunks.append(str(v))
    return " | ".join(chunks).lower()


DERIVE_RULES: Dict[str, List[Tuple[str, str]]] = {
    "MR Devices": [
        (r"\bar ost\b|\boptical see[- ]through\b|\bost\b", "AR OST HWD"),
        (r"\bar vst\b|\bvideo see[- ]through\b|\bvst\b", "AR VST HWD"),
        (r"\bhmd\b|\bhead[- ]mounted\b|\bhead mounted\b|\bvr\b|\bmixed reality\b|\baugmented reality\b", "HMD (VR/AR)"),
        (r"\bcave\b|\bcave[- ]like\b", "CAVE"),
        (r"\bprojection\b|\bprojected\b|\bspatial ar\b", "Projected"),
    ],
    "2D Devices": [
        (r"\bsmartphone\b|\bphone\b|\bmobile\b", "Smartphone"),
        (r"\blaptop\b|\bnotebook\b", "Laptop"),
        (r"\bdesktop\b", "Desktop"),
        (r"\btablet\b|\bipad\b", "Tablet"),
        (r"\bmonitor\b|\bdisplay\b|\bscreen\b", "Screen/Monitor"),
    ],

    "Configuration": [
        (r"\bmigratory interface\b|\bmigration\b", "Migratory Interface"),
        (r"\blogical distribution\b|\blogical distributed\b", "Logical Distribution"),
        (r"\bmulti[- ]device\b|\bmultidevice\b", "Multi-device"),
        (r"\bsingle device\b", "Single device"),
        (r"\bmultiple displays\b|\bmulti[- ]display\b|\bmulti display\b", "Multi-display"),
        (r"\bshared display\b|\bshared workspace\b", "Shared Display/Workspace"),
        (r"\bdistributed interface\b", "Distributed Interface"),
    ],
    "Temporal": [
        (r"\bserial\b", "Serial"),
        (r"\bparallel\b", "Parallel"),
        (r"\bexclusive\b", "Exclusive"),
        (r"\bsequential\b", "Serial"),
        (r"\bsimultaneous\b", "Parallel"),
        (r"\basynchronous\b|\bturn[- ]taking\b", "Asynchronous/Turn-taking"),
    ],
    "Relationship": [
        (r"\bsingle user\b", "Single User"),
        (r"\bmulti[- ]user\b|\bmultiple users\b|\bmultiuser\b", "Multi-user"),
        (r"\bshared component\b", "Multi-user - Shared Component"),
        (r"\bindividual component\b", "Multi-user - Individual Component"),
        (r"\bcollaborative\b|\bcollaboration\b|\bgroup\b", "Collaborative/Group"),
    ],
    "Range": [
        (r"\bpersonal\b", "Personal"),
        (r"\bsocial\b", "Social"),
        (r"\bnear\b", "Near"),
        (r"\bpublic\b", "Public"),
    ],
    "Device Dependency": [
        (r"\bfixed\b", "Fixed"),
        (r"\bsemi[- ]fixed\b", "Semi-fixed"),
        (r"\bflexible\b", "Flexible"),
    ],
    "Interaction Dynamics": [
        (r"\bbidirectional\b", "Bidirectional"),
        (r"\bunidirectional\b.*\b2d\b|\b2d[- ]centric\b", "Unidirectional (2D-centric)"),
        (r"\bunidirectional\b.*\bmr\b|\bmr[- ]centric\b", "Unidirectional (MR-centric)"),
        (r"\btangible\b|\bembodied\b", "Tangible/Embodied"),
        (r"\bshape[- ]changing\b|\bdeformable\b", "Shape-changing/Deformable"),
        (r"\bdirect manipulation\b|\bphysical manipulation\b", "Direct/Physical Manipulation"),
        (r"\bgesture\b|\bhand[- ]tracking\b", "Gesture/Hand-tracking"),
    ],
    "Space": [
        (r"\bco[- ]located\b|\bcolocated\b|\bcollocated\b", "Co-Located"),
        (r"\bremote\b|\bdistributed\b", "Remote/Distributed"),
        (r"\btelepresence\b", "Telepresence"),
        (r"\bshared space\b|\bshared workspace\b", "Shared Space/Workspace"),
    ],
    "Anchoring": [
        (r"\bfree\b", "Free"),
        (r"\bdynamic\b", "Dynamic"),
        (r"\bcomponent[- ]coupled\b|\bcoupled\b", "Component-coupled"),
    ],

    "Terminology": [
        (r"\bhybrid ui\b", "Term: Hybrid UI"),
    ],
    "Main Contribution": [
        (r"\bartifact\b", "Artifact"),
        (r"\bframework\b", "Framework"),
        (r"\bmodel\b", "Model"),
        (r"\balgorithm\b", "Algorithm"),
    ],
    "Secondary Contribution": [
        (r"\bempirical\b", "Empirical (+)"),
        (r"\bempirical\s*\(\s*-\s*\)\b", "Empirical (-)"),
    ],
    "Evaluation": [
        (r"\busage\b", "Usage"),
        (r"\bstudy\b|\buser study\b", "User study"),
        (r"\bexperiment\b", "Experiment"),
    ],
    "Edge Case": [
        (r"\bedge case\b|\bedgecase\b", "Yes"),
    ],

    "Display Geometry": [
        (r"\bcurved\b|\bcurvature\b|\bcurved surface\b|\bcurved surfaces\b", "Curved"),
        (r"\bspherical\b|\bsphere\b", "Spherical"),
        (r"\bcylindrical\b|\bcylinder\b", "Cylindrical"),
        (r"\bflexible\b", "Flexible"),
        (r"\bshape[- ]changing\b|\bdeformable\b", "Shape-changing/Deformable"),
        (r"\btangible\b|\bphysical\b", "Tangible/Physical Surface"),
    ],
}

TIMELINE_FIELDS = {"Year"}

BASE_FIELDS = [
    "Relevancenumber at Scopus",
    "Relevance Interval by Scopus",
    "Index",
    "Relevance for the work",
    "Exclusion criteria",
    "Inclusion criteria",
    "Comments and notes",
    "Useful in:",
    "Name",
    "Authors",
    "Year",
    "Source title",
    "DOI",
    "Bibtex",
    "Abstract",
    "Author Keywords",
    "Publisher",
    "Conference name",
    "Conference date",
    "Conference code",
    "Document Type",
    "Type of display",
    "Composition of display",
    "Explanation/Reason for the choice",
    "Application area",
    "Use Case",
    "Data type",
    "Goal of the visualization",
    "Displayed content/Visualization",
    "Human perception of visualization",
    "Known limitations or challenges for visualisation on this type of display",
    "Interaction",
    "Type of interaction",
    "Number of users",
    "Comments",
]

DERIVED_FIELDS = list(DERIVE_RULES.keys())

MULTISELECT_FIELDS = {
    "Authors",
    "Author Keywords",
    "Document Type",
    "Relevance Interval by Scopus",
    "Relevance for the work",
    "Exclusion criteria",
    "Inclusion criteria",
    "Useful in:",
    "Type of display",
    "Composition of display",
    "Application area",
    "Use Case",
    "Data type",
    "Goal of the visualization",
    "Human perception of visualization",
    "Interaction",
    "Type of interaction",
    "Number of users",
    *DERIVED_FIELDS,
}

FILTER_GROUPS: Dict[str, List[str]] = {
    "Technology": ["MR Devices", "2D Devices"],
    "Taxonomy": [
        "Configuration",
        "Temporal",
        "Relationship",
        "Range",
        "Device Dependency",
        "Interaction Dynamics",
        "Space",
        "Anchoring",
        "Display Geometry",
    ],
    "DISPLAY": ["Type of display", "Composition of display", "Application area", "Use Case"],
    "DATA & VIS": ["Data type", "Goal of the visualization", "Human perception of visualization", "Interaction"],
    "SCREENING": [
        "Exclusion criteria",
        "Inclusion criteria",
        "Useful in:",
    ],
}
DETAIL_SHOW = [
    "Name", "Authors", "Year", "DOI", "Bibtex",
    # derived taxonomy 
    "MR Devices", "2D Devices",
    "Configuration", "Temporal", "Relationship", "Range", "Device Dependency",
    "Interaction Dynamics", "Space", "Anchoring",
    "Display Geometry",
    # original columns
    "Type of display", "Composition of display", "Application area", "Use Case",
    "Data type", "Goal of the visualization", "Interaction", "Type of interaction", "Number of users",
    "Terminology", "Main Contribution", "Secondary Contribution", "Evaluation", "Edge Case",
    "Abstract",
]

SUMMARY_SHOW = ["Name", "Year", "MR Devices", "2D Devices", "Configuration", "Display Geometry"]


def derive_tags(corpus_lc: str, rules: List[Tuple[str, str]]) -> List[str]:
    out: List[str] = []
    for pattern, tag in rules:
        if re.search(pattern, corpus_lc):
            if tag not in out:
                out.append(tag)
    return out


def derive_all(row: pd.Series) -> Dict[str, List[str]]:
    corpus = row_corpus(row, DERIVE_FROM_COLS)
    derived: Dict[str, List[str]] = {}
    for field, rules in DERIVE_RULES.items():
        derived[field] = derive_tags(corpus, rules)

    # default edge case
    if "Edge Case" in derived:
        derived["Edge Case"] = ["No"] if len(derived["Edge Case"]) == 0 else derived["Edge Case"]
    return derived


def build_meta(fields: List[str]) -> List[Dict[str, str]]:
    meta: List[Dict[str, str]] = []
    for f in fields:
        if f in TIMELINE_FIELDS:
            meta.append({"name": f, "type": "Timeline"})
        elif f in MULTISELECT_FIELDS:
            meta.append({"name": f, "type": "MultiSelect"})
        else:
            meta.append({"name": f, "type": "String"})
    return meta


def build_config(meta_fields: List[str], title: str, desc: str, authors: str, github: str) -> Dict[str, Any]:
    filterBy = []
    for gname, cols in FILTER_GROUPS.items():
        cats = []
        for c in cols:
            if c in meta_fields:
                cats.append({"name": c, "values": [], "selected": []})
        if cats:
            filterBy.append({"groupName": gname, "categories": cats})

    return {
        "filterBy": filterBy,
        "detailView": {"view": "normal", "show": [c for c in DETAIL_SHOW if c in meta_fields]},
        "summaryView": {"view": "text", "showImg": True, "show": [c for c in SUMMARY_SHOW if c in meta_fields]},
        "topView": {
            "title": title,
            "description": desc,
            "authors": authors,
            "addEntry": {
                "description": [
                    "If you know a peer-reviewed published work that presents a contribution missing in our browser, please submit an entry!",
                    "Filling out the form below will create a json entry that can be added to an issue in our Github repository.",
                ],
                "github": github,
            },
        },
    }


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input-xlsx", required=True, help="Path to XLSX (e.g., final lr.xlsx)")
    p.add_argument("-o", "--out-dir", required=True, help="Output dir where survey-data.json & survey-config.json will be written")
    p.add_argument("--sheet", default=0, help="Sheet name or index (default 0)")
    p.add_argument("--header-row", type=int, default=1, help="0-based header row index for pandas (default 1 for 2nd row)")
    p.add_argument("--title", default="Hybrid User Interfaces", help="Website title")
    p.add_argument("--desc", default="Imported from XLSX with derived taxonomy.", help="Website description")
    p.add_argument("--authors", default="", help="Website authors string")
    p.add_argument("--github", default="", help="Github link (optional)")
    return p.parse_args()


def update_config_value_pools(cfg: Dict[str, Any], data: List[Dict[str, Any]]) -> None:
    """
    Fill cfg['filterBy'][*]['categories'][*]['values'] with unique values observed in data.
    - For MultiSelect fields: union of list items
    - For String fields: unique non-empty strings
    """
    pools: Dict[str, Set[str]] = {}

    for entry in data:
        for k, v in entry.items():
            if k not in pools:
                pools[k] = set()
            if isinstance(v, list):
                for item in v:
                    if item is None:
                        continue
                    s = str(item).strip()
                    if s != "":
                        pools[k].add(s)
            else:
                s = str(v).strip()
                if s != "":
                    pools[k].add(s)

    for group in cfg.get("filterBy", []):
        for cat in group.get("categories", []):
            name = cat.get("name")
            if not name:
                continue
            values = sorted(pools.get(name, set()))
            cat["values"] = values


def main():
    args = parse_args()
    xlsx_path = Path(args.input_xlsx)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(xlsx_path, sheet_name=args.sheet, header=args.header_row)
    df = df.loc[:, ~df.columns.isna()]

    if "Name" not in df.columns:
        raise RuntimeError("Column 'Name' not found. Check header row (--header-row).")

    df = df[~df["Name"].apply(is_truly_empty)].copy()

    all_fields = BASE_FIELDS + [f for f in DERIVED_FIELDS if f not in BASE_FIELDS]
    meta = build_meta(all_fields)

    data: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        entry: Dict[str, Any] = {}

        for f in BASE_FIELDS:
            if f not in df.columns:
                continue

            if f in TIMELINE_FIELDS:
                v = row.get(f, "")
                if is_truly_empty(v):
                    entry[f] = ""
                elif is_unknown_token(v):
                    entry[f] = UNKNOWN_CANON
                else:
                    try:
                        entry[f] = str(int(float(v)))
                    except Exception:
                        entry[f] = str(v).strip()

            elif f in MULTISELECT_FIELDS:
                entry[f] = split_multivalue(row.get(f, ""))

            else:
                entry[f] = cell_str(row.get(f, ""))

        # derived taxonomy
        derived = derive_all(row)
        for k, v in derived.items():
            entry[k] = v

        if "Authors" in entry and isinstance(entry["Authors"], list):
            entry["Authors"] = [a for a in entry["Authors"] if str(a).strip() != ""]
        if "Author Keywords" in entry and isinstance(entry["Author Keywords"], list):
            entry["Author Keywords"] = [a for a in entry["Author Keywords"] if str(a).strip() != ""]

        data.append(entry)

    survey_data = {"meta": meta, "data": data}
    cfg = build_config([m["name"] for m in meta], args.title, args.desc, args.authors, args.github)

 
    update_config_value_pools(cfg, data)

    (out_dir / "survey-data.json").write_text(json.dumps(survey_data, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "survey-config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Wrote:", out_dir / "survey-data.json")
    print("Wrote:", out_dir / "survey-config.json")
    print("Rows:", len(data))


if __name__ == "__main__":
    main()