"""Data Analytics Dashboard : analyse de ventes avec Pandas, Matplotlib et Seaborn.

Usage :
    python analytics_dashboard.py [chemin_du_csv]
Sortie : dashboard.png + résumé dans la console.
"""
import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

CSV = sys.argv[1] if len(sys.argv) > 1 else "sales.csv"
PURPLE = "#5b2fc9"

# ---------- 1. Chargement et nettoyage ----------
df = pd.read_csv(CSV, parse_dates=["date"])
df = df.dropna().drop_duplicates(subset="order_id")
df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()

# ---------- 2. KPIs ----------
total_sales = df["amount"].sum()
total_orders = df["order_id"].nunique()
total_customers = df["customer_id"].nunique()
avg_order = total_sales / total_orders

monthly = df.groupby("month")["amount"].sum()
by_cat = df.groupby("category")["amount"].sum().sort_values(ascending=False)
best_month = monthly.idxmax()
repeat_rate = (df.groupby("customer_id").size() > 1).mean() * 100

print("=== Résumé ===")
print(f"Ventes totales     : {total_sales:,.2f} $")
print(f"Commandes          : {total_orders}")
print(f"Clients            : {total_customers}")
print(f"Panier moyen       : {avg_order:,.2f} $")
print(f"Meilleur mois      : {best_month:%B %Y} ({monthly.max():,.2f} $)")
print(f"Clients récurrents : {repeat_rate:.1f} %")
print("\nVentes par catégorie :")
print((by_cat / total_sales * 100).round(1).astype(str) + " %")

# ---------- 3. Dashboard ----------
sns.set_theme(style="whitegrid")
fig = plt.figure(figsize=(14, 9), facecolor="white")
gs = fig.add_gridspec(3, 4, height_ratios=[0.9, 2.2, 2.2], hspace=0.55, wspace=0.35)

fig.suptitle("Sales Overview", x=0.06, ha="left", fontsize=22,
             fontweight="bold", color=PURPLE)

# Cartes KPI
kpis = [
    ("Total Sales", f"${total_sales:,.0f}"),
    ("Total Orders", f"{total_orders}"),
    ("Total Customers", f"{total_customers}"),
    ("Average Order", f"${avg_order:,.2f}"),
]
for i, (label, value) in enumerate(kpis):
    ax = fig.add_subplot(gs[0, i])
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes,
                               facecolor="#f3efff", edgecolor="#d9cffa", lw=1.2))
    ax.text(0.5, 0.74, label, ha="center", va="center", fontsize=11, color="#555")
    ax.text(0.5, 0.32, value, ha="center", va="center", fontsize=20,
            fontweight="bold", color=PURPLE)

# Ventes dans le temps
ax1 = fig.add_subplot(gs[1:, :2])
sns.lineplot(x=monthly.index, y=monthly.values, marker="o", color=PURPLE, ax=ax1)
ax1.fill_between(monthly.index, monthly.values, alpha=0.12, color=PURPLE)
ax1.set_title("Sales Over Time (monthly)", loc="left", fontweight="bold")
ax1.set_xlabel("")
ax1.set_ylabel("Sales ($)")
ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b"))

# Ventes par catégorie (camembert)
ax2 = fig.add_subplot(gs[1:, 2:])
colors = sns.color_palette("Set2", len(by_cat))
ax2.pie(by_cat.values, labels=by_cat.index, colors=colors, autopct="%1.0f%%",
        startangle=90, wedgeprops={"edgecolor": "white", "linewidth": 2})
ax2.set_title("Sales by Category", loc="left", fontweight="bold")

fig.savefig("dashboard.png", dpi=150, bbox_inches="tight")
print("\ndashboard.png créé.")
