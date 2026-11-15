# what the model picks up on, and what using it for cart reminders would look like
import duckdb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score
from sklearn.inspection import permutation_importance

con = duckdb.connect("ecom.duckdb")
df = con.sql("SELECT * FROM cart_features").df()
con.close()

df["items_left"] = (df["carts"] - df["removes"]).clip(lower=0)
features = ["views", "products_viewed", "carts", "removes", "items_left", "sessions",
            "cart_value", "avg_cart_price", "days_active_before_cart", "cart_on_peak_day"]
X = df[features].fillna(0)
y = df["bought_next7d"]

X_log = X.copy()
for col in features:
    if col != "cart_on_peak_day":
        X_log[col] = np.log1p(X_log[col])

train = df["first_cart"] < "2019-11-15"
test = ~train

model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
model.fit(X_log[train], y[train])
scores = model.predict_proba(X_log[test])[:, 1]
y_test = y[test].values
print(f"test AUC: {roc_auc_score(y_test, scores):.3f}\n")


# feature importance
# the coefficients are hard to read because carts, cart_value and avg_cart_price
# move together, so shuffle one feature at a time and see how much AUC drops
pi = permutation_importance(model, X_log[test], y_test, scoring="roc_auc",
                            n_repeats=5, random_state=0)
importance = pd.Series(pi.importances_mean, index=features).sort_values(ascending=False)
print("drop in AUC when shuffled:")
print(importance.round(3).to_string(), "\n")

# check the main ones against the actual buy rate
d = df.copy()
d["cart_value_quartile"] = pd.qcut(d["cart_value"].fillna(0), 4,
                                   labels=["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"])
print("buy rate by cart value:")
print(d.groupby("cart_value_quartile", observed=True)
        .agg(users=("bought_next7d", "size"),
             median_cart_value=("cart_value", "median"),
             buy_rate=("bought_next7d", "mean"))
        .round(3).to_string(), "\n")

d["session_group"] = pd.cut(d["sessions"], [0, 1, 2, 4, 10_000], labels=["1", "2", "3-4", "5+"])
print("buy rate by sessions in the first 24h:")
print(d.groupby("session_group", observed=True)
        .agg(users=("bought_next7d", "size"), buy_rate=("bought_next7d", "mean"))
        .round(3).to_string(), "\n")

d["removed_items"] = np.where(d["removes"] > 0, "removed something", "removed nothing")
print("buy rate by whether they removed anything:")
print(d.groupby("removed_items")
        .agg(users=("bought_next7d", "size"), buy_rate=("bought_next7d", "mean"))
        .round(3).to_string(), "\n")


# if we only reminded the top x% by score, how many eventual buyers would we reach?
order = np.argsort(-scores)
n = len(order)
total_buyers = y_test.sum()

rows = []
for share in [0.1, 0.2, 0.3, 0.5]:
    k = int(n * share)
    buyers = y_test[order[:k]].sum()
    rows.append({
        "target_top": f"{share:.0%}",
        "users_contacted": k,
        "buyers_reached": int(buyers),
        "buy_rate": round(buyers / k, 3),
        "share_of_all_buyers": round(buyers / total_buyers, 3),
        "buyers_if_random": round(k * y_test.mean()),
    })
targeting = pd.DataFrame(rows)
print(targeting.to_string(index=False), "\n")

# gains chart
reached = np.cumsum(y_test[order]) / total_buyers
x = np.arange(1, n + 1) / n
top20 = targeting.loc[1, "share_of_all_buyers"]

fig, ax = plt.subplots(figsize=(6, 4.5))
ax.plot(x * 100, reached * 100, color="#2563eb", label="Model")
ax.plot([0, 100], [0, 100], color="#9ca3af", linestyle="--", label="Random")
ax.scatter([20], [top20 * 100], color="#dc2626", zorder=3)
ax.annotate(f"Top 20% reaches {top20:.0%} of buyers", (20, top20 * 100),
            textcoords="offset points", xytext=(10, -15), fontsize=9)
ax.set_xlabel("Users contacted (%)")
ax.set_ylabel("Eventual buyers reached (%)")
ax.set_title("Who to remind: model vs random")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig("charts/6_gains.png", dpi=200)
print("saved charts/6_gains.png")

# ranked list of the top 20% (not uploaded to github)
scored = df.loc[test, ["user_id", "first_cart", "cart_value"]].copy()
scored["score"] = scores.round(4)
scored.sort_values("score", ascending=False).head(int(n * 0.2)).to_csv(
    "reminder_list_top20.csv", index=False)
print("saved reminder_list_top20.csv")