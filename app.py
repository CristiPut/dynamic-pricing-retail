import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Retail Dynamic Pricing - Catalog Altex", layout="wide", page_icon="📊")

@st.cache_data
def load_data_from_catalog(file_name):
    if not os.path.exists(file_name):
        return pd.DataFrame()
    
    try:
        
        df = pd.read_csv(
            file_name, 
            sep=r'\t| {2,}', 
            engine='python', 
            header=None, 
            names=["SKU", "Produs", "Pret_Altex"]
        )
        
        df['SKU'] = df['SKU'].astype(str).str.strip()
        df['Produs'] = df['Produs'].astype(str).str.strip()
        
        df['Pret_Altex'] = (df['Pret_Altex']
                            .astype(str)
                            .str.replace('RON', '', case=False)
                            .str.replace(' ', '')
                            .str.replace(',', '.')
                            .str.strip())
        df['Pret_Altex'] = pd.to_numeric(df['Pret_Altex'], errors='coerce')
        
        return df.dropna(subset=['SKU', 'Pret_Altex']).reset_index(drop=True)
    except Exception as e:
        st.error(f"Eroare la citirea fișierului: {e}")
        return pd.DataFrame()

df_catalog = load_data_from_catalog("c.txt")

st.title("📊 Pricing Engine - Gestiune Catalog Complet")

if not df_catalog.empty:
    st.success(f"✅ S-au încărcat {len(df_catalog)} produse din baza de date c.txt")
else:
    st.error("⚠️ Eroare: Fișierul c.txt nu a fost găsit, este gol sau are un format invalid.")

st.sidebar.header("⚙️ Setări Campanii")
app_discount = st.sidebar.slider("Discount Aplicație (%)", 0, 30, 20)
rabla_voucher = st.sidebar.number_input("Voucher Rabla (RON)", 0, 500, 150)
min_margin = st.sidebar.slider("Marjă Minimă Profit (%)", 1, 15, 7)

if 'df_monitor' not in st.session_state:
    st.session_state.df_monitor = pd.DataFrame(columns=["SKU", "Produs", "Cost_Achizitie", "Pret_Altex", "Stoc_Depozit"])

if not df_catalog.empty:
    st.subheader("🔎 Selector Produse")
   
    options = df_catalog.apply(lambda row: f"[{row['SKU']}] {row['Produs']}", axis=1).tolist()
    selected_option = st.selectbox("Caută și adaugă produse în lista de monitorizare:", options)

    if st.button("➕ Adaugă în Tabel"):
        sku_clean = selected_option.split(']')[0][1:]
        
        if sku_clean not in st.session_state.df_monitor["SKU"].values:
            info = df_catalog[df_catalog["SKU"] == sku_clean].iloc[0]
            cost_simulat = round(info["Pret_Altex"] * 0.78, 2)
            
            new_row = pd.DataFrame([{
                "SKU": info["SKU"],
                "Produs": info["Produs"],
                "Cost_Achizitie": cost_simulat,
                "Pret_Altex": info["Pret_Altex"],
                "Stoc_Depozit": 15
            }])
            
            st.session_state.df_monitor = pd.concat([st.session_state.df_monitor, new_row], ignore_index=True)
            st.rerun()

if not st.session_state.df_monitor.empty:
    st.markdown("---")
    st.subheader("📋 Analiză Prețuri la Raft")
    
    edited_df = st.data_editor(st.session_state.df_monitor, num_rows="dynamic", use_container_width=True, key="editor_tabel")
    
    st.session_state.df_monitor = edited_df

    if st.button("🚀 EXECUTĂ RE-PRICING"):
        df_calc = edited_df.copy()
        
        factor_app = 1 - (app_discount / 100)
        target_net = df_calc['Pret_Altex'] - 5
        
        suggested_shelf = (target_net + rabla_voucher) / factor_app
        
        min_net_allowed = df_calc['Cost_Achizitie'] * (1 + min_margin / 100)
        actual_net = (suggested_shelf * factor_app) - rabla_voucher
        
        suggested_shelf = np.where(
            actual_net < min_net_allowed,
            (min_net_allowed + rabla_voucher) / factor_app,
            suggested_shelf
        )
        
        df_calc['Status_Profit'] = np.where(actual_net < min_net_allowed, "🔴 Marjă Protejată", "🟢 Competitiv")
        
        df_calc['Pret_Nou_Eticheta'] = np.floor(suggested_shelf) + 0.90
        
        df_calc['Profit_Estimat_RON'] = round(((df_calc['Pret_Nou_Eticheta'] * factor_app) - rabla_voucher) - df_calc['Cost_Achizitie'], 2)
        
        st.session_state.df_monitor = df_calc
        st.rerun()

    # Dacă tabelul conține deja calculele de re-pricing, le afișăm vizual
if 'Pret_Nou_Eticheta' in st.session_state.df_monitor.columns:
    st.markdown("### 📈 Rezultate Re-Pricing")
    
    # Adăugăm str.strip() sau verificări solide pentru a evita erorile de formatare
    def color_status(val):
        if pd.isna(val): 
            return ''
        val_str = str(val).strip()
        if "🔴" in val_str or "Marjă Protejată" in val_str: 
            return 'background-color: #ffcccc; color: black;'
        if "🟢" in val_str or "Competitiv" in val_str: 
            return 'background-color: #ccffcc; color: black;'
        return ''
        
    try:
        st.dataframe(
            st.session_state.df_monitor.style.map(color_status, subset=['Status_Profit']), 
            use_container_width=True
        )
    except AttributeError:
        st.dataframe(
            st.session_state.df_monitor.style.applymap(color_status, subset=['Status_Profit']), 
            use_container_width=True
        )
        
        st.bar_chart(st.session_state.df_monitor.set_index('Produs')[['Pret_Altex', 'Pret_Nou_Eticheta']])
