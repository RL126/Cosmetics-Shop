# run.py  运行一个 .sql 文件，把每一句查询的结果打印出来
# 用法一：python run.py sql/01_explore.sql
# 用法二：直接点 VS Code 的 ▶，会运行下面 DEFAULT_SQL 指定的文件

import sys
import duckdb
import pandas as pd

DEFAULT_SQL = "sql/11_cart_features.sql"   

# 让 pandas 显示所有列，不折叠
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)

con = duckdb.connect("ecom.duckdb")

#read the sql file
sql_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SQL
text = open(sql_file, encoding="utf-8").read()


for chunk in text.split(";"):
    lines = chunk.strip().splitlines()
    #skip empty lines and comments
    code = [l for l in lines if l.strip() and not l.strip().startswith("--")]
    if not code:
        continue

    #print("====", lines[0].strip("- ").strip())  
    comments = [l.strip("- ").strip() for l in lines if l.strip().startswith("--")]
    if comments:
        print("====", comments[-1])

    result = con.sql(chunk)
    if result is not None:
        print(result.df())
    print()

con.close()