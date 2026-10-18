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
# 2. PENGAMBILAN DATA (AUTO-EXTRACT BU)
# ==========================================
SHEET_ID = "1RfrC_LUAZbKrGEN15KPkBXhUz8ei2jyqGdUaKPS4WMY"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(url)
    raw_kode = df.iloc[:, 3].astype(str).str.upper().str.strip()
    kode_toko_bersih = raw_kode.apply(lambda x: x[:4] if len(x) >= 4 else x)
    bisnis_unit = raw_kode.apply(lambda x: x[4:] if len(x) > 4 else 'BU LAINNYA')
    
    df_clean = pd.DataFrame({
        'TANGGAL': df.iloc[:, 0].astype(str),
        'BISNIS UNIT': bisnis_unit,
        'FRA': df.iloc[:, 1].astype(str).str.upper().str.strip(),
        'KODE STORE': kode_toko_bersih,
        'NAMA STORE': df.iloc[:, 4].astype(str).str.upper().str.strip(),
        'DETAIL TEMUAN': df.iloc[:, 5].astype(str).str.upper().str.strip()
    })
    return df_clean.replace(['NAN', 'NAN ', ''], None)

try:
    df_mentah = load_data()
except Exception as e:
    st.error("Gagal membaca data dari Google Sheets.")
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
# 4. SIDEBAR - PANEL FILTER PINTAR & CREDIT
# ==========================================
st.sidebar.markdown("### 🎛️ Panel Filter Data")
urutan_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
bulan_tersedia = [b for b in urutan_bulan if b in df_mentah['Bulan'].unique()]
tahun_tersedia = sorted(df_mentah[df_mentah['Tahun'] != 'Unknown']['Tahun'].unique(), reverse=True)
list_bu = sorted([b for b in df_mentah['BISNIS UNIT'].dropna().unique() if b and b not in ['BU LAINNYA', 'NONE']])
list_fra = sorted([f for f in df_mentah['FRA'].dropna().unique() if f and f != 'NONE'])

pilih_tahun = st.sidebar.selectbox("📅 Pilih Tahun", ["Semua Tahun"] + tahun_tersedia)
pilih_bulan = st.sidebar.selectbox("🗓️ Pilih Bulan", ["Semua Bulan"] + bulan_tersedia)
st.sidebar.markdown("---")
pilih_bu = st.sidebar.selectbox("🏢 Filter Bisnis Unit", ["Semua Bisnis Unit"] + list_bu)
pilih_fra = st.sidebar.selectbox("🧑‍💼 Filter Area (FRA)", ["Semua Area"] + list_fra)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style='text-align: center; margin-top: 20px; padding: 15px; border-radius: 10px; background-color: #f1f5f9; border-left: 4px solid #1E3A8A;'>
        <span style='font-size: 12px; color: #64748b;'>⚡ Powered & Developed by:</span><br>
        <strong style='font-size: 15px; color: #0f172a;'>M Khadafi Zainal</strong><br>
        <span style='font-size: 13px; color: #3b82f6; font-weight: 500;'>Finance Representative</span>
    </div>
    """, 
    unsafe_allow_html=True
)

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
        <div class="metric-box"><div class="metric-title">Total Kunjungan</div><div class="metric-value">{total_visit}</div><div class="metric-sub">Toko diaudit pada filter ini</div></div>
        <div class="metric-box alert"><div class="metric-title">Kasus Temuan</div><div class="metric-value">{total_temuan}</div><div class="metric-sub">Rincian isu operasional</div></div>
        <div class="metric-box alert"><div class="metric-title">Toko Bermasalah</div><div class="metric-value">{toko_unik_bermasalah}</div><div class="metric-sub">Toko unik memiliki temuan</div></div>
        <div class="metric-box {'alert' if rasio_temuan > 30 else 'success'}"><div class="metric-title">Defect Rate</div><div class="metric-value">{rasio_temuan:.1f}%</div><div class="metric-sub">Tingkat cacat operasional</div></div>
    </div>
''', unsafe_allow_html=True)

if total_temuan == 0:
    st.success("🎉 Luar biasa! Tidak ada data temuan. Operasional berjalan bersih.")
    st.stop()

# ==========================================
# 6. TAB NAVIGASI ANALISA
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Eksekutif", "🎯 Analisa Mendalam", "📂 Arsip Data (Detail)"])

with tab1:
    col_chart1, col_chart2 = st.columns([6, 4])
    with col_chart1:
        st.markdown("#### Distribusi Kategori Temuan Utama")
        top_kategori = df_temuan['Kategori Temuan'].value_counts().reset_index()
        top_kategori.columns = ['Kategori', 'Jumlah']
        top_kategori['Persentase'] = (top_kategori['Jumlah'] / total_temuan * 100).round(1)
        top_kategori['Label Teks'] = top_kategori['Jumlah'].astype(str) + " kasus (" + top_kategori['Persentase'].astype(str) + "%)"
        top_kategori = top_kategori.sort_values('Jumlah', ascending=True)
        fig_bar = px.bar(top_kategori, x='Persentase', y='Kategori', orientation='h', text='Label Teks', color_discrete_sequence=['#2563eb'])
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=True, gridcolor='#f1f5f9', range=[0, top_kategori['Persentase'].max() * 1.3]), margin=dict(l=0, r=0, t=10, b=0), height=380)
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_chart2:
        st.markdown("#### Proporsi Kunjungan Bersih vs Bermasalah")
        kunjungan_bersih = total_visit - total_temuan if (total_visit - total_temuan) > 0 else 0
        fig_donut = px.pie(names=['Kunjungan Bersih', 'Ada Temuan'], values=[kunjungan_bersih, total_temuan], hole=0.6, color_discrete_sequence=['#10B981', '#E11D48'])
        fig_donut.update_traces(textinfo='percent', textfont_size=14, hoverinfo='label+value')
        fig_donut.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=380, showlegend=False)
        st.plotly_chart(fig_donut, use_container_width=True)

with tab2:
    st.markdown("#### 🚨 Rapor Beban Temuan Berdasarkan Bisnis Unit (BU)")
    bu_counts = df_temuan['BISNIS UNIT'].value_counts().reset_index()
    bu_counts.columns = ['Bisnis Unit', 'Total Temuan']
    fig_bu = px.bar(bu_counts, x='Bisnis Unit', y='Total Temuan', text='Total Temuan', color='Total Temuan', color_continuous_scale='Blues')
    fig_bu.update_traces(textposition='outside')
    fig_bu.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor='rgba(0,0,0,0)', showlegend=False, coloraxis_showscale=False, height=300)
    st.plotly_chart(fig_bu, use_container_width=True)
    
    st.markdown("---")
    col_deep1, col_deep2 = st.columns(2)
    with col_deep1:
        st.markdown("#### 🚨 Kinerja Area (Top FRA Bermasalah)")
        fra_counts = df_temuan['FRA'].value_counts().reset_index().head(10)
        fra_counts.columns = ['Nama FRA', 'Total Temuan']
        fig_fra = px.bar(fra_counts, x='Nama FRA', y='Total Temuan', text='Total Temuan', color='Total Temuan', color_continuous_scale='Reds')
        fig_fra.update_traces(textposition='outside')
        fig_fra.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor='rgba(0,0,0,0)', showlegend=False, coloraxis_showscale=False, height=350)
        st.plotly_chart(fig_fra, use_container_width=True)
    with col_deep2:
        st.markdown("#### 🏪 Top 10 Toko Kritis")
        store_counts = df_temuan.groupby(['BISNIS UNIT', 'KODE STORE', 'NAMA STORE']).size().reset_index(name='Jumlah Temuan')
        store_counts = store_counts.sort_values(['Jumlah Temuan', 'BISNIS UNIT'], ascending=[False, True]).head(10)
        st.dataframe(store_counts, hide_index=True, use_container_width=True)

# Membuat Variabel df_tampil agar bisa dibaca oleh AI
df_tampil = df_temuan[['BISNIS UNIT', 'FRA', 'KODE STORE', 'NAMA STORE', 'TANGGAL', 'DETAIL TEMUAN', 'Kategori Temuan']]
df_tampil = df_tampil.sort_values(by=['BISNIS UNIT', 'FRA', 'KODE STORE'])

with tab3:
    st.markdown("#### 📂 Arsip Detail Temuan")
    st.dataframe(df_tampil, hide_index=True, use_container_width=True)

# ==========================================
# 7. ASISTEN AI (Bicara dengan Data via LANGCHAIN & GROQ)
# ==========================================
st.markdown("---")
st.markdown("#### 🤖 Asisten AI Executive (Tanya Jawab Data)")
st.caption("Ketik pertanyaan Anda (misal: 'Sebutkan 3 toko yang paling parah masalah brankasnya!').")

if "GROQ_API_KEY" in st.secrets:
    try:
        from langchain_groq import ChatGroq
        from langchain_experimental.agents import create_pandas_dataframe_agent
        
        # 1. Menghubungkan ke Otak Groq Model Terbaru Aktif
        llm = ChatGroq(
            groq_api_key=st.secrets["GROQ_API_KEY"], 
            model_name="openai/gpt-oss-120b", 
            temperature=0
        )
        
        # 2. Membuat Agen Pembaca Data
        agen_data = create_pandas_dataframe_agent(
            llm, 
            df_tampil, 
            verbose=False, 
            allow_dangerous_code=True
        )
        
        # 3. Membuat Kotak Chat
        pertanyaan = st.chat_input("Tanyakan sesuatu tentang data di atas...")
        
        if pertanyaan:
            with st.chat_message("user"):
                st.write(pertanyaan)
            
            with st.chat_message("assistant"):
                with st.spinner('AI sedang membaca tabel Anda secara mendalam...'):
                    # Trik Bahasa Indonesia
                    instruksi_rahasia = pertanyaan + " (Jawablah wajib dalam Bahasa Indonesia yang baik, sopan, dan jelas. Hanya gunakan data dari dataframe yang diberikan)."
                    
                    # Meminta AI menjawab
                    respon = agen_data.invoke(instruksi_rahasia)
                    
                    # Menampilkan hasil
                    if "output" in respon:
                        st.write(respon["output"])
                    else:
                        st.write("Maaf, AI tidak menemukan kesimpulan yang cocok dari pertanyaan Anda.")
    
    except Exception as e:
        st.error(f"Sistem AI mengalami kendala teknis: {e}")
else:
    st.warning("⚠️ Kunci GROQ_API_KEY belum dipasang di menu Settings > Secrets Streamlit.")
