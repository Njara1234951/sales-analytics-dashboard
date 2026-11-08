"""Analyse avancée des ventes : croissance, segmentation RFM, prévision, jours de semaine.

Usage : python advanced_analysis.py [chemin_du_csv]
Sorties : dashboard_advanced.png + résumé console.
"""
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

CSV = sys.argv[1] if len(sys.argv) > 1 else "sales.csv"
PURPLE = "#5b2fc9"

df = pd.read_csv(CSV, parse_dates=["date"]).dropna().drop_duplicates(subset="order_id")
df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()

# ---------- 1. Croissance mensuelle ----------
monthly = df.groupby("month")["amount"].sum()
growth = monthly.pct_change() * 100

# ---------- 2. Prévision (tendance linéaire, 3 mois) ----------
x = np.arange(len(monthly))
slope, intercept = np.polyfit(x, monthly.values, 1)
future_x = np.arange(len(monthly), len(monthly) + 3)
future_idx = pd.date_range(monthly.index[-1] + pd.offsets.MonthBegin(1), periods=3, freq="MS")
forecast = pd.Series(slope * future_x + intercept, index=future_idx)
resid_std = np.std(monthly.values - (slope * x + intercept), ddof=2)

# ---------- 3. Segmentation RFM ----------
snapshot = df["date"].max() + pd.Timedelta(days=1)
rfm = df.groupby("customer_id").agg(
    recency=("date", lambda s: (snapshot - s.max()).days),
    frequency=("order_id", "count"),
    monetary=("amount", "sum"),
)
rfm["R"] = pd.qcut(rfm["recency"], 3, labels=[3, 2, 1]).astype(int)
rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"), 3, labels=[1, 2, 3]).astype(int)
rfm["M"] = pd.qcut(rfm["monetary"], 3, labels=[1, 2, 3]).astype(int)
score = rfm["R"] + rfm["F"] + rfm["M"]
rfm["segment"] = pd.cut(score, bins=[0, 4, 6, 9], labels=["À risque", "Réguliers", "Champions"])
seg = rfm.groupby("segment", observed=True).agg(
    clients=("monetary", "size"), ca=("monetary", "sum"))
seg["part_ca_%"] = seg["ca"] / seg["ca"].sum() * 100

# ---------- 4. Jour de semaine x catégorie ----------
df["weekday"] = df["date"].dt.dayofweek
days = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
heat = df.pivot_table(index="category", columns="weekday", values="amount",
                      aggfunc="sum", fill_value=0)
heat = heat.reindex(columns=range(7), fill_value=0)
heat.columns = days

# ---------- 5. Concentration (Pareto clients) ----------
cust = df.groupby("customer_id")["amount"].sum().sort_values(ascending=False)
top20_n = int(np.ceil(len(cust) * 0.2))
top20_share = cust.head(top20_n).sum() / cust.sum() * 100

print("=== Analyse avancée ===")
print(f"Croissance moyenne mensuelle : {growth.mean():+.1f} %")
print(f"Tendance : {slope:+,.0f} $ de ventes en plus par mois")
print("Prévision (3 mois) :")
for d, v in forecast.items():
    print(f"  {d:%b %Y} : {v:,.0f} $ (± {1.96 * resid_std:,.0f})")
print("\nSegments RFM :")
print(seg.round(1).to_string())
print(f"\nLes 20 % meilleurs clients font {top20_share:.1f} % du chiffre d'affaires")
best = heat.sum().idxmax()
print(f"Meilleur jour de la semaine : {best}")

# ---------- Dashboard ----------
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(2, 2, figsize=(14, 9))
fig.suptitle("Advanced Sales Analytics", x=0.06, ha="left", fontsize=22,
             fontweight="bold", color=PURPLE)

# a) Ventes + prévision
ax = axes[0, 0]
ax.plot(monthly.index, monthly.values, marker="o", color=PURPLE, label="Réel")
ax.plot([monthly.index[-1], *future_idx], [monthly.values[-1], *forecast.values],
        "--", marker="o", color="#e07a1f", label="Prévision")
ax.fill_between(future_idx, forecast.values - 1.96 * resid_std,
                forecast.values + 1.96 * resid_std, color="#e07a1f", alpha=0.15)
ax.set_title("Ventes mensuelles et prévision (tendance linéaire)", loc="left", fontweight="bold")
ax.set_ylabel("Ventes ($)")
ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b"))
ax.legend()

# b) Croissance mensuelle
ax = axes[0, 1]
g = growth.dropna()
ax.bar(g.index, g.values, width=20, color=np.where(g.values >= 0, PURPLE, "#d1495b"))
ax.axhline(0, color="#333", lw=0.8)
ax.set_title("Croissance mois sur mois (%)", loc="left", fontweight="bold")
ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b"))

# c) Segments RFM
ax = axes[1, 0]
order = [s for s in ["Champions", "Réguliers", "À risque"] if s in seg.index]
s2 = seg.loc[order]
bars = ax.bar(s2.index.astype(str), s2["ca"], color=[PURPLE, "#8f73e0", "#c9bdf2"][:len(s2)])
for b, (n, p) in zip(bars, zip(s2["clients"], s2["part_ca_%"])):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{n} clients\n{p:.0f} % du CA",
            ha="center", va="bottom", fontsize=10)
ax.set_ylim(0, s2["ca"].max() * 1.25)
ax.set_title("Segmentation clients (RFM)", loc="left", fontweight="bold")
ax.set_ylabel("Chiffre d'affaires ($)")

# d) Heatmap jour x catégorie
ax = axes[1, 1]
sns.heatmap(heat, cmap="Purples", annot=True, fmt=".0f", cbar=False, ax=ax)
ax.set_title("Ventes par catégorie et jour de semaine ($)", loc="left", fontweight="bold")
ax.set_xlabel("")
ax.set_ylabel("")

fig.tight_layout(rect=(0, 0, 1, 0.94))
fig.savefig("dashboard_advanced.png", dpi=150, bbox_inches="tight")
print("\ndashboard_advanced.png créé.")
