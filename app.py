import streamlit as st
import pandas as pd
import json
import os
import matplotlib.pyplot as plt

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
            data = [data]
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

def save_portfolio(portfolio):
    try:
        with open("portfolio.json", "w") as f:
            json.dump(portfolio, f, indent=4)
        st.success("¡Portfolio guardado exitosamente!")
    except Exception as e:
        st.error(f"Error guardando portfolio: {e}")

def load_portfolio():
    if os.path.exists("portfolio.json"):
        with open("portfolio.json", "r") as f:
            return json.load(f)
    return []

# ----------------------
# Código principal
# ----------------------

st.title("💵 Portfolio Tracker de Bonos")

# Cargar bonos
bonos_df = load_data()

# Inicializar portfolio en sesión
if "portfolio" not in st.session_state:
    st.session_state["portfolio"] = load_portfolio()

# Inicializar estado de inputs
if "selected_bono" not in st.session_state:
    st.session_state["selected_bono"] = ""
if "cantidad_input" not in st.session_state:
    st.session_state["cantidad_input"] = 0

# Función para agregar un bono al portfolio
def agregar_bono():
    selected_bono = st.session_state.get("selected_bono", "")
    cantidad = st.session_state.get("cantidad_input", 0)

    if selected_bono and cantidad > 0:
        precio_bono = bonos_df.loc[bonos_df["bono"] == selected_bono, "precio"].values[0]

        for item in st.session_state["portfolio"]:
            if item["Bono"] == selected_bono:
                item["Cantidad"] += cantidad
                item["Valor de la posición"] = item["Cantidad"] * item["Precio actual"]
                break
        else:
            st.session_state["portfolio"].append({
                "Bono": selected_bono,
                "Cantidad": cantidad,
                "Precio actual": precio_bono,
                "Valor de la posición": cantidad * precio_bono
            })

        # Resetear campos de entrada visualmente
        st.session_state["selected_bono"] = ""
        st.session_state["cantidad_input"] = 0
        st.success(f"{cantidad} unidades de {selected_bono} agregadas al portfolio.")
    else:
        st.warning("Por favor selecciona un bono y una cantidad mayor a 0.")

# Sidebar para agregar posiciones
st.sidebar.header("Agregar una posición")

if not bonos_df.empty:
    st.sidebar.selectbox(
        "Seleccionar Bono",
        [""] + list(bonos_df["bono"].unique()),
        key="selected_bono"
    )

    st.sidebar.number_input(
        "Cantidad de títulos",
        min_value=0,
        value=0,
        step=1,
        key="cantidad_input"
    )

    st.sidebar.button("Agregar al portfolio", on_click=agregar_bono)
else:
    st.sidebar.warning("No hay bonos cargados.")

# Opciones generales en sidebar
st.sidebar.header("Opciones del Portfolio")

if st.sidebar.button("🔄 Reiniciar Portfolio"):
    st.session_state["portfolio"] = []
    if os.path.exists("portfolio.json"):
        os.remove("portfolio.json")
    st.success("Portfolio reiniciado.")

if st.sidebar.button("💾 Guardar Portfolio"):
    save_portfolio(st.session_state["portfolio"])

# Mostrar portfolio
st.subheader("💼 Mi Portfolio")

if st.session_state["portfolio"]:
    total_valor = sum(item["Valor de la posición"] for item in st.session_state["portfolio"])

    for idx, item in enumerate(st.session_state["portfolio"]):
        with st.expander(f"{item['Bono']} - {item['Cantidad']} títulos - ${item['Valor de la posición']:,.2f}", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                nueva_cantidad = st.number_input(
                    f"Editar cantidad ({item['Bono']})",
                    min_value=0,
                    value=item['Cantidad'],
                    step=1,
                    key=f"editar_{idx}"
                )


            if st.button(f"Actualizar {item['Bono']}", key=f"update_{idx}"):
                st.session_state["portfolio"][idx]["Cantidad"] = nueva_cantidad
                st.session_state["portfolio"][idx]["Valor de la posición"] = nueva_cantidad * item["Precio actual"]
                st.experimental_rerun()  # <- fuerza el redibujo para que se actualice el título


            with col2:
                if st.button(f"🗑️ Borrar {item['Bono']}", key=f"delete_{idx}"):
                    st.session_state["portfolio"].pop(idx)
                    st.success(f"Bono {item['Bono']} eliminado del portfolio.")
                    st.experimental_rerun()

            with col3:
                st.metric(label="Valor actual", value=f"${item['Valor de la posición']:,.2f}")

    # Resumen
    st.subheader("📈 Resumen del Portfolio")
    st.metric("Valor Total del Portfolio", f"${total_valor:,.2f}")

    st.subheader("📊 Distribución del Portfolio")
    portfolio_df = pd.DataFrame(st.session_state["portfolio"])
    fig, ax = plt.subplots()
    portfolio_df.set_index('Bono')["Valor de la posición"].plot.pie(autopct='%1.1f%%', ax=ax, figsize=(6, 6))
    ax.set_ylabel("")
    st.pyplot(fig)

else:
    st.info("Todavía no agregaste bonos al portfolio.")
