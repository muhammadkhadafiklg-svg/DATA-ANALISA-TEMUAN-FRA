import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq

# ==========================================
# 1. KONFIGURASI & TEMA DASHBOARD (ENTERPRISE EXECUTIVE)
# ==========================================
st.set_page_config(
    page_title="Dashboard Analisa Temuan Visit Store",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Plus Jakarta Sans', sans-serif; 
        color: #0f172a; 
        background-color: #f8fafc;
    }
    
    /* Layout & Container Styling */
    .main-header {
        background: #ffffff;
        padding: 24px 30px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 25px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    
    .kpi-container { display: flex; gap: 20px; margin-bottom: 25px; }
    .kpi-card { 
        background: #ffffff; 
        border: 1px solid #cbd5e1; 
        padding: 22px 24px; 
        border-radius: 12px; 
        width: 100%; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: #1E3A8A;
    }
    .kpi-card.alert::before { background: #E11D48; }
    .kpi-card.success::before { background: #10B981; }
    
    .kpi-label { font-size: 12px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }
    .kpi-value { font-size: 30px; font-weight: 800; color: #020617; line-height: 1.1; }
    .kpi-desc { font-size: 12px; font-weight: 600; color: #64748b; margin-top: 6px; }
    
    .rekomendasi-box { 
        background-color: #ffffff; 
        border: 1px solid #cbd5e1; 
        border-left: 5px solid #2563eb; 
        padding: 22px 26px; 
        border-radius: 8px; 
        margin-bottom: 25px; 
        font-size: 14px; 
        line-height: 1.8; 
        color: #1e293b;
        box-shadow: 0 1px 2px 0 rgba(0,0,0,0.02);
    }
    
    .chat-container {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    hr { border-color: #cbd5e1; margin: 2rem 0; }
    </style>
''', unsafe_allow_html=True)

# ==========================================
# 2. PENGAMBILAN DATA
# ==========================================
SHEET_ID = "1RfrC_LUAZbKrGEN15KPkBXhUz8ei2jyqGdUaKPS4WMY"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(url)
    
    raw_kode = df.iloc[:, 3].astype(str).str.upper().str.strip()
    kode_toko_bersih = raw_kode.apply(lambda x: x[:4] if len(x) >= 4 else x)
    
    df_clean = pd.DataFrame({
        'TANGGAL': df.iloc[:, 0].astype(str),
        'FRA': df.iloc[:, 1].astype(str).str.upper().str.strip(),
        'KODE STORE': kode_toko_bersih,
        'NAMA STORE': df.iloc[:, 4].astype(str).str.upper().str.strip(),
        'DETAIL TEMUAN': df.iloc[:, 5].astype(str).str.upper().str.strip(),
        'BISNIS UNIT': df.iloc[:, 6].astype(str).str.upper().str.strip()
    })
    
    return df_clean.replace(['NAN', 'NAN ', ''], None)

try:
    df_mentah = load_data()
except Exception as e:
    st.error("Gagal membaca sambungan data dari Google Sheets.")
    st.stop()

# ==========================================
# 3. KATEGORISASI (ENGINE LOGIKA KOSONG)
# ==========================================
def deteksi_kategori(teks):
    if not teks or pd.isna(teks) or str(teks).strip() == "": return None
    
    teks_upper = str(teks).upper()
    kata_aman = ["TIDAK ADA", "-", "0", "–", "NIHIL", "AMAN", "TDK ADA", "KOSONG", "TIDAK DIISI", "TIDAK ADA TEMUAN"]
    if any(x in teks_upper for x in kata_aman): return None
    
    if "STB" in teks_upper: return "ISU STB (SETORAN)"
    if any(x in teks_upper for x in ["BRANKAS", "PASS"]): return "AKSES/PASSWORD BRANKAS"
    if any(x in teks_upper for x in ["NOTA", "BON"]): return "ADMINISTRASI NOTA/BON"
    if any(x in teks_upper for x in ["SELISIH", "MINUS", "PLUS", "PC", "RP"]): return "SELISIH UANG / PC"
    if any(x in teks_upper for x in ["KASBON", "KB"]): return "KASBON MENGGANTUNG"
    if any(x in teks_upper for x in ["DBS", "PETTY CASH"]): return "PENGELUARAN DBS/PETTY CASH"
    if any(x in teks_upper for x in ["MOP", "EDC"]): return "MESIN EDC / MOP"
    
    return "TEMUAN OPERASIONAL LAINNYA"

df_mentah['Bulan'] = df_mentah['TANGGAL'].apply(lambda x: x.split(' ')[1] if len(x.split(' ')) >= 3 else 'Unknown')
df_mentah['Tahun'] = df_mentah['TANGGAL'].apply(lambda x: x.split(' ')[2] if len(x.split(' ')) >= 3 else 'Unknown')
df_mentah['Kategori Temuan'] = df_mentah['DETAIL TEMUAN'].apply(deteksi_kategori)
df_mentah['Ada Temuan'] = df_mentah['Kategori Temuan'].notna()

# ==========================================
# 4. SIDEBAR - PANEL KONTROL
# ==========================================
st.sidebar.markdown("<h3 style='color:#0f172a; font-weight:800; font-size:18px;'>🎛️ Panel Filter & Kontrol</h3>", unsafe_allow_html=True)

urutan_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
bulan_tersedia = [b for b in urutan_bulan if b in df_mentah['Bulan'].unique()]
tahun_tersedia = sorted(df_mentah[df_mentah['Tahun'] != 'Unknown']['Tahun'].unique(), reverse=True)

list_bu = sorted([b for b in df_mentah['BISNIS UNIT'].dropna().unique() if b and b != 'NONE'])
list_fra = sorted([f for f in df_mentah['FRA'].dropna().unique() if f and f != 'NONE'])

pilih_tahun = st.sidebar.selectbox("📅 Tahun Data", ["Semua Tahun"] + tahun_tersedia)
pilih_bulan = st.sidebar.selectbox("🗓️ Bulan Data", ["Semua Bulan"] + bulan_tersedia)
st.sidebar.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
pilih_bu = st.sidebar.selectbox("🏢 Unit Bisnis (BU)", ["Semua Bisnis Unit"] + list_bu)
pilih_fra = st.sidebar.selectbox("🧑‍💼 Area (FRA)", ["Semua Area"] + list_fra)

st.sidebar.markdown(
    """
    <div style='text-align: center; margin-top: 35px; padding: 20px; border-radius: 10px; background: #ffffff; border: 1px solid #cbd5e1; box-shadow: 0 1px 3px rgba(0,0,0,0.04);'>
        <div style='font-size: 10px; color: #64748b; font-weight:800; letter-spacing:1.2px; margin-bottom:6px;'>POWERED & DEVELOPED BY</div>
        <div style='font-size: 16px; color: #020617; font-weight: 800;'>M Khadafi Zainal</div>
        <div style='font-size: 13px; color: #1E3A8A; font-weight: 700; margin-top:4px;'>Finance Representative</div>
    </div>
    """, unsafe_allow_html=True
)

# Filtering Engine
df_filter = df_mentah.copy()
if pilih_tahun != "Semua Tahun": df_filter = df_filter[df_filter['Tahun'] == pilih_tahun]
if pilih_bulan != "Semua Bulan": df_filter = df_filter[df_filter['Bulan'] == pilih_bulan]
if pilih_bu != "Semua Bisnis Unit": df_filter = df_filter[df_filter['BISNIS UNIT'] == pilih_bu]
if pilih_fra != "Semua Area": df_filter = df_filter[df_filter['FRA'] == pilih_fra]

total_visit = len(df_filter)
df_temuan = df_filter[df_filter['Ada Temuan'] == True]
total_temuan = len(df_temuan)
toko_dengan_temuan = df_temuan['NAMA STORE'].nunique()
rasio_temuan = (total_temuan / total_visit * 100) if total_visit > 0 else 0

# ==========================================
# 5. HEADER & KPI 
# ==========================================
st.markdown('''
    <div class="main-header">
        <h2 style='color:#020617; font-weight:800; font-size:26px; margin:0 0 6px 0;'>Dashboard Analisa Temuan Visit Store</h2>
        <p style='color:#475569; font-size:15px; font-weight:500; margin:0;'>Laporan analitik komprehensif data temuan operasional lapangan berdasarkan visit cabang.</p>
    </div>
''', unsafe_allow_html=True)

st.markdown(f'''
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi
