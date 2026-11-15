# are conversion rates on peak days really higher than on normal days?
import duckdb
from scipy import stats

con = duckdb.connect("ecom.duckdb")
df = con.sql("SELECT * FROM daily_tagged").df()
con.close()

df["view_to_cart"] = df["cart_users"] / df["view_users"] * 100
df["cart_to_purchase"] = df["purchase_users"] / df["cart_users"] * 100
df["purchase_rate"] = df["purchase_users"] / df["active_users"] * 100

peak = df[df["day_type"] == "Peak Day"]
normal = df[df["day_type"] == "Normal Day"]
print(f"peak days: {len(peak)}, normal days: {len(normal)}\n")

# welch's t-test, since the two groups have different sizes and spreads
for col in ["view_to_cart", "cart_to_purchase", "purchase_rate"]:
    t, p = stats.ttest_ind(peak[col], normal[col], equal_var=False)
    print(col)
    print(f"  peak {peak[col].mean():.2f}%  normal {normal[col].mean():.2f}%")
    print(f"  t = {t:.2f}, p = {p:.6f}\n")