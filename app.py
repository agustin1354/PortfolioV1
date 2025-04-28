pip install -r requirements.txt

import streamlit as st
import pandas as pd
import json
import os

# Cargar los bonos scrapeados
with open("bonos.json", "r") as f:
    bonos_data = json.load(f)

# Convertir a DataFrame
bonos_df = pd.DataFrame(bonos_data)

# Cargar portfolio guardado si existe
PORTFOLIO_FILE = "mi_portfolio.json"
if os.path.exists(PORTFOLIO_FILE):
    with open(PORTFOLIO_FILE, "r") as f:
        saved_portfolio = json.load(f)
else:
    saved_portfolio = []

# Función para guardar el portfolio actual
def guardar_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=4)

st.title("📈 Portfolio Tracker de Bonos")

# Opciones para agregar nuevo bono al portfolio
st.subheader("➕ Agregar nuevo bono")

with st.form(key="agregar_bono_form"):
    bono = st.selectbox("Seleccionar bono", bonos_df['bono'])
    cantidad = st.number_input(f"Cantidad de {bono}", min_value=0.0, step=1.0)
    submit_button = st.form_submit_button(label="Agregar al portfolio")

    if submit_button:
        precio = bonos_df.loc[bonos_df['bono'] == bono, 'precio'].values[0]
        valor_total = cantidad * precio

        nuevo_bono = {
            "Bono": bono,
            "Cantidad": cantidad,
            "Precio Actual": precio,
            "Valor de la posición": valor_total
        }

        saved_portfolio.append(nuevo_bono)
        guardar_portfolio(saved_portfolio)
        st.success(f"✅ {bono} agregado correctamente al portfolio.")

# Mostrar el portfolio actual
st.subheader("🧾 Mi Portfolio Actual")

if saved_portfolio:
    portfolio_df = pd.DataFrame(saved_portfolio)
    st.dataframe(portfolio_df)

    total = portfolio_df["Valor de la posición"].sum()
    st.success(f"💰 Valor total del portfolio: ${total:,.2f}")

    # Graficar distribución
    st.subheader("📊 Distribución del Portfolio")
    fig = portfolio_df.set_index('Bono')["Valor de la posición"].plot.pie(autopct='%1.1f%%', figsize=(6,6)).get_figure()
    st.pyplot(fig)

    # Botón para limpiar todo
    if st.button("🗑️ Borrar todo el portfolio"):
        saved_portfolio = []
        guardar_portfolio(saved_portfolio)
        st.success("Portfolio eliminado correctamente.")
else:
    st.info("Todavía no agregaste bonos a tu portfolio.")
