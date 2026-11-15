# analysis.py
# Welch's t-test: do peak days have significantly higher conversion rates than normal days?

import duckdb
from scipy import stats

con = duckdb.connect("ecom.duckdb")

# Load the daily_tagged table into a pandas DataFrame
df = con.sql("SELECT * FROM daily_tagged").df()

# Daily conversion rates (in %), added as new columns
# Must be added BEFORE splitting into groups
df["view_to_cart"] = df["cart_users"] / df["view_users"] * 100
df["cart_to_purchase"] = df["purchase_users"] / df["cart_users"] * 100
df["purchase_rate"] = df["purchase_users"] / df["active_users"] * 100

# Split into two groups
peak = df[df["day_type"] == "Peak Day"]
normal = df[df["day_type"] == "Normal Day"]

print(f"Peak days: {len(peak)}, Normal days: {len(normal)}\n")

# Welch's t-test for each metric (equal_var=False: does not assume equal variances)
for col in ["view_to_cart", "cart_to_purchase", "purchase_rate"]:
    result = stats.ttest_ind(peak[col], normal[col], equal_var=False)
    print(f"{col}")
    print(f"  peak mean:   {peak[col].mean():.2f}%")
    print(f"  normal mean: {normal[col].mean():.2f}%")
    print(f"  t = {result.statistic:.2f}, p = {result.pvalue:.6f}\n")

con.close()