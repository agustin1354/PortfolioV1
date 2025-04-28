import os
os.system('playwright install chromium')
import streamlit as st
import pandas as pd
import asyncio
from playwright.async_api import async_playwright

# Función de scraping
@st.cache_data(ttl=3600)  # cachea por 1 hora
def scrape_bonos():
    async def scrape():
        all_data = []
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
                        precio = cols[1].replace(",", ".").strip()
                        try:
                            precio = float(precio)
                            all_data.append((nombre, precio))
                        except ValueError:
                            continue
                if page_num < 3:
                    next_page_locator = page.locator(".dataTables_paginate .paginate_button.next:not(.disabled)")
                    if await next_page_locator.is_visible():
                        await next_page_locator.click()
                        await page.wait_for_load_state("networkidle")
                    else:
                        break
            await browser.close()
        return all_data
    
    bonos = asyncio.run(scrape())
    df = pd.DataFrame(bonos, columns=["Bono", "Último Precio"])
    return df

# Título
st.title("💵 Calculadora de Bonos - IOL")

# Botón para actualizar los bonos
if st.button("🔄 Actualizar Bonos"):
    st.cache_data.clear()
    st.experimental_rerun()

# Obtener los bonos
df_bonos = scrape_bonos()

if not df_bonos.empty:
    # Dropdown para seleccionar bono
    bono_seleccionado = st.selectbox("Selecciona un bono:", df_bonos["Bono"])

    # Mostrar precio
    precio_bono = df_bonos[df_bonos["Bono"] == bono_seleccionado]["Último Precio"].values[0]
    st.write(f"💲 Último precio: {precio_bono:.2f}")

    # Input de cantidad
    cantidad = st.number_input("Cantidad de bonos:", min_value=1, value=1)

    # Calcular total
    total = precio_bono * cantidad
    st.success(f"💰 Total: {total:.2f}")
else:
    st.warning("No se encontraron bonos. Intenta actualizar.")
