import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. KONFIGURASI & TEMA DASHBOARD
# ==========================================
st.set_page_config(page_title="Executive Dashboard - Analisa Visit", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown('''
    <style>
    .metric-container { display: flex; justify-content: space-between; gap: 15px; margin-bottom: 20px; }
    .metric-box { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 20px; border-radius: 10px; width: 100%; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border-top: 4px solid #1E3A8A; }
    .metric-box.alert { border-top-color: #E11D48; }
    .metric-box.success { border-top-color: #10B981; }
    .metric-title { font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
    .metric-value { font-size: 28px; font-weight: 800; color: #0f172a; }
    .metric-sub { font-size: 12px; font-weight: 500; color: #94a3b8; margin-top: 5px;}
    .rekomendasi-box { background-color: #f8fafc; border-left: 4px solid #3b82f6; padding: 15px 20px; border-radius: 5px; margin-bottom:15px; }
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
    
    # Membaca Data (Pastikan index kolom Excel sesuai)
    df_clean = pd.DataFrame({
        'TANGGAL': df.iloc[:, 0].astype(str),
        'FRA': df.iloc[:, 1].astype(str).str.upper().str.strip(),
        'BISNIS UNIT': df.iloc[:, 2].astype(str).str.upper().str.strip(),
        'KODE STORE': df.iloc[:, 3].astype(str).str.upper().str.strip(),
        'NAMA STORE': df.iloc[:, 4].astype(str).str.upper().str.strip(),
        'DETAIL TEMUAN': df.iloc[:, 5].astype(str).str.upper().str.strip()
    })
    
    df_clean = df_clean.replace(['NAN', 'NAN ', ''], None)
    return df_clean

try:
    df_mentah = load_data()
except Exception as e:
    st.error("Gagal membaca data dari Google Sheets. Pastikan link dapat diakses publik.")
    st.stop()

# ==========================================
# 3. ALGORITMA KATEGORISASI (ENGINE)
# ==========================================
def deteksi_kategori(teks):
    if not teks or pd.isna(teks): return None
    if any(x in teks for x in ["TIDAK ADA", "-", "0", "–", "NIHIL", "AMAN", "TDK ADA"]): return None
    
    if "STB" in teks: return "ISU STB (SETORAN)"
    if any(x in teks for x in ["BRANKAS", "PASS"]): return "AKSES/PASSWORD BRANKAS"
    if any(x in teks for x in ["NOTA", "BON"]): return "ADMINISTRASI NOTA/BON"
    if any(x in teks for x in ["SELISIH", "MINUS", "PLUS", "PC", "RP"]): return "SELISIH UANG / PC"
    if any(x in teks for x in ["KASBON", "KB"]): return "KASBON MENGGANTUNG"
    if any(x in teks for x in ["DBS", "PETTY CASH"]): return "PENGELUARAN DBS/PETTY CASH"
    if any(x in teks for x in ["MOP", "EDC"]): return "MESIN EDC / MOP"
    return "TEMUAN OPERASIONAL LAINNYA"

df_mentah['Bulan'] = df_mentah['TANGGAL'].apply(lambda x: x.split(' ')[1] if len(x.split(' ')) >= 3 else 'Unknown')
df_mentah['Tahun'] = df_mentah['TANGGAL'].apply(lambda x: x.split(' ')[2] if len(x.split(' ')) >= 3 else 'Unknown')
df_mentah['Kategori Temuan'] = df_mentah['DETAIL TEMUAN'].apply(deteksi_kategori)
df_mentah['Ada Temuan'] = df_mentah['Kategori Temuan'].notna()

# ==========================================
# 4. SIDEBAR - PANEL FILTER PINTAR
# ==========================================
st.sidebar.markdown("### 🎛️ Panel Filter Data")

urutan_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
bulan_tersedia = [b for b in urutan_bulan if b in df_mentah['Bulan'].unique()]
tahun_tersedia = sorted(df_mentah[df_mentah['Tahun'] != 'Unknown']['Tahun'].unique(), reverse=True)
list_bu = sorted([b for b in df_mentah['BISNIS UNIT'].dropna().unique() if b and b != 'NONE'])
list_fra = sorted([f for f in df_mentah['FRA'].dropna().unique() if f and f != 'NONE'])

pilih_tahun = st.sidebar.selectbox("📅 Pilih Tahun", ["Semua Tahun"] + tahun_tersedia)
pilih_bulan = st.sidebar.selectbox("🗓️ Pilih Bulan", ["Semua Bulan"] + bulan_tersedia)

st.sidebar.markdown("---")
st.sidebar.markdown("**Filter Hirarki:**")
pilih_bu = st.sidebar.selectbox("🏢 Filter Bisnis Unit", ["Semua Bisnis Unit"] + list_bu)
pilih_fra = st.sidebar.selectbox("🧑‍💼 Filter Area (FRA)", ["Semua Area"] + list_fra)

# Terapkan Filter
df_filter = df_mentah.copy()
if pilih_tahun != "Semua Tahun": df_filter = df_filter[df_filter['Tahun'] == pilih_tahun]
if pilih_bulan != "Semua Bulan": df_filter = df_filter[df_filter['Bulan'] == pilih_bulan]
if pilih_bu != "Semua Bisnis Unit": df_filter = df_filter[df_filter['BISNIS UNIT'] == pilih_bu]
if pilih_fra != "Semua Area": df_filter = df_filter[df_filter['FRA'] == pilih_fra]

total_visit = len(df_filter)
df_temuan = df_filter[df_filter['Ada Temuan'] == True]
total_temuan = len(df_temuan)
toko_unik_bermasalah = df_temuan['NAMA STORE'].nunique()
rasio_temuan = (total_temuan / total_visit * 100) if total_visit > 0 else 0

# ==========================================
# 5. HEADER & KPI METRICS
# ==========================================
st.markdown("<h2 style='color:#0f172a; font-weight:800; margin-bottom:0px;'>📈 Executive Dashboard: Visit Operations</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#64748b; margin-bottom:25px;'>Analisa mendalam temuan operasional lapangan untuk mendukung keputusan strategis.</p>", unsafe_allow_html=True)

st.markdown(f'''
    <div class="metric-container">
        <div class="metric-box">
            <div class="metric-title">Total Kunjungan (Visit)</div>
            <div class="metric-value">{total_visit}</div>
            <div class="metric-sub">Toko yang diaudit pada filter ini</div>
        </div>
        <div class="metric-box alert">
            <div class="metric-title">Kasus Temuan</div>
            <div class="metric-value">{total_temuan}</div>
            <div class="metric-sub">Total rincian isu operasional</div>
        </div>
        <div class="metric-box alert">
            <div class="metric-title">Toko Bermasalah</div>
            <div class="metric-value">{toko_unik_bermasalah}</div>
            <div class="metric-sub">Toko unik yang memiliki temuan</div>
        </div>
        <div class="metric-box {'alert' if rasio_temuan > 30 else 'success'}">
            <div class="metric-title">Defect Rate (Rasio Masalah)</div>
            <div class="metric-value">{rasio_temuan:.1f}%</div>
            <div class="metric-sub">Tingkat kecacatan dari total visit</div>
        </div>
    </div>
''', unsafe_allow_html=True)

if total_temuan == 0:
    st.success("🎉 Luar biasa! Tidak ada data temuan pada Bisnis Unit / Filter yang Anda pilih. Operasional berjalan bersih
