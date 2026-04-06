import streamlit as st
import pandas as pd
import math

# Configurare pagină
st.set_page_config(page_title="Retail Dynamic Pricing", layout="wide")

st.title("🔌 Dynamic Pricing Engine - Management Stoc și Prețuri")
st.markdown("---")

# --- SIDEBAR: SETĂRI CAMPANII ---
st.sidebar.header("⚙️ Parametri Campanii")
app_discount = st.sidebar.slider("Discount Aplicație (%)", 0, 30, 20)
rabla_voucher = st.sidebar.number_input("Voucher Rabla (RON)", 0, 500, 150)
min_margin = st.sidebar.slider("Marjă Minimă Profit (%)", 1, 15, 7)

# --- INIȚIALIZARE DATE (Dacă nu există, creăm un tabel gol cu structură) ---
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame([
        {"SKU": "TV-SAM-01", "Produs": "TV Samsung OLED", "Cost": 3200.0, "Pret_Raft_Actual": 4800.0, "Stoc": 10, "Pret_Competitor": 4700.0},
        {"SKU": "MS-WH-02", "Produs": "Masina Spalat Whirlpool", "Cost": 1100.0, "Pret_Raft_Actual": 1850.0, "Stoc": 20, "Pret_Competitor": 1790.0},
    ])

# --- INTERFAȚA DE EDITARE ---
st.subheader("1. Catalog Produse (Editează sau Adaugă Produse Noi)")
st.info("Poți adăuga rânduri noi apăsând pe semnul '+' de jos sau poți șterge rânduri selectându-le.")

# Tabelul care permite adăugarea de rânduri noi (num_rows="dynamic")
edited_df = st.data_editor(
    st.session_state.db, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "Cost": st.column_config.NumberColumn(format="%.2f RON"),
        "Pret_Raft_Actual": st.column_config.NumberColumn(format="%.2f RON"),
        "Pret_Competitor": st.column_config.NumberColumn(format="%.2f RON"),
    }
)

# Salvează datele introduse manual în "baza de date" a sesiunii
st.session_state.db = edited_df

# --- LOGICA DE CALCUL ---
if st.button("🚀 CALCULEAZĂ PREȚURI PENTRU TOATE PRODUSELE"):
    def calculate_logic(row):
        # Regula: -5 RON sub competitor
        target_net = row['Pret_Competitor'] - 5
        
        # Ajustare stoc (Ex: lichidare stoc mare)
        if row['Stoc'] > 50: target_net -= 25
        
        # Formula inversă pentru preț raft (pentru a compensa campaniile)
        disc_factor = 1 - (app_discount / 100)
        suggested_shelf = (target_net + rabla_voucher) / disc_factor
        
        # Validare Marjă Minimă
        min_net_allowed = row['Cost'] * (1 + min_margin / 100)
        actual_net = (suggested_shelf * disc_factor) - rabla_voucher
        
        if actual_net < min_net_allowed:
            suggested_shelf = (min_net_allowed + rabla_voucher) / disc_factor
            status = "🔴 Marjă Protejată"
        else:
            status = "🟢 Optimizat"
            
        return round(math.floor(suggested_shelf) + 0.90, 2), status

    # Aplicăm logica pe toate rândurile introduse de tine
    results = [calculate_logic(row) for _, row in edited_df.iterrows()]
    edited_df['Pret_Nou_Propus'], edited_df['Status_Profit'] = zip(*results)
    
    st.success(f"Analiză finalizată pentru {len(edited_df)} produse!")
    st.dataframe(edited_df, use_container_width=True)

    # Vizualizare grafică a diferențelor
    st.subheader("Diferența de Preț (Actual vs Propus)")
    st.bar_chart(edited_df.set_index('Produs')[['Pret_Raft_Actual', 'Pret_Nou_Propus']])
