import streamlit as st
from streamlit_jsevents import jsevents  # Necesitas instalar: pip install streamlit-jsevents
import pandas as pd
import json
import os
import matplotlib.pyplot as plt

st.set_page_config(page_title="Portfolio Tracker", page_icon="💰", layout="wide")

# ----------------------
# Funciones auxiliares
# ----------------------

def load_json_file(archivo):
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
    st.session_state["tipo_activo"] = ""
    st.session_state["selected_activo"] = ""
    st.session_state["cantidad_input"] = 0

def update_portfolio_values(portfolio, bonos_df, cedears_df):
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
# Inicialización de estados
# ----------------------

if "initialized" not in st.session_state:
    st.session_state["portfolio"] = load_portfolio()
    st.session_state["tipo_activo"] = ""
    st.session_state["selected_activo"] = ""
    st.session_state["cantidad_input"] = 0
    st.session_state["eliminar_activos"] = []
    st.session_state["initialized"] = True

# Cargar datos si no están en caché
if "cached_bonos" not in st.session_state:
    st.session_state.cached_bonos = load_data("BONOS")
if "cached_cedears" not in st.session_state:
    st.session_state.cached_cedears = load_data("CEDEARS")

# ----------------------
# Sidebar - Agregar posiciones
# ----------------------

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
# Mostrar Portfolio con edición automática
# ----------------------

st.title("📁 Mi Portfolio")

if st.session_state["portfolio"]:
    st.session_state["portfolio"] = update_portfolio_values(
        st.session_state["portfolio"],
        st.session_state.cached_bonos,
        st.session_state.cached_cedears
    )

    portfolio_df = pd.DataFrame(st.session_state["portfolio"])
    tipos_grupos = portfolio_df.groupby("Tipo")

    st.session_state["eliminar_activos"] = []

    # Estilo CSS
    html_style = """
    <style>
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            text-align: center;
            font-family: Arial, sans-serif;
            margin-bottom: 16px;
        }
        .styled-table th, .styled-table td {
            padding: 10px;
            border: 1px solid #ddd;
            text-align: center;
        }
        .styled-table th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .checkbox-column {
            width: 80px;
        }
        .activo-column {
            width: 200px;
        }
        .cantidad-column {
            width: 100px;
        }
        .precio-column, .valor-column {
            width: 120px;
        }
        input[type="number"] {
            width: 80px;
            text-align: center;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 4px;
        }
    </style>
    """
    st.markdown(html_style, unsafe_allow_html=True)

    for tipo_activo, grupo in tipos_grupos:
        st.markdown(f"### {tipo_activo}")
        grupo = grupo.reset_index(drop=True)

        grupo["Seleccionar"] = False
        grupo["ID"] = grupo.index

        html_table = "<table class='styled-table'><thead><tr>"
        html_table += "<th class='checkbox-column'>Eliminar</th>"
        html_table += "<th class='activo-column'>Activo</th>"
        html_table += "<th class='cantidad-column'>Cantidad</th>"
        html_table += "<th class='precio-column'>Precio Actual</th>"
        html_table += "<th class='valor-column'>Valor</th>"
        html_table += "</tr></thead><tbody>"

        for idx, row in grupo.iterrows():
            activo = row["Activo"]
            cantidad_id = f"{tipo_activo}_{idx}"
            checkbox_id = f"chk_{tipo_activo}_{idx}"

            html_table += f"""
                <tr>
                    <td><input type="checkbox" id="{checkbox_id}" /></td>
                    <td>{activo}</td>
                    <td><input type="number" id="{cantidad_id}" value="{int(row['Cantidad'])}" min="0" onkeydown="handleKey(event, '{cantidad_id}', '{activo}', '{tipo_activo}')" onblur="handleBlur('{cantidad_id}', '{activo}', '{tipo_activo}')"></td>
                    <td>${row['Precio actual']:.2f}</td>
                    <td>${row['Valor de la posición']:.2f}</td>
                </tr>
            """

        html_table += "</tbody></table>"
        html_script = """
        <script>
            function handleKey(e, id, activo, tipo) {
                if (e.key === 'Enter') {
                    const val = document.getElementById(id).value;
                    Streamlit.events.emit('customEvent', {
                        type: 'update',
                        payload: { id, activo, tipo, cantidad: parseInt(val) }
                    });
                }
            }

            function handleBlur(id, activo, tipo) {
                const val = document.getElementById(id).value;
                Streamlit.events.emit('customEvent', {
                    type: 'update',
                    payload: { id, activo, tipo, cantidad: parseInt(val) }
                });
            }

            function collectDeletes() {
                const checks = document.querySelectorAll("input[type='checkbox']");
                let deletes = [];
                checks.forEach(chk => {
                    if (chk.checked && chk.id.startsWith("chk_")) {
                        const parts = chk.id.split("_");
                        deletes.push({ tipo: parts[1], activo: parts.slice(2).join("_") });
                    }
                });
                Streamlit.events.emit('customEvent', {
                    type: 'delete',
                    payload: deletes
                });
            }
        </script>
        <button onclick="collectDeletes()" style="margin-top: 10px;">🗑️ Eliminar Seleccionados</button>
        """
        jsevents(html=html_table + html_script)

    total_valor = portfolio_df["Valor de la posición"].sum()

    st.markdown("---")
    st.markdown("### 📈 Resumen del Portfolio")
    st.metric("Valor Total del Portfolio", f"${total_valor:,.2f}")

    fig, ax = plt.subplots(figsize=(8, 6))
    portfolio_df.set_index('Activo')["Valor de la posición"].plot.pie(
        autopct='%1.1f%%', ax=ax, startangle=90, textprops={'fontsize': 10}
    )
    ax.set_ylabel("")
    ax.set_title("Distribución del Valor del Portfolio")
    st.pyplot(fig)

else:
    st.info("📦 Todavía no agregaste activos al portfolio.")

# ----------------------
# Manejo de eventos JS
# ----------------------

if "event" in st.query_params:
    event = st.query_params["event"]
    payload = json.loads(st.query_params["payload"])

    if event == "update":
        for item in st.session_state["portfolio"]:
            if item["Activo"] == payload["activo"] and item["Tipo"] == payload["tipo"]:
                item["Cantidad"] = int(payload["cantidad"])
                item["Valor de la posición"] = round(item["Cantidad"] * item["Precio actual"], 2)
        st.rerun()

    elif event == "delete":
        eliminar_lista = payload
        if eliminar_lista:
            st.session_state["portfolio"] = [
                item for item in st.session_state["portfolio"]
                if not any(
                    elim["activo"] == item["Activo"] and elim["tipo"] == item["Tipo"]
                    for elim in eliminar_lista
                )
            ]
            st.success("🗑️ Activos seleccionados eliminados.")
            st.rerun()
