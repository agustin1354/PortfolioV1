import streamlit as st
import pandas as pd
import asyncio
from playwright.async_api import async_playwright
import matplotlib.pyplot as plt

st.set_page_config(page_title="Portfolio de Bonos", page_icon="💰", layout="centered")

# -------- Scraping Function --------
async def scrape():
    data = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://iol.invertironline.com/mercado/cotizaciones/argentina/bonos/todos")
        await page.wait_for_load_state("networkidle")
        for page_num in range(1, 4):
            await page.wait_for_selector("table")
            rows = await page.locator("table tbody tr").all()
            for row in rows:
                cols = await row.locator("td").all_inner_texts()
                if len(cols) >= 2:
                    nombre = cols[0].strip()
                    precio = cols[1].strip().replace(".", "").replace(",", ".")
                    try:
                        precio = float(precio)
                        data.append({"Bono": nombre, "Precio": precio})
                    except ValueError:
                        continue
            if page_num < 3:
                next_button = page.locator(".dataTables_paginate .paginate_button.next:not(.disabled)")
                if await next_button.is_visible():
                    await next_button.click()
                    await page.wait_for_load_state("networkidle")
                else:
                    break
        await browser.close()
    return pd.DataFrame(data)

@st.cache_resource
def load_data():
    return asyncio.run(scrape())

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


