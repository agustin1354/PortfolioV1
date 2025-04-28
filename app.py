import streamlit as st
import pandas as pd
import json

# Cargar los bonos desde el JSON
with open("bonos.json", "r") as f:
    bonos_data = json.load(f)

# Convertir a DataFrame
bonos_df = pd.DataFrame(bonos_data)

st.title("📈 Portfolio Tracker de Bonos")

# Seleccionar cantidad de bonos que querés agregar
num_bonos = st.number_input("¿Cuántos bonos querés agregar a tu portfolio?", min_value=1, max_value=50, value=1)

portfolio = []

# Para cada bono, seleccionás y ponés cantidad
for i in range(num_bonos):
    st.subheader(f"Bono #{i+1}")

    bono = st.selectbox(f"Seleccionar bono #{i+1}", bonos_df['bono'], key=f"bono_{i}")
    cantidad = st.number_input(f"Cantidad de {bono}", min_value=0.0, step=1.0, key=f"cantidad_{i}")

    # Precio del bono
    precio = bonos_df.loc[bonos_df['bono'] == bono, 'precio'].values[0]
    valor_total = cantidad * precio

    portfolio.append({
        "Bono": bono,
        "Cantidad": cantidad,
        "Precio Actual": precio,
        "Valor de la posición": valor_total
    })

# Mostrar resumen del portfolio
st.subheader("🧾 Resumen de Portfolio")

portfolio_df = pd.DataFrame(portfolio)
st.dataframe(portfolio_df)

# Mostrar total general
total = portfolio_df["Valor de la posición"].sum()
st.success(f"💰 Valor total del portfolio: ${total:,.2f}")
