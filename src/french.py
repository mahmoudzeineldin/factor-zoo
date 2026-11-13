# reads Ken French's factor files. only the monthly table is kept, converted from percent to decimals
import io
import re
import zipfile

import pandas as pd


def parse_french_csv(text):
    lines = text.splitlines()
    header = None
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.split(",")]
        if header is None:
            # the header row starts with an empty cell, then the factor names
            if len(cells) > 1 and cells[0] == "" and all(cells[1:]):
                header = cells[1:]
            continue
        if re.fullmatch(r"\d{6}", cells[0]):
            rows.append(cells)
        elif rows:
            # the monthly table has ended
            break
    if header is None or not rows:
        raise ValueError("Could not find the monthly table in the French file.")

    table = pd.DataFrame(rows, columns=["date"] + header)
    table["date"] = pd.to_datetime(table["date"], format="%Y%m") + pd.offsets.MonthEnd(0)
    table = table.set_index("date").apply(pd.to_numeric, errors="coerce")
    # French marks missing values with -99.99 or -999
    table = table.where(table > -99)
    return table / 100


def read_french_zip(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        name = z.namelist()[0]
        return parse_french_csv(z.read(name).decode("latin-1"))
