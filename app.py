import streamlit as st
import pandas as pd
import math
from io import BytesIO

# Configurare vizuală interfață
st.set_page_config(page_title="Retail Dynamic Pricing", layout="wide")

st.title("🔌 Dynamic Pricing Engine - Sector Electrocasnice")
st.info("Proiect Practică - Facultatea de Informatică")

# --- SIDEBAR: LOGICA DE CAMPANIE ---
st.sidebar.header("Setări Campanii Active")
app_discount = st.sidebar.slider("Discount Aplicație (%)", 0, 30, 20)
rabla_voucher = st.sidebar.number_input("Voucher Rabla (RON)", 0, 500, 150)
min_margin = st.sidebar.slider("Marjă Minimă Profit (%)", 1, 15, 7)

# --- DATE INITIALE ---
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame([
        {"SKU": "TV-SAM-OLED", "Produs": "TV Samsung 55 OLED", "Cost": 3200, "Pret_Raft": 4800, "Stoc": 25,
         "Pret_Comp": 4700},
        {"SKU": "MS-WH-9KG", "Produs": "Mașină Spălat Whirlpool", "Cost": 1100, "Pret_Raft": 1850, "Stoc": 12,
         "Pret_Comp": 1790},
        {"SKU": "AC-GREE-12", "Produs": "Aer Condiționat 12k", "Cost": 1500, "Pret_Raft": 2300, "Stoc": 60,
         "Pret_Comp": 2250}
    ])

# --- TABEL INTERACTIV ---
st.subheader("1. Monitorizare Competitori")
edited_df = st.data_editor(st.session_state.db, num_rows="dynamic")

# --- BUTON CALCUL ---
if st.button("🚀 RULEAZĂ MOTORUL DE PREȚURI"):
    def calculate(row):
        # Vrem sa fim cu 5 RON sub competitor la pretul NET (final platit de client)
        target_net = row['Pret_Comp'] - 5

        # Ajustare stoc (Daca avem stoc mare, suntem mai agresivi)
        if row['Stoc'] > 50: target_net -= 20

        # Formula inversa pret raft
        disc_factor = 1 - (app_discount / 100)
        suggested_shelf = (target_net + rabla_voucher) / disc_factor

        # Protectie Marja
        min_net_allowed = row['Cost'] * (1 + min_margin / 100)
        actual_net = (suggested_shelf * disc_factor) - rabla_voucher

        if actual_net < min_net_allowed:
            suggested_shelf = (min_net_allowed + rabla_voucher) / disc_factor
            status = "🔴 Profit Protejat"
        else:
            status = "🟢 Optimizat"

        return round(math.floor(suggested_shelf) + 0.90, 2), status


    res = [calculate(row) for _, row in edited_df.iterrows()]
    edited_df['Pret_Nou_Raft'], edited_df['Status'] = zip(*res)

    st.session_state.db = edited_df
    st.dataframe(edited_df)

    # Grafic Impact
    st.bar_chart(edited_df.set_index('Produs')[['Pret_Raft', 'Pret_Nou_Raft']])