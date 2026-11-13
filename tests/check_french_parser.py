# checks the French file reader on a small made-up file
import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from french import read_french_zip

TEXT = """This file was created by CMPT_ME_BEME_OP_INV_RETS using the 202609 CRSP database.
The 1-month TBill rate data until 202405 are from Ibbotson Associates.

,Mkt-RF,SMB,HML,RMW,CMA,RF
196307,   -0.39,   -0.41,   -0.97,    0.68,   -1.18,    0.27
196308,    5.07,   -0.80,    1.80,    0.36,   -0.35,    0.25
196309,   -1.57,   -0.52,    0.13,   -0.71,    0.29,  -99.99

 Annual Factors: January-December
,Mkt-RF,SMB,HML,RMW,CMA,RF
   1964,   12.52,   -0.10,    9.64,   -2.26,    6.56,    3.54
"""

buffer = io.BytesIO()
with zipfile.ZipFile(buffer, "w") as z:
    z.writestr("F-F_Research_Data_5_Factors_2x3.csv", TEXT)
table = read_french_zip(buffer.getvalue())

assert list(table.columns) == ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]
assert len(table) == 3, len(table)
assert str(table.index[0].date()) == "1963-07-31"
assert abs(table.loc["1963-08-31", "Mkt-RF"] - 0.0507) < 1e-12
assert table["RF"].isna().sum() == 1
print("French file reader passed.")
