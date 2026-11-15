# charts.py
# Draw the 5 charts for the report and save them into the charts/ folder

import os
import duckdb
import matplotlib.pyplot as plt

con = duckdb.connect("ecom.duckdb")
os.makedirs("charts", exist_ok=True)

# Shared style
plt.rcParams.update({"figure.dpi": 120, "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False})
BLUE, GREY, RED = "#2563eb", "#9ca3af", "#dc2626"


def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"charts/{name}.png", dpi=200)
    plt.close(fig)
    print("saved charts/" + name + ".png")


# ---------- Chart 1: User-level funnel ----------
f = con.sql("""
    SELECT
        COUNT(*) FILTER (WHERE has_view)                               AS viewed,
        COUNT(*) FILTER (WHERE has_view AND has_cart)                  AS carted,
        COUNT(*) FILTER (WHERE has_view AND has_cart AND has_purchase) AS purchased
    FROM user_flags
""").df().iloc[0]

steps = ["View", "View + Cart", "View + Cart + Purchase"]
values = [f["viewed"], f["carted"], f["purchased"]]

fig, ax = plt.subplots(figsize=(8, 3.5))
bars = ax.barh(steps[::-1], values[::-1], color=BLUE)
for bar, v in zip(bars, values[::-1]):
    ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
            f"  {v:,}", va="center")
# Step conversion rates
ax.text(values[1], 1.45, f"{values[1] / values[0]:.1%} of viewers", color=GREY, fontsize=9)
ax.text(values[2], 0.45, f"{values[2] / values[1]:.1%} of carters", color=GREY, fontsize=9)
ax.set_xlim(0, values[0] * 1.2)
ax.set_xlabel("Users")
ax.set_title("User-level conversion funnel (Nov 2019)")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
save(fig, "1_funnel")


# ---------- Chart 2: Daily buyers with peak days ----------
d = con.sql("SELECT * FROM daily_tagged ORDER BY event_date").df()
threshold = 1.5 * d["purchase_users"].median()
peak = d[d["day_type"] == "Peak Day"]

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(d["event_date"], d["purchase_users"], color=BLUE, marker="o", markersize=3, label="Buyers per day")
ax.scatter(peak["event_date"], peak["purchase_users"], color=RED, zorder=3, label="Peak day")
ax.axhline(threshold, color=GREY, linestyle="--", linewidth=1, label=f"1.5 x median ({threshold:.0f})")
ax.set_ylabel("Buyers")
ax.set_title("Daily buyers: 8 peak days in November")
ax.legend(frameon=False)
fig.autofmt_xdate()
save(fig, "2_daily_buyers")


# ---------- Chart 3: Peak vs normal conversion rates ----------
d["view_to_cart"] = d["cart_users"] / d["view_users"] * 100
d["cart_to_purchase"] = d["purchase_users"] / d["cart_users"] * 100
d["purchase_rate"] = d["purchase_users"] / d["active_users"] * 100
m = d.groupby("day_type")[["view_to_cart", "cart_to_purchase", "purchase_rate"]].mean()

labels = ["View to cart", "Cart to purchase", "Daily purchase rate"]
x = range(len(labels))
w = 0.38
fig, ax = plt.subplots(figsize=(8, 4))
b1 = ax.bar([i - w / 2 for i in x], m.loc["Normal Day"], w, color=GREY, label="Normal day")
b2 = ax.bar([i + w / 2 for i in x], m.loc["Peak Day"], w, color=BLUE, label="Peak day")
for bars in (b1, b2):
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=9)
ax.set_xticks(list(x))
ax.set_xticklabels(labels)
ax.set_ylabel("Average daily rate (%)")
ax.set_title("Peak days convert better at every step (Welch t-test, p < 0.001)")
ax.legend(frameon=False)
save(fig, "3_peak_vs_normal")


# ---------- Chart 4: Time from first cart to purchase ----------
t = con.sql("""
    SELECT
        CASE
            WHEN minutes < 10   THEN '< 10 min'
            WHEN minutes < 60   THEN '10-60 min'
            WHEN minutes < 1440 THEN '1-24 h'
            WHEN minutes < 4320 THEN '1-3 days'
            ELSE '> 3 days'
        END AS band,
        MIN(minutes) AS sort_key,
        COUNT(*) AS users
    FROM cart_to_buy
    GROUP BY band
    ORDER BY sort_key
""").df()
t["pct"] = t["users"] / t["users"].sum() * 100

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(t["band"], t["pct"], color=BLUE)
for bar, p in zip(bars, t["pct"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{p:.1f}%",
            ha="center", va="bottom", fontsize=9)
ax.set_ylabel("Share of buyers (%)")
ax.set_title("Time from first add-to-cart to purchase (median 79 min)")
save(fig, "4_cart_to_purchase_time")


# ---------- Chart 5: Conversion by price band ----------
p = con.sql("""
    WITH b AS (
        SELECT *,
            CASE
                WHEN price < 5  THEN '< 5'
                WHEN price < 10 THEN '5-10'
                WHEN price < 20 THEN '10-20'
                WHEN price < 50 THEN '20-50'
                ELSE '50+'
            END AS band
        FROM events
        WHERE price > 0
    )
    SELECT
        band,
        MIN(price) AS sort_key,
        COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'view')     AS viewers,
        COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'purchase') AS buyers,
        SUM(price) FILTER (WHERE event_type = 'purchase')              AS revenue
    FROM b
    GROUP BY band
    ORDER BY sort_key
""").df()
p["conv"] = p["buyers"] / p["viewers"] * 100
p["rev_share"] = p["revenue"] / p["revenue"].sum() * 100

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(p["band"], p["conv"], color=BLUE)
for bar, c, r in zip(bars, p["conv"], p["rev_share"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
            f"{c:.1f}%\n({r:.0f}% of revenue)", ha="center", va="bottom", fontsize=9)
ax.set_xlabel("Price band")
ax.set_ylabel("View to purchase (%)")
ax.set_ylim(0, p["conv"].max() * 1.3)
ax.set_title("Conversion drops sharply above 20")
save(fig, "5_price_band")

con.close()