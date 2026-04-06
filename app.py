import streamlit as st
import pandas as pd
import math

# --- CONFIGURARE ---
st.set_page_config(page_title="Altex Price Monitor", layout="wide")

# --- BAZA DE DATE PRODUSE ALTEX (Catalog Simulat) ---
# Aici poți adăuga oricâte mașini de spălat dorești
CATALOG_ALTEX = {
    "Whirlpool 7kg": {"Cost": 1050, "Pret_Altex": 1599, "SKU": "WH-7KG-PRO"},
    "Whirlpool 8kg": {"Cost": 1200, "Pret_Altex": 1799, "SKU": "WH-8KG-PRO"},
    "Whirlpool 9kg": {"Cost": 1350, "Pret_Altex": 2100, "SKU": "WH-9KG-PRO"},
    "Samsung 7kg Ecobubble": {"Cost": 1400, "Pret_Altex": 1949, "SKU": "SAM-7KG-EB"},
    "Samsung 8kg Ecobubble": {"Cost": 1600, "Pret_Altex": 2299, "SKU": "SAM-8KG-EB"},
    "Samsung 10kg AI Control": {"Cost": 2100, "Pret_Altex": 3199, "SKU": "SAM-10KG-AI"},
    "Beko 7kg Hygiene": {"Cost": 900, "Pret_Altex": 1349, "SKU": "BK-7KG-HYG"},
    "Beko 9kg IronFast": {"Cost": 1150, "Pret_Altex": 1699, "SKU": "BK-9KG-IF"},
    "LG 8kg DirectDrive": {"Cost": 1500, "Pret_Altex": 2150, "SKU": "LG-8KG-DD"},
}

st.title("🔌 Dynamic Pricing Engine - Altex Selection Tool")
st.markdown("---")

# --- SIDEBAR ---
st.sidebar.header("⚙️ Parametri Campanii")
app_discount = st.sidebar.slider("Discount Aplicație (%)", 0, 30, 20)
rabla_voucher = st.sidebar.number_input("Voucher Rabla (RON)", 0, 500, 150)
min_margin = st.sidebar.slider("Marjă Minimă Profit (%)", 1, 15, 7)

# --- SECȚIUNE ADĂUGARE PRODUS ---
st.subheader("🛒 Selectează Produsul de pe Altex")
col1, col2 = st.columns([2, 1])

with col1:
    produs_selectat = st.selectbox(
        "Alege modelul de mașină de spălat:",
        options=list(CATALOG_ALTEX.keys())
    )

with col2:
    if st.button("➕ Adaugă în Monitorizare"):
        info = CATALOG_ALTEX[produs_selectat]
        nou_rand = {
            "SKU": info["SKU"],
            "Produs": produs_selectat,
            "Cost": float(info["Cost"]),
            "Pret_Raft_Actual": float(info["Pret_Altex"] + 100), # Exemplu: noi suntem mai scumpi inițial
            "Stoc": 10,
            "Pret_Competitor": float(info["Pret_Altex"]) # Prețul luat "automat" de la Altex
        }
        
        if 'db' not in st.session_state:
            st.session_state.db = pd.DataFrame([nou_rand])
        else:
            # Evităm duplicatele
            if nou_rand["SKU"] not in st.session_state.db["SKU"].values:
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([nou_rand])], ignore_index=True)
            else:
                st.warning("Produsul este deja în listă!")

# --- TABEL ȘI CALCUL ---
if 'db' in st.session_state and not st.session_state.db.empty:
    st.subheader("2. Analiză Prețuri Active")
    
    # Permitem editarea stocului sau prețului nostru, dar cel Altex e deja acolo
    edited_df = st.data_editor(st.session_state.db, num_rows="dynamic", use_container_width=True)
    st.session_state.db = edited_df

    if st.button("🚀 CALCULEAZĂ OPTIMIZARE"):
        results = []
        for _, row in edited_df.iterrows():
            try:
                # Logica Dynamic Pricing
                target_net = float(row['Pret_Competitor']) - 5
                disc_factor = 1 - (app_discount / 100)
                suggested_shelf = (target_net + rabla_voucher) / disc_factor
                
                # Protecție Profit
                min_net = float(row['Cost']) * (1 + min_margin / 100)
                actual_net = (suggested_shelf * disc_factor) - rabla_voucher
                
                if actual_net < min_net:
                    suggested_shelf = (min_net + rabla_voucher) / disc_factor
                    status = "🔴 Marjă Protejată"
                else:
                    status = "🟢 Optimizat"
                
                results.append((round(math.floor(suggested_shelf) + 0.90, 2), status))
            except:
                results.append((0, "Incomplet"))

        edited_df['Pret_Nou_Propus'], edited_df['Status'] = zip(*results)
        st.dataframe(edited_df, use_container_width=True)
else:
    st.write("Niciun produs selectat. Folosește meniul de mai sus pentru a adăuga mașini de spălat.")
