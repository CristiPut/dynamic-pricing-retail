import streamlit as st
import pandas as pd
import math
import os
import re

# --- CONFIGURARE PAGINĂ ---
st.set_page_config(page_title="Retail Dynamic Pricing - Catalog Altex", layout="wide")

# --- FUNCȚIE DE CITIRE ROBUSTĂ (PENTRU FORMATUL TAB) ---
@st.cache_data
def load_data_from_catalog(file_name):
    catalog = []
    if not os.path.exists(file_name):
        return []
    
    with open(file_name, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue  # Sărim peste liniile goale
            
            # Împărțim linia după TAB (\t) sau minim 2 spații consecutive
            parts = re.split(r'\t| {2,}', line)
            
            if len(parts) >= 3:
                try:
                    sku = parts[0].strip()
                    nume = parts[1].strip()
                    # Curățăm prețul de orice caracter care nu e cifră sau punct
                    raw_price = parts[2].replace('RON', '').replace(' ', '').replace(',', '.').strip()
                    pret = float(raw_price)
                    
                    catalog.append({
                        "SKU": sku, 
                        "Produs": nume, 
                        "Pret_Altex": pret
                    })
                except:
                    continue # Dacă un rând e greșit, trecem la următorul
    return catalog

# 1. Încărcăm datele din c.txt
data = load_data_from_catalog("c.txt")

st.title("📊 Pricing Engine - Gestiune Catalog Complet")

if data:
    st.success(f"✅ S-au încărcat {len(data)} produse din baza de date c.txt")
else:
    st.error("⚠️ Eroare: Fișierul c.txt nu a fost găsit sau este gol.")

# --- SIDEBAR: STRATEGIE COMERCIALĂ ---
st.sidebar.header("⚙️ Setări Campanii")
app_discount = st.sidebar.slider("Discount Aplicație (%)", 0, 30, 20)
rabla_voucher = st.sidebar.number_input("Voucher Rabla (RON)", 0, 500, 150)
min_margin = st.sidebar.slider("Marjă Minimă Profit (%)", 1, 15, 7)

# --- LOGICĂ SELECȚIE PRODUSE ---
if data:
    st.subheader("🔎 Selector Produse")
    # Creăm o listă de selecție formată din SKU și Nume
    options = [f"[{p['SKU']}] {p['Produs']}" for p in data]
    selected_option = st.selectbox("Caută și adaugă produse în lista de monitorizare:", options)

    if st.button("➕ Adaugă în Tabel"):
        # Extragem SKU-ul dintre paranteze
        sku_clean = selected_option.split(']')[0][1:]
        info = next(item for item in data if item["SKU"] == sku_clean)
        
        # Simulare cost achiziție (WAC) - aprox 78% din preț
        cost_simulat = round(info["Pret_Altex"] * 0.78, 2)
        
        new_row = {
            "SKU": info["SKU"],
            "Produs": info["Produs"],
            "Cost_Achizitie": cost_simulat,
            "Pret_Altex": info["Pret_Altex"],
            "Stoc_Depozit": 15
        }
        
        if 'df_monitor' not in st.session_state:
            st.session_state.df_monitor = pd.DataFrame([new_row])
        else:
            # Evităm duplicatele în tabel
            if new_row["SKU"] not in st.session_state.df_monitor["SKU"].values:
                st.session_state.df_monitor = pd.concat([st.session_state.df_monitor, pd.DataFrame([new_row])], ignore_index=True)

# --- DASHBOARD CALCUL ȘI AFIȘARE ---
if 'df_monitor' in st.session_state and not st.session_state.df_monitor.empty:
    st.markdown("---")
    st.subheader("📋 Analiză Prețuri la Raft")
    
    # Permitem editarea costului sau stocului direct în tabel
    edited_df = st.data_editor(st.session_state.df_monitor, num_rows="dynamic", use_container_width=True)
    st.session_state.df_monitor = edited_df

    if st.button("🚀 EXECUTĂ RE-PRICING"):
        res_prices = []
        res_status = []
        
        for _, row in edited_df.iterrows():
            # Strategie: Vrem să fim cu 5 lei sub Altex la prețul final plătit de client
            target_net = row['Pret_Altex'] - 5
            
            # Formula inversă pentru calculul prețului de etichetă (Shelf Price)
            # Ținem cont de discountul de aplicație și de Rabla
            factor_app = 1 - (app_discount / 100)
            suggested_shelf = (target_net + rabla_voucher) / factor_app
            
            # Verificare marjă de siguranță
            min_net_allowed = row['Cost_Achizitie'] * (1 + min_margin / 100)
            actual_net = (suggested_shelf * factor_app) - rabla_voucher
            
            if actual_net < min_net_allowed:
                # Dacă pierdem bani, forțăm prețul minim care să acopere marja
                suggested_shelf = (min_net_allowed + rabla_voucher) / factor_app
                status = "🔴 Marjă Protejată"
            else:
                status = "🟢 Competitiv"
            
            # Rotunjire psihologică .90
            final_p = round(math.floor(suggested_shelf) + 0.90, 2)
            res_prices.append(final_p)
            res_status.append(status)
        
        edited_df['Pret_Nou_Eticheta'] = res_prices
        edited_df['Status_Profit'] = res_status
        
        st.dataframe(edited_df, use_container_width=True)
        
        # Vizualizare grafică a diferențelor
        st.bar_chart(edited_df.set_index('SKU')[['Pret_Altex', 'Pret_Nou_Eticheta']])
