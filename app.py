"""Dashboard interactif des ventes (Streamlit + Plotly).

Lancer : streamlit run app.py
"""
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Sales Dashboard", layout="wide")
st.title("Sales Overview")


@st.cache_data
def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"]).dropna().drop_duplicates(subset="order_id")
    return df


uploaded = st.sidebar.file_uploader("Votre fichier CSV (optionnel)", type="csv")
df = load(uploaded) if uploaded else load("sales.csv")

# ---------- Filtres ----------
st.sidebar.header("Filtres")
dmin, dmax = df["date"].min().date(), df["date"].max().date()
start, end = st.sidebar.date_input("Période", (dmin, dmax), min_value=dmin, max_value=dmax)
cats = st.sidebar.multiselect("Catégories", sorted(df["category"].unique()),
                              default=sorted(df["category"].unique()))

mask = (df["date"].dt.date >= start) & (df["date"].dt.date <= end) & df["category"].isin(cats)
f = df[mask]

if f.empty:
    st.warning("Aucune donnée pour ces filtres.")
    st.stop()

# ---------- KPIs ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Sales", f"${f['amount'].sum():,.0f}")
c2.metric("Total Orders", f"{f['order_id'].nunique()}")
c3.metric("Total Customers", f"{f['customer_id'].nunique()}")
c4.metric("Average Order", f"${f['amount'].sum() / f['order_id'].nunique():,.2f}")

# ---------- Graphiques ----------
left, right = st.columns(2)

monthly = (f.assign(month=f["date"].dt.to_period("M").dt.to_timestamp())
             .groupby("month", as_index=False)["amount"].sum())
left.plotly_chart(
    px.line(monthly, x="month", y="amount", markers=True, title="Sales Over Time",
            labels={"month": "", "amount": "Ventes ($)"}),
    width="stretch")

by_cat = f.groupby("category", as_index=False)["amount"].sum()
right.plotly_chart(
    px.pie(by_cat, names="category", values="amount", hole=0.4, title="Sales by Category"),
    width="stretch")

# ---------- Top clients + données ----------
st.subheader("Top 10 clients")
top = (f.groupby("customer_id").agg(commandes=("order_id", "count"), ventes=("amount", "sum"))
         .sort_values("ventes", ascending=False).head(10).round(2))
st.dataframe(top, width="stretch")

with st.expander("Voir les données brutes"):
    st.dataframe(f, width="stretch")
    st.download_button("Télécharger le CSV filtré", f.to_csv(index=False).encode(),
                       "sales_filtered.csv", "text/csv")
