import streamlit as st
import pandas as pd
import json
import os
import matplotlib.pyplot as plt

st.set_page_config(page_title="Portfolio Tracker", page_icon="💰", layout="wide")

# ----------------------
# Funciones auxiliares
# ----------------------

def load_json_file(archivo):
    """Carga un archivo JSON y maneja errores."""
    try:
        if not os.path.exists(archivo):
            st.error(f"No se encontró el archivo {archivo}.")
            return []
        with open(archivo, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error cargando {archivo}: {e}")
        return []

def process_bonos_data(data):
    df = pd.DataFrame(data)
    df.rename(columns={"bono": "nombre"}, inplace=True)
    return df[["nombre", "precio"]]

def process_cedears_data(data):
    df = pd.DataFrame(data)
    df["precio"] = (
        df["precio"].astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".")
        .astype(float)
    )
    df.rename(columns={"activo": "nombre"}, inplace=True)
    return df[["nombre", "precio"]]

def load_data(tipo):
    archivo = "bonos.json" if tipo == "BONOS" else "cedears.json"
    data = load_json_file(archivo)

    if tipo == "CEDEARS":
        return process_cedears_data(data)
    else:
        return process_bonos_data(data)

def save_portfolio(portfolio):
    try:
        with open("portfolio.json", "w") as f:
            json.dump(portfolio, f, indent=4)
        st.toast("✅ ¡Portfolio guardado exitosamente!")
    except Exception as e:
        st.error(f"❌ Error guardando portfolio: {e}")

def load_portfolio():
    if os.path.exists("portfolio.json"):
        with open("portfolio.json", "r") as f:
            return json.load(f)
    return []

def reset_sidebar():
    """Reinicia campos del sidebar para nueva entrada."""
    st.session_state["tipo_activo"] = ""
    st.session_state["selected_activo"] = ""
    st.session_state["cantidad_input"] = 0

def update_portfolio_values(portfolio, bonos_df, cedears_df):
    """Recalcula los valores del portfolio con precios actualizados."""
    for item in portfolio:
        if item["Tipo"] == "BONOS" and bonos_df is not None:
            row = bonos_df[bonos_df["nombre"] == item["Activo"]]
        elif item["Tipo"] == "CEDEARS" and cedears_df is not None:
            row = cedears_df[cedears_df["nombre"] == item["Activo"]]
        else:
            continue

        if not row.empty:
            item["Precio actual"] = float(row["precio"].values[0])
            item["Valor de la posición"] = round(item["Cantidad"] * item["Precio actual"], 2)
    return portfolio

# ----------------------
# Inicialización de estados (una sola vez)
# ----------------------

if "initialized" not in st.session_state:
    st.session_state["portfolio"] = load_portfolio()
    st.session_state["tipo_activo"] = ""
    st.session_state["selected_activo"] = ""
    st.session_state["cantidad_input"] = 0
    st.session_state["eliminar_activos"] = []
    st.session_state["initialized"] = True

# Cargar datos al inicio si no están en caché
if "cached_bonos" not in st.session_state:
    st.session_state.cached_bonos = load_data("BONOS")
if "cached_cedears" not in st.session_state:
    st.session_state.cached_cedears = load_data("CEDEARS")

# Ejecutar reinicio seguro del sidebar si es necesario
if st.session_state.get("reset_sidebar", False):
    reset_sidebar()
    st.session_state.reset_sidebar = False

# ----------------------
# UI Principal
# ----------------------

st.title("💰 Portfolio Tracker")

# Sidebar - Agregar posiciones
with st.sidebar:
    st.header("➕ Agregar una posición")

    tipo_activo = st.selectbox(
        "Tipo de activo",
        ["", "BONOS", "CEDEARS"],
        key="tipo_activo"
    )

    if tipo_activo:
        activos_df = st.session_state.cached_bonos if tipo_activo == "BONOS" else st.session_state.cached_cedears
        selected_activo = st.selectbox(
            f"Seleccionar {tipo_activo}",
            [""] + list(activos_df["nombre"].unique()),
            key="selected_activo"
        )
    else:
        selected_activo = ""

    cantidad = st.number_input(
        "Cantidad de títulos",
        min_value=0,
        value=st.session_state.get("cantidad_input", 0),
        step=1,
        key="cantidad_input"
    )

    if st.button("Agregar al portfolio", use_container_width=True):
        if tipo_activo and selected_activo and cantidad > 0:
            df = st.session_state.cached_bonos if tipo_activo == "BONOS" else st.session_state.cached_cedears
            if selected_activo not in df["nombre"].values:
                st.error("❌ Activo seleccionado no encontrado.")
            else:
                precio = df[df["nombre"] == selected_activo]["precio"].values[0]
                encontrado = False
                for item in st.session_state["portfolio"]:
                    if item["Activo"] == selected_activo and item["Tipo"] == tipo_activo:
                        item["Cantidad"] += cantidad
                        item["Valor de la posición"] = round(item["Cantidad"] * item["Precio actual"], 2)
                        encontrado = True
                        break
                if not encontrado:
                    st.session_state["portfolio"].append({
                        "Activo": selected_activo,
                        "Tipo": tipo_activo,
                        "Cantidad": cantidad,
                        "Precio actual": precio,
                        "Valor de la posición": round(cantidad * precio, 2)
                    })
                st.session_state.reset_sidebar = True
                st.toast("✅ ¡Activo agregado correctamente!")
        else:
            st.warning("⚠️ Seleccione todos los campos.")

    st.markdown("---")
    st.header("⚙️ Opciones del Portfolio")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Limpiar"):
            st.session_state["portfolio"] = []
            if os.path.exists("portfolio.json"):
                os.remove("portfolio.json")
            st.toast("🗑️ Portfolio borrado.")
            st.session_state.reset_sidebar = True
    with col2:
        if st.button("📂 Guardar"):
            save_portfolio(st.session_state["portfolio"])

# ----------------------
# Mostrar Portfolio - Versión Tabla Agrupada + Edición Automática + Múltiples Eliminaciones
# ----------------------

st.subheader("📁 Mi Portfolio")

if st.session_state["portfolio"]:
    # Actualizar valores del portfolio con precios actuales
    st.session_state["portfolio"] = update_portfolio_values(
        st.session_state["portfolio"],
        st.session_state.cached_bonos,
        st.session_state.cached_cedears
    )

    # Convertir a DataFrame
    portfolio_df = pd.DataFrame(st.session_state["portfolio"])

    # Calcular total
    total_valor = portfolio_df["Valor de la posición"].sum()

    # Agrupar por tipo de activo
    tipos_grupos = portfolio_df.groupby("Tipo")

    # Variable temporal para guardar IDs a eliminar
    st.session_state["eliminar_activos"] = []

    # Mostrar cada grupo en su propia tabla
    for tipo_activo, grupo in tipos_grupos:
        st.markdown(f"### {tipo_activo}")
        grupo = grupo.reset_index(drop=True)

        # Añadir columna de selección y ocultar índice
        grupo["Seleccionar"] = False

        # Usamos st.data_editor con edición automática
        edited_df = st.data_editor(
            grupo[["Seleccionar", "Activo", "Cantidad", "Precio actual", "Valor de la posición"]],
            column_config={
                "Seleccionar": st.column_config.CheckboxColumn("Eliminar"),
                "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=0, step=1),
                "Precio actual": st.column_config.NumberColumn("Precio actual", disabled=True),
                "Valor de la posición": st.column_config.NumberColumn("Valor", disabled=True)
            },
            hide_index=True,
            key=f"editor_{tipo_activo}",
            on_change=None,
            use_container_width=True,
            num_rows="fixed"
        )

        # Actualizar automáticamente si cambia alguna cantidad
        original_grupo = grupo[["Activo", "Cantidad"]]
        edited_grupo = edited_df[["Activo", "Cantidad"]]

        # Detectar cambios en las cantidades
        cambios = original_grupo.merge(edited_grupo, on="Activo", how="inner", suffixes=("_old", "_new"))
        cambios = cambios[cambios["Cantidad_old"] != cambios["Cantidad_new"]]

        for _, row in cambios.iterrows():
            for item in st.session_state["portfolio"]:
                if item["Activo"] == row["Activo"]:
                    item["Cantidad"] = int(row["Cantidad_new"])
                    item["Valor de la posición"] = round(item["Cantidad"] * item["Precio actual"], 2)

        # Guardar los activos seleccionados para eliminar
        seleccionados = edited_df[edited_df["Seleccionar"]]["Activo"].tolist()
        st.session_state["eliminar_activos"] += [
            {"Tipo": tipo_activo, "Activo": activo} for activo in seleccionados
        ]

    # Botón para eliminar todos los seleccionados
    if st.button("🗑️ Eliminar Seleccionados", type="primary", use_container_width=True):
        eliminar_lista = st.session_state["eliminar_activos"]
        if eliminar_lista:
            st.session_state["portfolio"] = [
                item for item in st.session_state["portfolio"]
                if not any(
                    elim["Activo"] == item["Activo"] and elim["Tipo"] == item["Tipo"]
                    for elim in eliminar_lista
                )
            ]
            st.session_state["eliminar_activos"] = []
            st.success("🗑️ Activos seleccionados eliminados.")
            st.rerun()
        else:
            st.warning("⚠️ No hay activos seleccionados para eliminar.")

    # Resumen del Portfolio
    st.markdown("---")
    st.markdown("### 📈 Resumen del Portfolio")
    st.metric("Valor Total del Portfolio", f"${total_valor:,.2f}")

    # Gráfico de distribución
    fig, ax = plt.subplots(figsize=(8, 6))
    portfolio_df.set_index('Activo')["Valor de la posición"].plot.pie(
        autopct='%1.1f%%', ax=ax, startangle=90, textprops={'fontsize': 10}
    )
    ax.set_ylabel("")
    ax.set_title("Distribución del Valor del Portfolio")
    st.pyplot(fig)

else:
    st.info("📦 Todavía no agregaste activos al portfolio.")
