import streamlit as st
import pandas as pd
import math
import os

# --- CONFIGURARE PAGINĂ ---
st.set_page_config(page_title="Retail Dynamic Pricing - Baza de Date Live", layout="wide")

# --- FUNCȚIE PENTRU CITIREA CATALOGULUI DIN C.TXT ---
@st.cache_data
def load_data_from_txt(file_name):
    catalog = []
    if not os.path.exists(file_name):
        return []
    
    with open(file_name, "r", encoding="utf-8") as f:
        for line in f:
            # Separăm coloanele (Excel folosește de obicei Tab/spațiu mare)
            parts = line.strip().split('\t')
            if len(parts) < 3:
                # Încercăm și după spații multiple dacă Tab nu merge
                parts = [p.strip() for p in line.split('   ') if p.strip()]
            
            if len(parts) >= 3:
                try:
                    sku = parts[0]
                    nume = parts[1]
                    # Curățăm prețul de "RON", puncte de mii sau virgule
                    raw_price = parts[2].replace('RON', '').replace('.', '').replace(',', '.').strip()
                    pret = float(raw_price)
                    
                    catalog.append({
                        "SKU": sku,
                        "Produs": nume,
                        "Pret_Altex": pret
                    })
                except:
                    continue
    return catalog

# Încărcăm produsele
data = load_data_from_txt("c.txt")

st.title("🔌 Dynamic Pricing Engine - Full Inventory")
if data:
    st.success(f"✅ S-au încărcat cu succes {len(data)} produse din fișierul c.txt!")
else:
    st.error("❌ Nu am putut citi datele din c.txt. Verifică formatul fișierului.")

# --- SIDEBAR: STRATEGIE COMERCIALĂ ---
st.sidebar.header("⚙️ Parametri Campanii")
app_discount = st.sidebar.slider("Discount Aplicație (%)", 0, 30, 20)
rabla_voucher = st.sidebar.number_input("Voucher Rabla (RON)", 0, 500, 150)
min_margin = st.sidebar.slider("Marjă Minimă Profit (%)", 1, 15, 7)

# --- SELECTOR DIN CATALOG ---
if data:
    st.subheader("🔎 Căutare și Selectare Produse")
    options = [f"[{p['SKU']}] {p['Produs']}" for p in data]
    selected_option = st.selectbox("Alege produsul pentru monitorizare:", options)

    if st.button("➕ Adaugă în Analiză"):
        # Extragem SKU-ul din selecție
        selected_sku = selected_option.split(']')[0][1:]
        info = next(item for item in data if item["SKU"] == selected_sku)
        
        # Simulare cost (80% din preț competitor)
        cost_simulat = round(info["Pret_Altex"] * 0.80, 2)
        
        new_row = {
            "SKU": info["SKU"],
            "Produs": info["Produs"],
            "Cost": cost_simulat,
            "Pret_Altex": info["Pret_Altex"],
            "Stoc": 10
        }
        
        if 'df_monitor' not in st.session_state:
            st.session_state.df_monitor = pd.DataFrame([new_row])
        else:
            if new_row["SKU"] not in st.session_state.df_monitor["SKU"].values:
                st.session_state.df_monitor = pd.concat([st.session_state.df_monitor, pd.DataFrame([new_row])], ignore_index=True)

# --- TABEL ȘI CALCULE ---
if 'df_monitor' in st.session_state and not st.session_state.df_monitor.empty:
    st.markdown("---")
    st.subheader("📊 Dashboard Monitorizare")
    
    edited_df = st.data_editor(st.session_state.df_monitor, num_rows="dynamic", use_container_width=True)
    st.session_state.df_monitor = edited_df

    if st.button("🚀 RULEAZĂ CALCUL DINAMIC"):
        results = []
        for _, row in edited_df.iterrows():
            # Target: Competitivitate (-5 RON față de Altex)
            target_net = row['Pret_Altex'] - 5
            
            # Formula inversă pentru prețul de raft
            f_app = 1 - (app_discount / 100)
            suggested_shelf = (target_net + rabla_voucher) / f_app
            
            # Verificare profitabilitate
            min_net = row['Cost'] * (1 + min_margin / 100)
            actual_net = (suggested_shelf * f_app) - rabla_voucher
            
            if actual_net < min_net:
                suggested_shelf = (min_net + rabla_voucher) / f_app
                status = "🔴 Profit Protejat"
            else:
                status = "🟢 Optimizat"
                
            results.append((round(math.floor(suggested_shelf) + 0.90, 2), status))
        
        edited_df['Pret_Nou_Raft'], edited_df['Status'] = zip(*results)
        st.dataframe(edited_df, use_container_width=True)
        st.bar_chart(edited_df.set_index('SKU')[['Pret_Altex', 'Pret_Nou_Raft']])
