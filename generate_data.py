"""Génère un jeu de données de ventes fictif (sales.csv).

Calé sur la maquette : 320 commandes, 150 clients, ~24 850 $ de ventes.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

N_ORDERS = 320
N_CUSTOMERS = 150
TARGET_TOTAL = 24_850.00

categories = ["Electronics", "Clothing", "Home", "Beauty", "Others"]
cat_probs = [0.32, 0.26, 0.18, 0.14, 0.10]
cat_price = {"Electronics": 130, "Clothing": 60, "Home": 70, "Beauty": 40, "Others": 45}

# Dates : 12 mois avec une légère tendance haussière
dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
weights = np.linspace(0.8, 1.4, len(dates))
weights /= weights.sum()
order_dates = rng.choice(dates, size=N_ORDERS, p=weights)

# Clients : chacun apparaît au moins une fois
customers = np.concatenate([
    np.arange(1, N_CUSTOMERS + 1),
    rng.integers(1, N_CUSTOMERS + 1, size=N_ORDERS - N_CUSTOMERS),
])
rng.shuffle(customers)

cats = rng.choice(categories, size=N_ORDERS, p=cat_probs)
amounts = np.array([rng.gamma(shape=3.0, scale=cat_price[c] / 3.0) for c in cats])

# Mise à l'échelle pour atteindre exactement le total cible
amounts = amounts * TARGET_TOTAL / amounts.sum()
amounts = np.round(amounts, 2)
amounts[-1] = round(amounts[-1] + (TARGET_TOTAL - amounts.sum()), 2)

df = pd.DataFrame({
    "order_id": np.arange(1001, 1001 + N_ORDERS),
    "date": pd.to_datetime(order_dates),
    "customer_id": customers,
    "category": cats,
    "amount": amounts,
}).sort_values("date").reset_index(drop=True)

df.to_csv("sales.csv", index=False)
print(f"sales.csv créé : {len(df)} lignes, total = {df['amount'].sum():,.2f} $")
