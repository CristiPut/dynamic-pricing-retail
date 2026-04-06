import streamlit as st
import pandas as pd
import math
import os
import re

# --- CONFIGURARE PAGINĂ ---
st.set_page_config(page_title="Retail Dynamic Pricing - Catalog Live", layout="wide")

# --- FUNCȚIE REZISTENTĂ LA ERORI PENTRU CITIRE C.TXT ---
@st.cache_data
def load_data_robust(file_name):
    catalog = []
    if not os.path.exists(file_name):
        return []
    
    with open(file_name, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            # Folosim Regex pentru a separa după Tab sau minim 2 spații consecutive
            parts = re.split(r'\t| {2,}', line)
            
            if len(parts) >= 3:
                try:
                    sku = parts[0].strip()
                    nume = parts[1].strip()
                    # Curățăm prețul: eliminăm "RON", puncte (mii) și convertim virgula în punct
                    raw_price = parts[2].upper().replace('RON', '').replace('.', '').replace(',', '.').strip()
                    pret = float(raw_price)
                    
                    catalog.append({"SKU": sku, "Produs": nume, "Pret_Altex": pret})
                except:
                    continue
    return catalog

# Încărcăm datele
data = load_data_robust("c.txt")

st.title("🔌 Dynamic Pricing Engine - Full Inventory")

if data:
    st.success(f"✅ Catalog activat: {len(data)} produse încărcate din c.txt")
else:
    st.error("⚠️ Atenție: Nu s-au putut extrage datele. Asigură-te că c.txt are: Cod [Spațiu/Tab] Nume [Spațiu/Tab] Preț")

# --- SIDEBAR: STRATEGIE ---
st.sidebar.header("⚙️ Parametri Campanii")
app_discount = st.sidebar.slider("Discount Aplicație (%)", 0, 30, 20)
rabla_voucher = st.sidebar.number_input("Voucher Rabla (RON)", 0, 500, 150)
min_margin = st.sidebar.slider("Marjă Minimă Profit (%)", 1, 15, 7)

# --- SELECTOR ȘI ANALIZĂ ---
if data:
    options = [f"[{p['SKU']}] {p['Produs']}" for p in data]
    selected_option = st.selectbox("Selectează produsul:", options)

    if st.button("➕ Adaugă în Tabel Monitorizare"):
        sku_clean = selected_option.split(']')[0][1:]
        info = next(item for item in data if item["SKU"] == sku_clean)
        
        # Simulare cost (80% din preț competitor)
        cost_simulat = round(info["Pret_Altex"] * 0.80, 2)
        
        new_row = {
            "SKU": info["SKU"],
            "Produs": info["Produs"],
            "Cost": cost_simulat,
            "Pret_Altex": info["Pret_Altex"],
            "Pret_Raft_Actual": round(info["Pret_Altex"] + 35, 2)
        }
        
        if 'df_monitor' not in st.session_state:
            st.session_state.df_monitor = pd.DataFrame([new_row])
        else:
            if new_row["SKU"] not in st.session_state.df_monitor["SKU"].values:
                st.session_state.df_monitor = pd.concat([st.session_state.df_monitor, pd.DataFrame([new_row])], ignore_index=True)

if 'df_monitor' in st.session_state and not st.session_state.df_monitor.empty:
    st.markdown("---")
    edited_df = st.data_editor(st.session_state.df_monitor, num_rows="dynamic", use_container_width=True)
    st.session_state.df_monitor = edited_df

    if st.button("🚀 CALCULEAZĂ PREȚURI"):
        res_prices = []
        res_status = []
        for _, row in edited_df.iterrows():
            target_net = row['Pret_Altex'] - 5
            f_app = 1 - (app_discount / 100)
            shelf_p = (target_net + rabla_voucher) / f_app
            
            min_net = row['Cost'] * (1 + min_margin / 100)
            actual_net = (shelf_p * f_app) - rabla_voucher
            
            if actual_net < min_net:
                shelf_p = (min_net + rabla_voucher) / f_app
                status = "🔴 Profit Protejat"
            else:
                status = "🟢 Optimizat"
            
            res_prices.append(round(math.floor(shelf_p) + 0.90, 2))
            res_status.append(status)
        
        edited_df['Pret_Nou_Raft'], edited_df['Status'] = res_prices, res_status
        st.dataframe(edited_df, use_container_width=True)
        st.bar_chart(edited_df.set_index('SKU')[['Pret_Altex', 'Pret_Nou_Raft']])
