import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. KONFIGURASI & TEMA DASHBOARD (HIGH CONTRAST)
# ==========================================
st.set_page_config(page_title="Dashboard Analisa Temuan", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown('''
    <style>
    /* Styling Teks Lebih Gelap & Terbaca Jelas */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #0f172a; }
    
    .kpi-container { display: flex; gap: 20px; margin-bottom: 30px; }
    .kpi-card { 
        background: #ffffff; 
        border: 1px solid #cbd5e1; 
        padding: 24px; 
        border-radius: 12px; 
        width: 100%; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: #1E3A8A;
    }
    .kpi-card.alert::before { background: #E11D48; }
    .kpi-card.success::before { background: #10B981; }
    
    .kpi-label { font-size: 13px; font-weight: 800; color: #1e293b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
    .kpi-value { font-size: 32px; font-weight: 800; color: #000000; line-height: 1.2; }
    .kpi-desc { font-size: 13px; font-weight: 600; color: #334155; margin-top: 6px; }
    
    .rekomendasi-box { 
        background-color: #f8fafc; 
        border: 1px solid #94a3b8; 
        border-left: 4px solid #2563eb; 
        padding: 20px 24px; 
        border-radius: 8px; 
        margin-bottom: 25px; 
        font-size: 15px; 
        line-height: 1.7; 
        color: #0f172a; 
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
    st.error("Gagal membaca sambungan data.")
    st.stop()

# ==========================================
# 3. KATEGORISASI (ENGINE LOGIKA KOSONG)
# ==========================================
def deteksi_kategori(teks):
    # Jika kosong atau bernilai null, dianggap tidak ada temuan
    if not teks or pd.isna(teks) or str(teks).strip() == "": return None
    
    teks_upper = str(teks).upper()
    # Logika filter untuk store yang aman / tidak ada temuan
    kata_aman = ["TIDAK ADA", "-", "0", "–", "NIHIL", "AMAN", "TDK ADA", "KOSONG", "TIDAK DIISI", "TIDAK ADA TEMUAN"]
    if any(x in teks_upper for x in kata_aman): return None
    
    # Logika klasifikasi temuan
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
st.sidebar.markdown("<h3 style='color:#0f172a; font-weight:800;'>🎛️ Panel Analisa Data</h3>", unsafe_allow_html=True)

urutan_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
bulan_tersedia = [b for b in urutan_bulan if b in df_mentah['Bulan'].unique()]
tahun_tersedia = sorted(df_mentah[df_mentah['Tahun'] != 'Unknown']['Tahun'].unique(), reverse=True)

list_bu = sorted([b for b in df_mentah['BISNIS UNIT'].dropna().unique() if b and b != 'NONE'])
list_fra = sorted([f for f in df_mentah['FRA'].dropna().unique() if f and f != 'NONE'])

pilih_tahun = st.sidebar.selectbox("📅 Tahun Data", ["Semua Tahun"] + tahun_tersedia)
pilih_bulan = st.sidebar.selectbox("🗓️ Bulan Data", ["Semua Bulan"] + bulan_tersedia)
st.sidebar.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
pilih_bu = st.sidebar.selectbox("🏢 Unit Bisnis (BU)", ["Semua Bisnis Unit"] + list_bu)
pilih_fra = st.sidebar.selectbox("🧑‍💼 Area (FRA)", ["Semua Area"] + list_fra)

st.sidebar.markdown(
    """
    <div style='text-align: center; margin-top: 30px; padding: 18px; border-radius: 8px; background: #f1f5f9; border: 1px solid #cbd5e1;'>
        <div style='font-size: 10px; color: #475569; font-weight:800; letter-spacing:1px; margin-bottom:5px;'>POWERED & DEVELOPED BY</div>
        <div style='font-size: 16px; color: #000000; font-weight: 800;'>M Khadafi Zainal</div>
        <div style='font-size: 13px; color: #1E3A8A; font-weight: 700; margin-top:2px;'>Finance Representative</div>
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
st.markdown("<h2 style='color:#000000; font-weight:800; margin-bottom:5px;'>Dashboard Analisa Temuan Visit Store</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#1e293b; font-size:16px; font-weight:500; margin-bottom:30px;'>Laporan analitik data temuan operasional lapangan berdasarkan visit cabang.</p>", unsafe_allow_html=True)

st.markdown(f'''
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">Total Visit</div>
            <div class="kpi-value">{total_visit}</div>
            <div class="kpi-desc">Total kunjungan audit</div>
        </div>
        <div class="kpi-card alert">
            <div class="kpi-label">Volume Temuan</div>
            <div class="kpi-value">{total_temuan}</div>
            <div class="kpi-desc">Total rincian isu tercatat</div>
        </div>
        <div class="kpi-card alert">
            <div class="kpi-label">Toko dengan Temuan</div>
            <div class="kpi-value">{toko_dengan_temuan}</div>
            <div class="kpi-desc">Toko unik yang memiliki data temuan</div>
        </div>
        <div class="kpi-card {'alert' if rasio_temuan > 30 else 'success'}">
            <div class="kpi-label">Rasio Temuan (Defect)</div>
            <div class="kpi-value">{rasio_temuan:.1f}%</div>
            <div class="kpi-desc">Persentase temuan terhadap total visit</div>
        </div>
    </div>
''', unsafe_allow_html=True)

if total_temuan == 0:
    st.success("Tabel Data Kosong: Berdasarkan filter yang Anda pilih, tidak ditemukan data temuan operasional.")
    st.stop()

# ==========================================
# 6. ANALYTICS TABS 
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Analisa Kategori", "🏢 Analisa Area & Toko", "📋 Arsip & Rekomendasi"])

# --- TAB 1 ---
with tab1:
    col_chart1, col_chart2 = st.columns([6, 4])
    with col_chart1:
        st.markdown("<h4 style='color:#0f172a; font-weight:800;'>Distribusi Data Kategori Temuan</h4>", unsafe_allow_html=True)
        top_kategori = df_temuan['Kategori Temuan'].value_counts().reset_index()
        top_kategori.columns = ['Kategori', 'Jumlah']
        top_kategori['Persentase'] = (top_kategori['Jumlah'] / total_temuan * 100).round(1)
        top_kategori['Label'] = top_kategori['Jumlah'].astype(str) + " (" + top_kategori['Persentase'].astype(str) + "%)"
        top_kategori = top_kategori.sort_values('Jumlah', ascending=True)
        
        fig_bar = px.bar(top_kategori, x='Persentase', y='Kategori', orientation='h', text='Label')
        fig_bar.update_traces(marker_color='#1E3A8A', textposition='outside', textfont=dict(color='#0f172a', size=13, weight='bold'))
        fig_bar.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', xaxis_title="", yaxis_title="", xaxis=dict(showgrid=True, gridcolor='#e2e8f0', range=[0, top_kategori['Persentase'].max() * 1.3]), margin=dict(l=0, r=0, t=10, b=0), height=380)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        st.markdown("<h4 style='color:#0f172a; font-weight:800;'>Proporsi Data Temuan Visit</h4>", unsafe_allow_html=True)
        kunjungan_bersih = total_visit - total_temuan if (total_visit - total_temuan) > 0 else 0
        fig_donut = px.pie(names=['Toko Tanpa Temuan', 'Terdapat Temuan'], values=[kunjungan_bersih, total_temuan], hole=0.65)
        fig_donut.update_traces(marker=dict(colors=['#10B981', '#E11D48']), textinfo='percent', textfont_size=15, hoverinfo='label+value')
        fig_donut.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=380, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))
        st.plotly_chart(fig_donut, use_container_width=True)

# --- TAB 2 ---
with tab2:
    # Menghapus Diagram BU yang mengganggu, menyisakan FRA dan Tabel
    col_deep1, col_deep2 = st.columns(2)
    
    with col_deep1:
        st.markdown("<h4 style='color:#0f172a; font-weight:800;'>Frekuensi Temuan Berdasarkan Area (FRA)</h4>", unsafe_allow_html=True)
        fra_counts = df_temuan['FRA'].value_counts().reset_index().head(10)
        fra_counts.columns = ['Nama FRA', 'Total Temuan']
        
        fig_fra = px.bar(fra_counts, x='Nama FRA', y='Total Temuan', text='Total Temuan')
        fig_fra.update_traces(marker_color='#1E3A8A', textposition='outside', textfont=dict(size=14, color='#0f172a', weight='bold'))
        fig_fra.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', xaxis_title="", yaxis_title="", margin=dict(t=10, b=0), height=400)
        st.plotly_chart(fig_fra, use_container_width=True)

    with col_deep2:
        st.markdown("<h4 style='color:#0f172a; font-weight:800;'>Daftar Toko dengan Temuan Terbanyak</h4>", unsafe_allow_html=True)
        store_counts = df_temuan.groupby(['BISNIS UNIT', 'KODE STORE', 'NAMA STORE']).size().reset_index(name='Frekuensi Temuan')
        store_counts = store_counts.sort_values(['Frekuensi Temuan', 'BISNIS UNIT'], ascending=[False, True]).head(10)
        
        st.dataframe(
            store_counts,
            column_config={
                "BISNIS UNIT": st.column_config.TextColumn("BU", width="small"),
                "KODE STORE": st.column_config.TextColumn("Kode", width="small"),
                "NAMA STORE": st.column_config.TextColumn("Nama Cabang", width="medium"),
                "Frekuensi Temuan": st.column_config.ProgressColumn("Total Data", format="%d", min_value=0, max_value=int(store_counts['Frekuensi Temuan'].max()))
            },
            hide_index=True, use_container_width=True, height=400
        )

# --- TAB 3 ---
df_tampil = df_temuan[['BISNIS UNIT', 'FRA', 'KODE STORE', 'NAMA STORE', 'TANGGAL', 'DETAIL TEMUAN', 'Kategori Temuan']]
df_tampil = df_tampil.sort_values(by=['BISNIS UNIT', 'FRA', 'KODE STORE'])

with tab3:
    st.markdown("<h4 style='color:#0f172a; font-weight:800;'>Analitik Data & Rekomendasi Standar</h4>", unsafe_allow_html=True)
    
    top_masalah = top_kategori.iloc[-1]['Kategori']
    persen_masalah = top_kategori.iloc[-1]['Persentase']
    top_fra = fra_counts.iloc[0]['Nama FRA'] if not fra_counts.empty else "N/A"
    
    st.markdown(f'''
        <div class="rekomendasi-box">
            Berdasarkan matriks data pada filter ini, rasio temuan tercatat pada angka <b>{rasio_temuan:.1f}%</b>. 
            Data historis menunjukkan bahwa kategori <b>{top_masalah}</b> menyumbang frekuensi tertinggi (<b>{persen_masalah}%</b>) dari keseluruhan temuan yang ada.<br><br>
            Jika ditinjau dari wilayah pengelolaan (FRA), area <b>{top_fra}</b> mencatatkan akumulasi data temuan tertinggi dan dapat menjadi fokus utama untuk analisa lebih lanjut.
        </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("<h5 style='color:#000000; font-weight:800; margin-top:15px;'>Rekomendasi Operasional:</h5>", unsafe_allow_html=True)
    
    if "SELISIH UANG" in top_masalah:
        st.warning("""1. **Validasi Kas Fisik:** Mengagendakan proses cash opname secara acak pada saat pergantian shift.\n2. **Kepatuhan Administrasi:** Memastikan seluruh form serah terima dana ditandatangani sesuai SOP yang berlaku.\n3. **Monitoring Fasilitas:** Mengevaluasi fungsi dan arah sorotan CCTV di area mesin kasir.""")
    elif "STB" in top_masalah:
        st.info("""1. **SOP Setoran:** Memastikan seluruh setoran bank (STB) diselesaikan selambatnya H+1.\n2. **Verifikasi Data:** Meminta validasi bukti transfer/resi melalui grup komunikasi operasional area.\n3. **Tinjauan Kebijakan:** Melakukan review performa toko yang memiliki frekuensi keterlambatan STB tinggi.""")
    elif "BRANKAS" in top_masalah:
        st.error("""1. **Protokol Kombinasi Sandi:** Merekomendasikan pembaruan PIN brankas secara berkala atau pasca mutasi personel.\n2. **Otorisasi Akses:** Mengontrol dengan ketat pembagian anak kunci fisik hanya kepada personel yang berwenang.\n3. **Pengecekan Fisik:** Melakukan verifikasi rutin bahwa pintu brankas tidak dalam posisi sengaja dibiarkan terbuka.""")
    elif "NOTA" in top_masalah:
        st.info("""1. **Manajemen Arsip:** Mengoptimalkan penggunaan alat pengarsipan (bantex/map) yang diindeks berdasarkan tanggal.\n2. **Validasi Digital:** Mendorong digitalisasi data nota melalui perangkat operasional sebelum nota fisik dikirim.\n3. **Audit Kelengkapan:** Menjadikan pengecekan kesesuaian bon pengeluaran sebagai standar prosedur visit.""")
    elif "KASBON" in top_masalah:
        st.error("""1. **Sosialisasi Ulang:** Memberikan penegasan terkait kebijakan perusahaan yang melarang penggunaan dana operasional untuk kepentingan di luar prosedur.\n2. **Koordinasi Keuangan:** Melakukan rekonsiliasi data dengan tim terkait untuk menindaklanjuti status kasbon yang menggantung.\n3. **Monitoring Area:** Menginstruksikan FRA untuk mengawasi ketat pergerakan Petty Cash harian.""")
    else:
        st.success("""1. **Refreshment Materi:** Menjadwalkan pelatihan penyegaran terkait prosedur operasional kepada jaringan toko.\n2. **Fokus Audit:** Menyesuaikan poin evaluasi pada lembar kerja audit FRA dengan tren temuan terbaru.\n3. **Analisa Performa:** Mengaitkan data tingkat penyelesaian temuan operasional dengan indikator penilaian kinerja (KPI).""")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#0f172a; font-weight:800;'>Tabel Arsip Data Temuan</h4>", unsafe_allow_html=True)
    
    st.dataframe(
        df_tampil,
        column_config={
            "BISNIS UNIT": st.column_config.TextColumn("BU", width="small"),
            "FRA": st.column_config.TextColumn("Nama FRA", width="small"),
            "KODE STORE": st.column_config.TextColumn("Kode", width="small"),
            "NAMA STORE": st.column_config.TextColumn("Nama Cabang", width="medium"),
            "TANGGAL": st.column_config.TextColumn("Tanggal Audit"),
            "DETAIL TEMUAN": st.column_config.TextColumn("Deskripsi Detail", width="large"),
            "Kategori Temuan": st.column_config.TextColumn("Kategori Data")
        },
        hide_index=True, use_container_width=True
    )

# ==========================================
# 7. AI ASISTEN (CHAT)
# ==========================================
st.markdown("<hr style='margin-top: 40px;'>", unsafe_allow_html=True)
st.markdown("<h3 style='color:#000000; font-weight:800;'>🤖 AI Asisten</h3>", unsafe_allow_html=True)
st.caption("Saya adalah asisten M Khadafi dan siap menjawab pertanyaan tentang data yang ditampilkan.")

if "GROQ_API_KEY" in st.secrets:
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage, SystemMessage
        
        llm = ChatGroq(
            groq_api_key=st.secrets["GROQ_API_KEY"], 
            model_name="llama3-8b-8192", 
            temperature=0.1
        )
        
        data_ringkas = df_tampil.head(30).to_markdown(index=False)
        pertanyaan = st.chat_input("Ketik pertanyaan Anda di sini...")
        
        if pertanyaan:
            with st.chat_message("user"):
                st.write(pertanyaan)
            
            with st.chat_message("assistant"):
                with st.spinner('Memproses analisa data...'):
                    
                    system_prompt = (
                        "Anda adalah AI Asisten untuk M Khadafi yang mengelola data analisa operasional toko. "
                        "Berikut adalah cuplikan data temuan operasional:\n\n"
                        f"{data_ringkas}\n\n"
                        "Tugas Anda: Jawab pertanyaan analitik berdasarkan data tabel tersebut.\n"
                        "ATURAN MUTLAK:\n"
                        "1. DILARANG menggunakan kata 'bermasalah', 'kritis', atau 'perlu atensi'. \n"
                        "2. Gunakan istilah objektif seperti 'toko dengan temuan', 'frekuensi temuan', atau 'analisa data'. \n"
                        "3. Jawablah menggunakan Bahasa Indonesia yang sangat rapi, analitis, sopan, dan netral."
                    )
                    
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=pertanyaan)
                    ]
                    
                    response = llm.invoke(messages)
                    st.write(response.content)
                    
    except Exception as e:
        st.error(f"Koneksi AI mengalami kendala teknis: {e}")
else:
    st.warning("⚠️ Kunci GROQ_API_KEY belum dikonfigurasi di menu Settings > Secrets Streamlit.")
