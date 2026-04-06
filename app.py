import streamlit as st
import pandas as pd
import math

# --- CONFIGURARE PAGINĂ ---
st.set_page_config(page_title="Retail Smart Engine - Full Catalog", layout="wide")

# --- FUNCȚIE PENTRU ÎNCĂRCAREA DATELOR DIN C.TXT ---
@st.cache_data
def load_catalog_from_file(file_path):
    catalog = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if "|" in line: # Presupunem că datele sunt separate prin "|" sau tab
                    parts = [p.strip() for p in line.split("|")]
                else:
                    # Dacă e copy-paste din Excel, separatorul e de obicei Tab (\t)
                    parts = [p.strip() for p in line.split("\t")]
                
                if len(parts) >= 3:
                    try:
                        # Curățăm prețul (scoatem "RON", spații, înlocuim virgula cu punct)
                        pret_raw = parts[2].replace("RON", "").replace(" ", "").replace(",", ".").strip()
                        catalog.append({
                            "cod": parts[0],
                            "nume": parts[1],
                            "pret_altex": float(pret_raw)
                        })
                    except:
                        continue
        return catalog
    except Exception as e:
        st.error(f"Eroare la citirea fișierului: {e}")
        return []

# Încărcăm datele
CATALOG_COMPLET = load_catalog_from_file("c.txt")

st.title("🔌 Dynamic Pricing Engine - Integrare Completă Catalog")
st.markdown(f"Sistemul a detectat și încărcat **{len(CATALOG_COMPLET)} produse** din baza de date `c.txt`.")

# --- SIDEBAR ---
st.sidebar.header("⚙️ Setări Strategie")
app_discount = st.sidebar.slider("Discount Aplicație (%)", 0, 30, 20)
rabla_voucher = st.sidebar.number_input("Voucher Rabla (RON)", 0, 500, 150)
margin_safety = st.sidebar.slider("Marjă Minimă Profit (%)", 1, 15, 7)

# --- SELECTOR PRODUSE ---
if CATALOG_COMPLET:
    st.subheader("🔎 Căutare Globală în Catalogul Altex")
    nume_list = [f"[{p['cod']}] {p['nume']}" for p in CATALOG_COMPLET]
    selectie = st.selectbox("Caută orice produs din listă:", options=nume_list)

    if st.button("➕ Adaugă la Analiză"):
        sku_ales = selectie.split(']')[0][1:]
        info_p = next(p for p in CATALOG_COMPLET if p["cod"] == sku_ales)
        
        # Simulare cost (aprox 78% din preț)
        cost_calc = round(info_p["pret_altex"] * 0.78, 2)
        
        rand = {
            "SKU": info_p["cod"],
            "Produs": info_p["nume"],
            "Cost Achizitie": cost_calc,
            "Pret Altex (Comp)": info_p["pret_altex"],
            "Pret Raft Actual": round(info_p["pret_altex"] + 49.0, 2)
        }
        
        if 'monitor' not in st.session_state:
            st.session_state.monitor = pd.DataFrame([rand])
        else:
            if rand["SKU"] not in st.session_state.monitor["SKU"].values:
                st.session_state.monitor = pd.concat([st.session_state.monitor, pd.DataFrame([rand])], ignore_index=True)

# --- CALCUL ȘI DASHBOARD ---
if 'monitor' in st.session_state and not st.session_state.monitor.empty:
    st.markdown("---")
    st.subheader("📊 Dashboard Decizional")
    
    df_ed = st.data_editor(st.session_state.monitor, num_rows="dynamic", use_container_width=True)
    st.session_state.monitor = df_ed

    if st.button("🚀 RULEAZĂ CALCUL DINAMIC"):
        new_prices = []
        statuses = []
        
        for _, r in df_ed.iterrows():
            target_net = float(r['Pret Altex (Comp)']) - 5
            f_app = 1 - (app_discount / 100)
            
            shelf_p = (target_net + rabla_voucher) / f_app
            
            min_allowed = float(r['Cost Achizitie']) * (1 + margin_safety / 100)
            net_final = (shelf_p * f_app) - rabla_voucher
            
            if net_final < min_allowed:
                shelf_p = (min_allowed + rabla_voucher) / f_app
                stat = "🔴 Marjă Protejată"
            else:
                stat = "🟢 Optimizat"
            
            new_prices.append(round(math.floor(shelf_p) + 0.90, 2))
            statuses.append(stat)

        df_ed['Pret Nou Sugerat'] = new_prices
        df_ed['Status'] = statuses
        st.dataframe(df_ed, use_container_width=True)
        st.bar_chart(df_ed.set_index('SKU')[['Pret Altex (Comp)', 'Pret Nou Sugerat']])
else:
    st.info("Catalogul este gata. Selectează produse pentru a începe simularea.")
