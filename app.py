import streamlit as st
import pandas as pd
import math

# --- CONFIGURARE PAGINĂ ---
st.set_page_config(page_title="Dynamic Pricing Engine - Retail", layout="wide")

# --- BAZA DE DATE PRODUSE (Extrasă din lista ta) ---
# Am mapat Denumirea, Codul (SKU) și Prețul de pe Altex
CATALOG_PRODUSE = [
    {"cod": "MSRWW70T4040EE", "nume": "Masina de spalat rufe frontala SAMSUNG WW70T4040EE/LE, 7kg", "pret_altex": 1499.90},
    {"cod": "MSRWW70TA046TE", "nume": "Masina de spalat rufe frontala SAMSUNG WW70TA046TE/L3, Eco Bubble, 7kg", "pret_altex": 1749.90},
    {"cod": "MSRWW80T4040EE", "nume": "Masina de spalat rufe frontala SAMSUNG WW80T4040EE/LE, 8kg", "pret_altex": 1549.90},
    {"cod": "MSRWW80TA046TE", "nume": "Masina de spalat rufe frontala SAMSUNG WW80TA046TE/LE, Eco Bubble, 8kg", "pret_altex": 1849.90},
    {"cod": "MSRWW90T4040EE", "nume": "Masina de spalat rufe frontala SAMSUNG WW90T4040EE/LE, 9kg", "pret_altex": 1649.90},
    {"cod": "MSRWW90TA046TE", "nume": "Masina de spalat rufe frontala SAMSUNG WW90TA046TE/LE, Eco Bubble, 9kg", "pret_altex": 1949.90},
    {"cod": "MSRWW11BB744DGA", "nume": "Masina de spalat rufe frontala SAMSUNG Bespoke WW11BB744DGA/S3, Eco Bubble, AI Control, 11kg", "pret_altex": 3299.90},
    {"cod": "MSRWW11BB944DGM", "nume": "Masina de spalat rufe frontala SAMSUNG Bespoke WW11BB944DGM/S3, QuickDrive, AI Control, 11kg", "pret_altex": 3799.90},
    {"cod": "MSRWUE7636X0W", "nume": "Masina de spalat rufe frontala BEKO WUE7636X0W, SteamCure, 7kg", "pret_altex": 1449.90},
    {"cod": "MSRWTV9636XS0", "nume": "Masina de spalat rufe frontala BEKO WTV9636XS0, SteamCure, 9kg", "pret_altex": 1699.90},
    {"cod": "MSRB3WFU7842WB", "nume": "Masina de spalat rufe frontala BEKO B3WFU7842WB, IronFast, 8kg", "pret_altex": 1599.90},
    {"cod": "MSRB3WFU7942CH", "nume": "Masina de spalat rufe frontala BEKO B3WFU7942CH, IronFast, 9kg", "pret_altex": 1749.90},
    {"cod": "MSRB5WFU71042W", "nume": "Masina de spalat rufe frontala BEKO B5WFU71042W, SteamCure, AquaTech, 10kg", "pret_altex": 2199.90},
    {"cod": "MSRWUI84524W", "nume": "Masina de spalat rufe frontala BEKO WUI84524W, SteamCure, IronFast, 8kg", "pret_altex": 1549.90},
    {"cod": "MSRF4J3TN5W", "nume": "Masina de spalat rufe frontala LG F4J3TN5W, Direct Drive, 8kg", "pret_altex": 1649.90},
    {"cod": "MSRF4WV308S3E", "nume": "Masina de spalat rufe frontala LG F4WV308S3E, AI DD, 8kg", "pret_altex": 1999.90},
    {"cod": "MSRF4WV309S6W", "nume": "Masina de spalat rufe frontala LG F4WV309S6W, AI DD, 9kg", "pret_altex": 2149.90},
    {"cod": "MSRF4WV310S6E", "nume": "Masina de spalat rufe frontala LG F4WV310S6E, AI DD, 10.5kg", "pret_altex": 2499.90},
    {"cod": "MSRF4V5VW0W", "nume": "Masina de spalat rufe frontala LG F4V5VW0W, AI DD, AI Control, 9kg", "pret_altex": 2249.90},
    {"cod": "MSRF4V11WSA", "nume": "Masina de spalat rufe frontala LG F4V11WSA, TurboWash, AI DD, 11kg", "pret_altex": 3499.90},
    {"cod": "MSRFFW8468BVEE", "nume": "Masina de spalat rufe frontala WHIRLPOOL FFW 8468 BV EE, 6th Sense, 8kg", "pret_altex": 1699.90},
    {"cod": "MSRFFW9468BVEE", "nume": "Masina de spalat rufe frontala WHIRLPOOL FFW 9468 BV EE, 6th Sense, 9kg", "pret_altex": 1849.90},
    {"cod": "MSRW8W946WR", "nume": "Masina de spalat rufe frontala WHIRLPOOL W8 W946WR EE, Supreme Silence, 9kg", "pret_altex": 2599.90},
    {"cod": "MSRW7XW845WBEE", "nume": "Masina de spalat rufe frontala WHIRLPOOL W7X W845WB EE, 6th Sense, 8kg", "pret_altex": 2149.90},
    {"cod": "MSRL7FEE48S", "nume": "Masina de spalat rufe frontala AEG Seria 7000 L7FEE48S, ProSteam, 8kg", "pret_altex": 2799.90},
    {"cod": "MSRL8FEE48S", "nume": "Masina de spalat rufe frontala AEG Seria 8000 L8FEE48S, OkoMix, 8kg", "pret_altex": 3149.90},
    {"cod": "MSRWAN28263BY", "nume": "Masina de spalat rufe frontala BOSCH WAN28263BY, EcoSilence Drive, 8kg", "pret_altex": 2299.90},
    {"cod": "MSRWGG14400BY", "nume": "Masina de spalat rufe frontala BOSCH WGG14400BY, EcoSilence Drive, 9kg", "pret_altex": 2649.90},
    {"cod": "MSRWGG254A0BY", "nume": "Masina de spalat rufe frontala BOSCH WGG254A0BY, i-DOS, 10kg", "pret_altex": 3199.90}
]

# Am inclus în cod o parte din listă (cele mai populare). 
# Aplicația poate fi extinsă ușor adăugând rânduri în lista de mai sus.

st.title("📊 Altex Dynamic Pricing Engine")
st.markdown("---")

# --- SIDEBAR: SETĂRI CAMPANIE ---
st.sidebar.header("⚙️ Configurare Campanii")
app_promo = st.sidebar.slider("Discount Aplicație (%)", 0, 30, 20)
rabla_promo = st.sidebar.number_input("Voucher Rabla (RON)", 0, 500, 150)
min_margin_pct = st.sidebar.slider("Marjă Minimă Profit (%)", 1, 20, 7)

# --- SELECTOR PRODUS ---
st.subheader("🔎 Selectare Produs din Catalog Altex")
nume_produse = [p["nume"] for p in CATALOG_PRODUSE]
produs_ales = st.selectbox("Caută mașina de spălat după kg sau brand:", options=nume_produse)

if st.button("➕ Adaugă în Monitorizare"):
    # Găsim datele produsului în catalog
    date_p = next(item for item in CATALOG_PRODUSE if item["nume"] == produs_ales)
    
    # Simulăm un cost de achiziție (WAC) de 75% din prețul Altex
    cost_simulat = round(date_p["pret_altex"] * 0.75, 2)
    
    nou_entry = {
        "Cod Articol": date_p["cod"],
        "Denumire": date_p["nume"],
        "Cost Achizitie": cost_simulat,
        "Pret Altex": date_p["pret_altex"],
        "Pret Nostru Actual": round(date_p["pret_altex"] + 50, 2),
        "Stoc": 15
    }
    
    if 'monitor' not in st.session_state:
        st.session_state.monitor = pd.DataFrame([nou_entry])
    else:
        if nou_entry["Cod Articol"] not in st.session_state.monitor["Cod Articol"].values:
            st.session_state.monitor = pd.concat([st.session_state.monitor, pd.DataFrame([nou_entry])], ignore_index=True)
        else:
            st.warning("Produsul este deja în lista de monitorizare!")

# --- TABEL MONITORIZARE ȘI CALCUL ---
if 'monitor' in st.session_state and not st.session_state.monitor.empty:
    st.markdown("---")
    st.subheader("📋 Lista de Monitorizare Activă")
    
    # Tabel editabil
    df_editat = st.data_editor(st.session_state.monitor, num_rows="dynamic", use_container_width=True)
    st.session_state.monitor = df_editat

    if st.button("🚀 CALCULEAZĂ PREȚURI OPTIMIZATE"):
        new_prices = []
        statuses = []
        
        for _, row in df_editat.iterrows():
            # Logica: Vrem sa fim cu 5 lei sub Altex la pretul final (Net)
            target_net = row['Pret Altex'] - 5
            
            # Factor discount aplicatie
            disc_app_factor = 1 - (app_promo / 100)
            
            # Calculam ce pret trebuie sa punem la raft pentru a ajunge la target_net
            # Shelf = (Target + Rabla) / Factor_App
            suggested_shelf = (target_net + rabla_promo) / disc_app_factor
            
            # Validare marja profit
            min_net_allowed = row['Cost Achizitie'] * (1 + min_margin_pct / 100)
            actual_net = (suggested_shelf * disc_app_factor) - rabla_promo
            
            if actual_net < min_net_allowed:
                # Daca iesim in pierdere, fortam pretul la limita de profit
                suggested_shelf = (min_net_allowed + rabla_promo) / disc_app_factor
                status = "🔴 Marjă Protejată"
            else:
                status = "🟢 Optimizat"
            
            # Rotunjire psihologica .90
            final_p = round(math.floor(suggested_shelf) + 0.90, 2)
            new_prices.append(final_p)
            statuses.append(status)
            
        df_editat['Pret Nou Raft'] = new_prices
        df_editat['Status'] = statuses
        
        st.success("Prețuri calculate!")
        st.dataframe(df_editat, use_container_width=True)
        
        # Grafic comparativ
        st.bar_chart(df_editat.set_index('Cod Articol')[['Pret Nostru Actual', 'Pret Nou Raft']])
else:
    st.info("Alege un produs de mai sus și apasă pe butonul de adăugare pentru a începe.")
