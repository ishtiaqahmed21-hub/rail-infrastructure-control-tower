"""Parse frozen official snapshots without optional spreadsheet engines."""

from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
import pandas as pd


class TableParser(HTMLParser):
    """Extract table cells as text, retaining source values."""

    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = []
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        if tag in ("td", "th"):
            self.cell = ""

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(self.cell.strip())
            self.cell = None
        if tag == "tr" and self.row:
            self.rows.append(self.row)


def load_operations(path):
    parser = TableParser()
    parser.feed(Path(path).read_text(encoding="utf-8"))
    frame = pd.DataFrame(parser.rows[1:], columns=parser.rows[0])
    if len(frame.columns) != 11:
        raise ValueError("ORR 3181a schema drift")
    frame.columns = ["period"] + [
        f"{r}_{s}"
        for s in ("periodic", "maa")
        for r in (
            "Eastern",
            "North West and Central",
            "Scotland",
            "Southern",
            "Wales and Western",
        )
    ]
    for c in frame.columns[1:]:
        frame[c] = pd.to_numeric(frame[c].replace("[z]", None), errors="raise")
    return frame


def load_infrastructure(path):
    ns = {"t": "urn:oasis:names:tc:opendocument:xmlns:table:1.0"}
    root = ET.fromstring(zipfile.ZipFile(path).read("content.xml"))
    table = [
        t
        for t in root.findall(".//t:table", ns)
        if t.attrib.get("{" + ns["t"] + "}name") == "6320_Mainline_infrastructure"
    ][0]
    rows = []
    for row in table.findall("t:table-row", ns):
        vals = [" ".join(c.itertext()) for c in row.findall("t:table-cell", ns)]
        if vals and vals[0] in ("Great Britain", "England", "Wales", "Scotland"):
            rows.append(vals[:7])
    out = pd.DataFrame(
        rows,
        columns=[
            "nation",
            "period",
            "route_km",
            "electrified_route_km",
            "track_km",
            "electrified_track_km",
            "new_electrification_track_km",
        ],
    )
    out["break_flag"] = out.period.str.contains("[b]", regex=False)
    for c in out.columns[2:7]:
        out[c] = pd.to_numeric(
            out[c]
            .str.replace(",", "")
            .str.replace("[b]", "", regex=False)
            .str.strip()
            .replace("[x]", None),
            errors="coerce",
        )
    return out
