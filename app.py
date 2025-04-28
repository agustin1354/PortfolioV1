import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Portfolio Tracker de Bonos", page_icon="💵", layout="wide")

# ----------------------
# Funciones auxiliares
# ----------------------

@st.cache_data
def load_data():
    try:
        with open("bonos.json", "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]  # por si es dict en lugar de lista
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error cargando bonos.json: {e}")
        return pd.DataFrame(columns=["bono", "precio"])

@st.cache_data
def save_data(df):
    try:
        df.to_json("bonos.json", orient="records", indent=4)
    except Exception as e:
        st.error(f"Error guardando bonos.json: {e}")

# ----------------------
# Código principal
# ----------------------

st.title("💵 Portfolio Tracker de Bonos")

# Cargar el JSON
bonos_df = load_data()

# Mostrar los bonos cargados
st.subheader("📋 Bonos disponibles")
st.dataframe(bonos_df)

# Sidebar para agregar posiciones
st.sidebar.header("Agregar una posición")

if not bonos_df.empty:
    bono_seleccionado = st.sidebar.selectbox("Seleccionar Bono", bonos_df["bono"].unique())
    cantidad = st.sidebar.number_input("Cantidad de títulos", min_value=0, value=0, step=1)
    
    # Botón para agregar al portfolio
    if st.sidebar.button("Agregar al portfolio"):
        if "portfolio" not in st.session_state:
            st.session_state["portfolio"] = []
        precio_bono = bonos_df.loc[bonos_df["Bono"] == bono_seleccionado, "precio"].values[0]
        st.session_state["portfolio"].append({
            "Bono": bono_seleccionado,
            "Cantidad": cantidad,
            "Precio actual": precio_bono,
            "Valor de la posición": cantidad * precio_bono
        })
else:
    st.sidebar.warning("No hay bonos cargados.")

# Mostrar portfolio
st.subheader("💼 Mi Portfolio")

if "portfolio" in st.session_state and st.session_state["portfolio"]:
    portfolio_df = pd.DataFrame(st.session_state["portfolio"])
    st.dataframe(portfolio_df)

    # Total del Portfolio
    total_valor = portfolio_df["Valor de la posición"].sum()
    st.metric("Valor Total del Portfolio", f"${total_valor:,.2f}")

    # Gráfico de torta
    st.subheader("📊 Distribución del Portfolio")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    portfolio_df.set_index('Bono')["Valor de la posición"].plot.pie(autopct='%1.1f%%', ax=ax, figsize=(6, 6))
    ax.set_ylabel("")
    st.pyplot(fig)
else:
    st.info("Todavía no agregaste bonos al portfolio.")

# ----------------------
# Fin del archivo
# ----------------------

