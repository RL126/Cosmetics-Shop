# run a .sql file and print each query's result
# python run.py sql/03_clean.sql 
# python run.py 

import os
import sys
import glob
import duckdb
import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)

base = os.path.dirname(os.path.abspath(__file__))
con = duckdb.connect(os.path.join(base, "ecom.duckdb"))

if len(sys.argv) > 1:
    files = [os.path.join(base, sys.argv[1])]
else:
    files = sorted(glob.glob(os.path.join(base, "sql", "*.sql")))

for path in files:
    print("====", os.path.basename(path))
    text = open(path, encoding="utf-8").read()

    # split on ; (so don't put ; inside comments)
    for chunk in text.split(";"):
        lines = chunk.strip().splitlines()
        code = [l for l in lines if l.strip() and not l.strip().startswith("--")]
        if not code:
            continue

        # use the last comment above the query as a label
        comments = [l.strip("- ").strip() for l in lines if l.strip().startswith("--")]
        if comments:
            print("--", comments[-1])

        result = con.sql(chunk)
        if result is not None:
            print(result.df())
        print()

con.close()