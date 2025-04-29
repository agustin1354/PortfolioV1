import streamlit as st
import pandas as pd
import json
import os
import matplotlib.pyplot as plt

st.set_page_config(page_title="Portfolio Tracker", page_icon="💰", layout="wide")

# ----------------------
# Funciones auxiliares
# ----------------------

@st.cache_data
def load_data(tipo):
    archivo = "bonos.json" if tipo == "BONOS" else "cedears.json"
    try:
        with open(archivo, "r") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        if tipo == "CEDEARS":
            df["precio"] = df["precio"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".").astype(float)
            df.rename(columns={"activo": "nombre"}, inplace=True)
        else:
            df.rename(columns={"bono": "nombre"}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Error cargando {archivo}: {e}")
        return pd.DataFrame(columns=["nombre", "precio"])

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

def reset_sidebar():
    """Reset sidebar inputs and rerun the app."""
    st.session_state["reset_sidebar"] = False
    st.experimental_rerun()

# ----------------------
# Inicialización
# ----------------------

st.title("💰 Portfolio Tracker")

# Ejecutar rerun si se activó el reset del sidebar
if st.session_state.get("reset_sidebar", False):
    reset_sidebar()

# Inicializar session_state si no existe
if "portfolio" not in st.session_state:
    st.session_state["portfolio"] = load_portfolio()
if "tipo_activo" not in st.session_state:
    st.session_state["tipo_activo"] = ""
if "selected_activo" not in st.session_state:
    st.session_state["selected_activo"] = ""
if "cantidad_input" not in st.session_state:
    st.session_state["cantidad_input"] = 0

# Sidebar para agregar posiciones
st.sidebar.header("Agregar una posición")

tipo_activo = st.sidebar.selectbox("Tipo de activo", [""] + ["BONOS", "CEDEARS"], key="tipo_activo")

if tipo_activo:
    activos_df = load_data(tipo_activo)
    if not activos_df.empty:
        selected_activo = st.sidebar.selectbox(
            f"Seleccionar {tipo_activo}",
            [""] + list(activos_df["nombre"].unique()),
            key="selected_activo"
        )
    else:
        st.sidebar.warning(f"No se encontraron activos para {tipo_activo}.")
        selected_activo = ""
else:
    activos_df = pd.DataFrame()
    selected_activo = ""

cantidad = st.sidebar.number_input(
    "Cantidad de títulos",
    min_value=0,
    value=st.session_state["cantidad_input"],
    step=1,
    key="cantidad_input"
)

if st.sidebar.button("Agregar al portfolio"):
    if tipo_activo and selected_activo and cantidad > 0:
        try:
            precio = activos_df.loc[activos_df["nombre"] == selected_activo, "precio"].values[0]
            encontrado = False
            for item in st.session_state["portfolio"]:
                if item["Activo"] == selected_activo and item["Tipo"] == tipo_activo:
                    item["Cantidad"] += cantidad
                    item["Valor de la posición"] = item["Cantidad"] * item["Precio actual"]
                    encontrado = True
                    break
            if not encontrado:
                st.session_state["portfolio"].append({
                    "Activo": selected_activo,
                    "Tipo": tipo_activo,
                    "Cantidad": cantidad,
                    "Precio actual": precio,
                    "Valor de la posición": cantidad * precio
                })
            # Resetear inputs
            reset_sidebar()
        except IndexError:
            st.error("Error al obtener el precio del activo seleccionado.")
    else:
        st.warning("Seleccioná un tipo de activo, un activo y una cantidad mayor a 0.")

# Sidebar opciones generales
st.sidebar.header("Opciones del Portfolio")
if st.sidebar.button("🔄 Reiniciar Portfolio"):
    st.session_state["portfolio"] = []
    if os.path.exists("portfolio.json"):
        os.remove("portfolio.json")
    st.success("Portfolio reiniciado.")
    reset_sidebar()

if st.sidebar.button("💾 Guardar Portfolio"):
    save_portfolio(st.session_state["portfolio"])

# ----------------------
# Mostrar Portfolio
# ----------------------

st.subheader("📂 Mi Portfolio")

if st.session_state["portfolio"]:
    total_valor = sum(item["Valor de la posición"] for item in st.session_state["portfolio"])

    for idx, item in enumerate(st.session_state["portfolio"]):
        with st.expander(f"{item['Tipo']} - {item['Activo']} - {item['Cantidad']} títulos - ${item['Valor de la posición']:,.2f}", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                nueva_cantidad = st.number_input(
                    f"Editar cantidad ({item['Activo']})",
                    min_value=0,
                    value=item['Cantidad'],
                    step=1,
                    key=f"editar_{idx}"
                )
                if st.button(f"Actualizar {item['Activo']}", key=f"update_{idx}"):
                    item["Cantidad"] = nueva_cantidad
                    item["Valor de la posición"] = nueva_cantidad * item["Precio actual"]
                    reset_sidebar()

            with col2:
                if st.button(f"🗑️ Borrar {item['Activo']}", key=f"delete_{idx}"):
                    st.session_state["portfolio"].pop(idx)
                    reset_sidebar()

            with col3:
                st.metric(label="Valor actual", value=f"${item['Valor de la posición']:,.2f}")

    # Total del Portfolio
    st.subheader("📈 Resumen del Portfolio")
    st.metric("Valor Total del Portfolio", f"${total_valor:,.2f}")

    # Gráfico de distribución
    portfolio_df = pd.DataFrame(st.session_state["portfolio"])
    if not portfolio_df.empty:
        fig, ax = plt.subplots()
        portfolio_df.set_index('Activo')["Valor de la posición"].plot.pie(autopct='%1.1f%%', ax=ax, figsize=(6, 6))
        ax.set_ylabel("")
        st.pyplot(fig)

else:
    st.info("Todavía no agregaste activos al portfolio.")
