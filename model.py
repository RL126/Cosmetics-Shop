# model.py
# Predict which cart abandoners (no purchase in 24h) will buy in the next 7 days

import duckdb
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score

con = duckdb.connect("ecom.duckdb")
df = con.sql("SELECT * FROM cart_features").df()
con.close()

# Extra feature: items still left in the cart
df["items_left"] = (df["carts"] - df["removes"]).clip(lower=0)

features = ["views", "products_viewed", "carts", "removes", "items_left", "sessions",
            "cart_value", "avg_cart_price", "days_active_before_cart", "cart_on_peak_day"]
X = df[features].fillna(0)
y = df["bought_next7d"]

# Counts are very skewed, so log-transform them for logistic regression
X_log = X.copy()
for col in features:
    if col != "cart_on_peak_day":
        X_log[col] = np.log1p(X_log[col])

# Time-based split: train on early November, test on later November
train = df["first_cart"] < "2019-11-15"
test = ~train
print(f"Train: {train.sum():,} users, buy rate {y[train].mean():.1%}")
print(f"Test:  {test.sum():,} users, buy rate {y[test].mean():.1%}\n")


def top_decile_lift(y_true, scores):
    """Buy rate of the top 10% scored users divided by the overall buy rate."""
    order = np.argsort(-scores)
    k = len(order) // 10
    top_rate = y_true[order[:k]].mean()
    return top_rate, top_rate / y_true.mean()


# Model 1: Logistic regression (easy to interpret)
lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
lr.fit(X_log[train], y[train])
p_lr = lr.predict_proba(X_log[test])[:, 1]

# Model 2: Gradient boosting (handles non-linear patterns)
gb = HistGradientBoostingClassifier(random_state=0)
gb.fit(X[train], y[train])
p_gb = gb.predict_proba(X[test])[:, 1]

y_test = y[test].values
for name, p in [("Logistic regression", p_lr), ("Gradient boosting", p_gb)]:
    auc = roc_auc_score(y_test, p)
    top_rate, lift = top_decile_lift(y_test, p)
    print(f"{name}")
    print(f"  AUC: {auc:.3f}")
    print(f"  Top 10% buy rate: {top_rate:.1%} (lift {lift:.2f}x)\n")