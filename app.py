# app.py

import streamlit as st
import json

# 📦 Cargar bonos
with open('bonos.json', 'r') as f:
    bonos = json.load(f)

# 📋 Armar lista de opciones
opciones_bonos = [item['bono'] for item in bonos]

st.title("Calculadora de Bonos 🇦🇷")

# 🧩 Selección de bono
bono_seleccionado = st.selectbox("Seleccioná un bono:", opciones_bonos)

# 🔍 Buscar precio del bono seleccionado
precio_bono = next((item['precio'] for item in bonos if item['bono'] == bono_seleccionado), None)

# ✍️ Ingresar cantidad
cantidad = st.number_input("Cantidad:", min_value=1, step=1)

# 💵 Mostrar precio
if precio_bono is not None:
    st.write(f"**Precio actual del bono:** ${precio_bono:.2f}")

    # 🧮 Calcular total
    total = cantidad * precio_bono
    st.write(f"**Valor total:** ${total:.2f}")
else:
    st.error("No se encontró precio para este bono.")
