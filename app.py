import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. KONFIGURASI & TEMA DASHBOARD PROFESIONAL
# ==========================================
st.set_page_config(page_title="Executive Dashboard - Analisa Visit", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown('''
    <style>
    .metric-container { display: flex; justify-content: space-between; gap: 15px; margin-bottom: 25px; }
    .metric-box { background-color: #ffffff; border: 1px solid #cbd5e1; padding: 20px; border-radius: 10px; width: 100%; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border-top: 5px solid #1E3A8A; }
    .metric-box.alert { border-top-color: #E11D48; }
    .metric-box.success { border-top-color: #10B981; }
    .metric-title { font-size: 13px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
    .metric-value { font-size: 28px; font-weight: 800; color: #0f172a; }
    .metric-sub { font-size: 12px; font-weight: 600; color: #64748b; margin-top: 5px;}
    .rekomendasi-box { background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 5px solid #2563eb; padding: 18px 22px; border-radius: 8px; margin-bottom:20px; color: #1e293b; font-size: 14px; line-height: 1.6; }
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
# 4. SIDEBAR - PANEL FILTER & CREDENTIALS
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
    <div style='text-align: center; margin-top: 15px; padding: 15px; border-radius: 10px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #1E3A8A;'>
        <span style='font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase;'>⚡ Powered & Developed by:</span><br>
        <strong style='font-size: 15px; color: #0f172a;'>M Khadafi Zainal</strong><br>
        <span style='font-size: 12px; color: #2563eb; font-weight: 700;'>Finance Representative</span>
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
toko_kritis = df_temuan['NAMA STORE'].nunique()
rasio_temuan = (total_temuan / total_visit * 100) if total_visit > 0 else 0

# ==========================================
# 5. HEADER & KPI METRICS (HIGH CONTRAST)
# ==========================================
st.markdown("<h2 style='color:#0f172a; font-weight:800; margin-bottom:0px;'>📈 Executive Dashboard: Visit Operations</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#475569; font-weight:500; margin-bottom:25px;'>Analisa mendalam temuan operasional lapangan untuk mendukung keputusan strategis perusahaan.</p>", unsafe_allow_html=True)

st.markdown(f'''
    <div class="metric-container">
        <div class="metric-box">
            <div class="metric-title">Total Kunjungan (Visit)</div>
            <div class="metric-value">{total_visit}</div>
            <div class="metric-sub">Total audit toko terekam</div>
        </div>
        <div class="metric-box alert">
            <div class="metric-title">Kasus Temuan</div>
            <div class="metric-value">{total_temuan}</div>
            <div class="metric-sub">Total rincian isu operasional</div>
        </div>
        <div class="metric-box alert">
            <div class="metric-title">Toko dengan Temuan</div>
            <div class="metric-value">{toko_kritis}</div>
            <div class="metric-sub">Jumlah toko memerlukan atensi</div>
        </div>
        <div class="metric-box {'alert' if rasio_temuan > 30 else 'success'}">
            <div class="metric-title">Defect Rate (Rasio Isu)</div>
            <div class="metric-value">{rasio_temuan:.1f}%</div>
            <div class="metric-sub">Tingkat penyimpangan audit</div>
        </div>
    </div>
''', unsafe_allow_html=True)

if total_temuan == 0:
    st.success("🎉 Luar biasa! Tidak ada data temuan operasional pada filter yang Anda pilih. Operasional berjalan bersih.")
    st.stop()

# ==========================================
# 6. TAB NAVIGASI ANALISA (PROFESIONAL LAYOUT)
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Eksekutif", "🎯 Analisa Mendalam & Tabel Rekap", "📂 Arsip Data Korporat"])

with tab1:
    col_chart1, col_chart2 = st.columns([6, 4])
    with col_chart1:
        st.markdown("#### **Distribusi Kategori Temuan Utama**")
        top_kategori = df_temuan['Kategori Temuan'].value_counts().reset_index()
        top_kategori.columns = ['Kategori', 'Jumlah']
        top_kategori['Persentase'] = (top_kategori['Jumlah'] / total_temuan * 100).round(1)
        top_kategori['Label Teks'] = top_kategori['Jumlah'].astype(str) + " kasus (" + top_kategori['Persentase'].astype(str) + "%)"
        top_kategori = top_kategori.sort_values('Jumlah', ascending=True)
        
        fig_bar = px.bar(top_kategori, x='Persentase', y='Kategori', orientation='h', text='Label Teks', color_discrete_sequence=['#1E3A8A'])
        fig_bar.update_traces(textposition='outside', textfont=dict(size=12, color='#0f172a', family='sans-serif'))
        fig_bar.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=True, gridcolor='#e2e8f0', range=[0, top_kategori['Persentase'].max() * 1.3]), margin=dict(l=0, r=0, t=10, b=0), height=380)
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_chart2:
        st.markdown("#### **Proporsi Kunjungan Bersih vs Temuan**")
        kunjungan_bersih = total_visit - total_temuan if (total_visit - total_temuan) > 0 else 0
        fig_donut = px.pie(names=['Kunjungan Bersih', 'Ada Temuan'], values=[kunjungan_bersih, total_temuan], hole=0.6, color_discrete_sequence=['#10B981', '#E11D48'])
        fig_donut.update_traces(textinfo='percent', textfont_size=14, hoverinfo='label+value')
        fig_donut.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=380, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))
        st.plotly_chart(fig_donut, use_container_width=True)

with tab2:
    st.markdown("#### **Rapor Kinerja & Beban Temuan per Bisnis Unit**")
    bu_summary = df_temuan.groupby('BISNIS UNIT').agg(
        Total_Temuan=('DETAIL TEMUAN', 'count'),
        Toko_Kritis=('NAMA STORE', 'nunique')
    ).reset_index().sort_values(by='Total_Temuan', ascending=False)
    
    fig_bu = px.bar(bu_summary, x='BISNIS UNIT', y='Total_Temuan', text='Total_Temuan', color='Total_Temuan', color_continuous_scale='Blues')
    fig_bu.update_traces(textposition='outside', textfont=dict(size=12, color='#0f172a'))
    fig_bu.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor='rgba(0,0,0,0)', showlegend=False, coloraxis_showscale=False, height=300)
    st.plotly_chart(fig_bu, use_container_width=True)
    
    st.markdown("---")
    col_deep1, col_deep2 = st.columns(2)
    with col_deep1:
        st.markdown("#### **Top Area (FRA) dengan Temuan Terbanyak**")
        fra_counts = df_temuan['FRA'].value_counts().reset_index().head(10)
        fra_counts.columns = ['Nama FRA', 'Total Temuan']
        
        fig_fra = px.bar(fra_counts, x='Nama FRA', y='Total Temuan', text='Total Temuan', color='Total Temuan', color_continuous_scale='Reds')
        fig_fra.update_traces(textposition='outside', textfont=dict(size=12, color='#0f172a'))
        fig_fra.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor='rgba(0,0,0,0)', showlegend=False, coloraxis_showscale=False, height=350)
        st.plotly_chart(fig_fra, use_container_width=True)
        
    with col_deep2:
        st.markdown("#### **Tabel Rekapitulasi Toko Kritis (Top 10)**")
        store_counts = df_temuan.groupby(['BISNIS UNIT', 'KODE STORE', 'NAMA STORE']).size().reset_index(name='Frekuensi Temuan')
        store_counts = store_counts.sort_values(['Frekuensi Temuan', 'BISNIS UNIT'], ascending=[False, True]).head(10)
        
        st.dataframe(
            store_counts,
            column_config={
                "BISNIS UNIT": st.column_config.TextColumn("Bisnis Unit", width="small"),
                "KODE STORE": st.column_config.TextColumn("Kode Toko", width="small"),
                "NAMA STORE": st.column_config.TextColumn("Nama Toko Korporat", width="medium"),
                "Frekuensi Temuan": st.column_config.ProgressColumn("Frekuensi Isu", format="%d", min_value=0, max_value=int(store_counts['Frekuensi Temuan'].max()))
            },
            hide_index=True, use_container_width=True
        )

# Variabel arsip data bersih untuk tabel dan AI
df_tampil = df_temuan[['BISNIS UNIT', 'FRA', 'KODE STORE', 'NAMA STORE', 'TANGGAL', 'DETAIL TEMUAN', 'Kategori Temuan']]
df_tampil = df_tampil.sort_values(by=['BISNIS UNIT', 'FRA', 'KODE STORE'])

with tab3:
    st.markdown("#### **Arsip Database Korporat - Temuan Operasional Lapangan**")
    st.dataframe(
        df_tampil,
        column_config={
            "BISNIS UNIT": st.column_config.TextColumn("BU"),
            "FRA": st.column_config.TextColumn("FRA"),
            "KODE STORE": st.column_config.TextColumn("Kode"),
            "NAMA STORE": st.column_config.TextColumn("Nama Toko"),
            "TANGGAL": st.column_config.TextColumn("Tanggal Audit"),
            "DETAIL TEMUAN": st.column_config.TextColumn("Detail Isu Temuan"),
            "Kategori Temuan": st.column_config.TextColumn("Klasifikasi Kategori")
        },
        hide_index=True, use_container_width=True
    )

# ==========================================
# 7. ASISTEN AI EXECUTIVE (DIRECT LLM / STABLE)
# ==========================================
st.markdown("---")
st.markdown("#### 🤖 Asisten AI Executive (Tanya Jawab Data Korporat)")
st.caption("Ketik pertanyaan Anda (misal: 'Ringkas temuan isu yang paling sering terjadi pada Bisnis Unit dan berikan rekomendasi perbaikannya!').")

if "GROQ_API_KEY" in st.secrets:
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage, SystemMessage
        
        llm = ChatGroq(
            groq_api_key=st.secrets["GROQ_API_KEY"], 
            model_name="openai/gpt-oss-120b", 
            temperature=0.1
        )
        
        data_ringkas = df_tampil.head(50).to_markdown(index=False)
        pertanyaan = st.chat_input("Tanyakan sesuatu tentang data di atas...")
        
        if pertanyaan:
            with st.chat_message("user"):
                st.write(pertanyaan)
            
            with st.chat_message("assistant"):
                with st.spinner('AI sedang menganalisa data korporat...'):
                    
                    system_prompt = (
                        "Anda adalah seorang Asisten AI Eksekutif korporat yang cerdas, profesional, dan berwibawa. "
                        "Berikut adalah data laporan temuan operasional toko:\n\n"
                        f"{data_ringkas}\n\n"
                        "Tugas Anda adalah menjawab pertanyaan dari manajemen berdasarkan data tabel di atas. "
                        "Gunakan istilah korporat yang sopan (hindari kata kasar atau kata 'bermasalah', gunakan 'toko kritis' atau 'toko dengan temuan'). "
                        "Jawablah dengan ringkas, akurat, dan wajib menggunakan Bahasa Indonesia yang profesional."
                    )
                    
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=pertanyaan)
                    ]
                    
                    response = llm.invoke(messages)
                    st.write(response.content)
                    
    except Exception as e:
        st.error(f"Sistem AI mengalami kendala teknis: {e}")
else:
    st.warning("⚠️ Kunci GROQ_API_KEY belum dipasang di menu Settings > Secrets Streamlit.")
