import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt

st.set_page_config(page_title="Portfolio de Bonos", page_icon="💰", layout="centered")

# -------- Load local JSON --------
@st.cache_data
def load_data():
    with open("bonos.json", "r") as f:
        data = json.load(f)
    return pd.DataFrame(data)

# -------- App --------
st.title("📈 Portfolio Tracker de Bonos")

bonos_df = load_data()

# Inicializar session_state
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

st.sidebar.header("Agregar Bono al Portfolio")

# Inputs
bono_seleccionado = st.sidebar.selectbox("Seleccionar Bono", bonos_df["Bono"].unique())
cantidad = st.sidebar.number_input("Cantidad", min_value=1, value=1, step=1)

# Botón agregar
if st.sidebar.button("➕ Agregar"):
    precio = bonos_df.loc[bonos_df["Bono"] == bono_seleccionado, "Precio"].values[0]
    st.session_state.portfolio.append({
        "Bono": bono_seleccionado,
        "Cantidad": cantidad,
        "Precio": precio,
        "Valor de la posición": precio * cantidad
    })
    st.success(f"{cantidad} x {bono_seleccionado} agregado al portfolio.")

# Botón limpiar
if st.sidebar.button("🗑️ Limpiar Portfolio"):
    st.session_state.portfolio = []
    st.warning("Portfolio vacío.")

# Mostrar portfolio
st.subheader("📜 Mi Portfolio")

if st.session_state.portfolio:
    portfolio_df = pd.DataFrame(st.session_state.portfolio)
    st.dataframe(portfolio_df)

    # Valor total
    valor_total = portfolio_df["Valor de la posición"].sum()
    st.metric("💵 Valor Total del Portfolio", f"USD {valor_total:,.2f}")

    # Gráfico
    fig, ax = plt.subplots(figsize=(6,6))
    portfolio_df.set_index('Bono')["Valor de la posición"].plot.pie(
        autopct='%1.1f%%', startangle=90, ax=ax
    )
    ax.set_ylabel('')
    st.subheader("📊 Distribución del Portfolio")
    st.pyplot(fig)
else:
    st.info("Todavía no agregaste bonos al portfolio.")

