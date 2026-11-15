# who comes back and buys within 7 days, out of people who added to cart
# but didn't buy in the first 24h? (features come from sql/11_cart_features.sql)
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

df["items_left"] = (df["carts"] - df["removes"]).clip(lower=0)

features = ["views", "products_viewed", "carts", "removes", "items_left", "sessions",
            "cart_value", "avg_cart_price", "days_active_before_cart", "cart_on_peak_day"]
X = df[features].fillna(0)
y = df["bought_next7d"]

# counts are very skewed, log them for the logistic regression
X_log = X.copy()
for col in features:
    if col != "cart_on_peak_day":
        X_log[col] = np.log1p(X_log[col])

# split by time instead of randomly: train on the first half of november
train = df["first_cart"] < "2019-11-15"
test = ~train
print(f"train: {train.sum():,} users, buy rate {y[train].mean():.1%}")
print(f"test:  {test.sum():,} users, buy rate {y[test].mean():.1%}\n")


def top10_lift(y_true, scores):
    order = np.argsort(-scores)
    k = len(order) // 10
    top_rate = y_true[order[:k]].mean()
    return top_rate, top_rate / y_true.mean()


lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
lr.fit(X_log[train], y[train])
p_lr = lr.predict_proba(X_log[test])[:, 1]

gb = HistGradientBoostingClassifier(random_state=0)
gb.fit(X[train], y[train])
p_gb = gb.predict_proba(X[test])[:, 1]

y_test = y[test].values
for name, p in [("logistic regression", p_lr), ("gradient boosting", p_gb)]:
    top_rate, lift = top10_lift(y_test, p)
    print(name)
    print(f"  AUC: {roc_auc_score(y_test, p):.3f}")
    print(f"  top 10% buy rate: {top_rate:.1%} (lift {lift:.2f}x)\n")