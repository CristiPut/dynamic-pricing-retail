import streamlit as st
import pandas as pd
import math
import os
import re

st.set_page_config(
    page_title="Retail Dynamic Pricing - Catalog Altex", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Pricing Engine - Gestiune Catalog Complet")
st.write("Proiect de laborator: Sistem inteligent pentru recalcularea dinamică a prețurilor la raft.")

@st.cache_data
def load_data_from_catalog(file_name):
    catalog = []
    if not os.path.exists(file_name):
        return []
    
    with open(file_name, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: 
                continue  
            
            parts = re.split(r'\t| {2,}', line)
            
            if len(parts) >= 3:
                try:
                    sku = parts[0].strip()
                    nume = parts[1].strip()
                    raw_price = parts[2].replace('RON', '').replace(' ', '').replace(',', '.').strip()
                    pret = float(raw_price)
                    
                    catalog.append({
                        "SKU": sku, 
                        "Produs": nume, 
                        "Pret_Altex": pret
                    })
                except ValueError:
                    continue 
    return catalog

data = load_data_from_catalog("c.txt")

if data:
    st.success(f"✅ Baza de date conectată: S-au încărcat {len(data)} produse din 'c.txt'")
else:
    st.error("⚠️ Eroare critică: Fișierul 'c.txt' nu a fost găsit sau structura sa este incorectă.")

st.sidebar.header("⚙️ Parametri Strategie Comercială")
st.sidebar.write("Modifică valorile de mai jos pentru a influența prețul final de etichetă:")

app_discount = st.sidebar.slider("Discount Aplicație (%)", min_value=0, max_value=30, value=20)
rabla_voucher = st.sidebar.number_input("Voucher Rabla (RON)", min_value=0, max_value=500, value=150, step=50)
min_margin = st.sidebar.slider("Marjă Minimă Profit (%)", min_value=1, max_value=15, value=7)

if data:
    st.subheader("🔎 Gestiune Produse de Monitorizat")
    
    options = [f"[{p['SKU']}] {p['Produs']}" for p in data]
    selected_option = st.selectbox("Caută produsul în catalogul general:", options)

    if st.button("➕ Adaugă produsul în analiză"):
        sku_clean = selected_option.split(']')[0][1:]
        info = next(item for item in data if item["SKU"] == sku_clean)
        
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
            if new_row["SKU"] not in st.session_state.df_monitor["SKU"].values:
                st.session_state.df_monitor = pd.concat([st.session_state.df_monitor, pd.DataFrame([new_row])], ignore_index=True)
        
        st.rerun()

def calculate_repricing(dataframe, discount, voucher, margin):
    res_prices = []
    res_status = []
    res_profit = []
    
    for _, row in dataframe.iterrows():
        try:
            cost = float(row['Cost_Achizitie'])
            pret_altex = float(row['Pret_Altex'])
            
            target_net = pret_altex - 5
            factor_app = 1 - (discount / 100)
            
            suggested_shelf = (target_net + voucher) / factor_app
            
            min_net_allowed = cost * (1 + margin / 100)
            actual_net = (suggested_shelf * factor_app) - voucher
            
            if actual_net < min_net_allowed:
                suggested_shelf = (min_net_allowed + voucher) / factor_app
                status = "🔴 Marjă Protejată"
            else:
                status = "🟢 Competitiv"
            
            final_p = round(math.floor(suggested_shelf) + 0.90, 2)
            
            venit_net_final = (final_p * factor_app) - voucher
            profit_ron = round(venit_net_final - cost, 2)
            
        except (ValueError, TypeError, ZeroDivisionError):
            final_p = 0.0
            status = "⚠️ Eroare Date Introduse"
            profit_ron = 0.0
            
        res_prices.append(final_p)
        res_status.append(status)
        res_profit.append(profit_ron)
        
    return res_prices, res_status, res_profit

if 'df_monitor' in st.session_state and not st.session_state.df_monitor.empty:
    st.markdown("---")
    st.subheader("📋 Panou de Gestiune și Analiză Prețuri")
    st.write("Poți edita direct în tabel valorile din 'Cost_Achizitie' sau 'Stoc_Depozit':")
    
    edited_df = st.data_editor(st.session_state.df_monitor, num_rows="dynamic", use_container_width=True)
    
    prices, statuses, profits = calculate_repricing(edited_df, app_discount, rabla_voucher, min_margin)
    
    edited_df['Pret_Nou_Eticheta'] = prices
    edited_df['Status_Profit'] = statuses
    edited_df['Profit_Estimat_RON'] = profits
    
    st.session_state.df_monitor = edited_df

    st.dataframe(edited_df, use_container_width=True, hide_index=True)
    
    st.write("")
    csv_data = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descarcă Raportul de Pricing (CSV)",
        data=csv_data,
        file_name="raport_pricing_dinamic.csv",
        mime="text/csv"
    )
    
    st.write("")
    st.subheader("📈 Vizualizare Grafică")
    st.bar_chart(edited_df.set_index('Produs')[['Pret_Altex', 'Pret_Nou_Eticheta']])
