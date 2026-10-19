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
            <div class="kpi-desc">Cabang unik dengan catatan temuan</div>
        </div>
        <div class="kpi-card {'alert' if rasio_temuan > 30 else 'success'}">
            <div class="kpi-label">Rasio Temuan (Defect Rate)</div>
            <div class="kpi-value">{rasio_temuan:.1f}%</div>
            <div class="kpi-desc">Persentase temuan terhadap visit</div>
        </div>
    </div>
''', unsafe_allow_html=True)

if total_temuan == 0:
    st.success("Informasi: Berdasarkan filter yang Anda pilih, tidak ditemukan data anomali atau temuan operasional.")
    st.stop()

# ==========================================
# 6. ANALYTICS TABS 
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Analisa Kategori", "🏢 Analisa Area & Toko", "📋 Arsip & Rekomendasi"])

with tab1:
    col_chart1, col_chart2 = st.columns([6, 4])
    with col_chart1:
        st.markdown("<h4 style='color:#0f172a; font-weight:700; font-size:16px;'>Distribusi Kategori Temuan Operasional</h4>", unsafe_allow_html=True)
        top_kategori = df_temuan['Kategori Temuan'].value_counts().reset_index()
        top_kategori.columns = ['Kategori', 'Jumlah']
        top_kategori['Persentase'] = (top_kategori['Jumlah'] / total_temuan * 100).round(1)
        top_kategori['Label'] = top_kategori['Jumlah'].astype(str) + " kasus (" + top_kategori['Persentase'].astype(str) + "%)"
        top_kategori = top_kategori.sort_values('Jumlah', ascending=True)
        
        fig_bar = px.bar(top_kategori, x='Persentase', y='Kategori', orientation='h', text='Label')
        fig_bar.update_traces(marker_color='#1E3A8A', textposition='outside', textfont=dict(color='#0f172a', size=12, weight='bold'))
        fig_bar.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', xaxis_title="", yaxis_title="", xaxis=dict(showgrid=True, gridcolor='#e2e8f0', range=[0, top_kategori['Persentase'].max() * 1.3]), margin=dict(l=0, r=0, t=10, b=0), height=380)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        st.markdown("<h4 style='color:#0f172a; font-weight:700; font-size:16px;'>Proporsi Kepatuhan Audit Visit</h4>", unsafe_allow_html=True)
        kunjungan_bersih = total_visit - total_temuan if (total_visit - total_temuan) > 0 else 0
        fig_donut = px.pie(names=['Toko Tanpa Temuan', 'Terdapat Temuan'], values=[kunjungan_bersih, total_temuan], hole=0.65)
        fig_donut.update_traces(marker=dict(colors=['#10B981', '#E11D48']), textinfo='percent', textfont_size=14, hoverinfo='label+value')
        fig_donut.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=380, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))
        st.plotly_chart(fig_donut, use_container_width=True)

with tab2:
    col_deep1, col_deep2 = st.columns(2)
    
    with col_deep1:
        st.markdown("<h4 style='color:#0f172a; font-weight:700; font-size:16px;'>Frekuensi Temuan Berdasarkan Area (FRA)</h4>", unsafe_allow_html=True)
        fra_counts = df_temuan['FRA'].value_counts().reset_index().head(10)
        fra_counts.columns = ['Nama FRA', 'Total Temuan']
        
        fig_fra = px.bar(fra_counts, x='Nama FRA', y='Total Temuan', text='Total Temuan')
        fig_fra.update_traces(marker_color='#1E3A8A', textposition='outside', textfont=dict(size=13, color='#0f172a', weight='bold'))
        fig_fra.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', xaxis_title="", yaxis_title="", margin=dict(t=10, b=0), height=400)
        st.plotly_chart(fig_fra, use_container_width=True)

    with col_deep2:
        st.markdown("<h4 style='color:#0f172a; font-weight:700; font-size:16px;'>Daftar Cabang dengan Temuan Terbanyak</h4>", unsafe_allow_html=True)
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

df_tampil = df_temuan[['BISNIS UNIT', 'FRA', 'KODE STORE', 'NAMA STORE', 'TANGGAL', 'DETAIL TEMUAN', 'Kategori Temuan']]
df_tampil = df_tampil.sort_values(by=['BISNIS UNIT', 'FRA', 'KODE STORE'])

with tab3:
    st.markdown("<h4 style='color:#0f172a; font-weight:700; font-size:16px;'>Analisis & Rekomendasi Tindakan</h4>", unsafe_allow_html=True)
    
    top_masalah = top_kategori.iloc[-1]['Kategori']
    persen_masalah = top_kategori.iloc[-1]['Persentase']
    top_fra = fra_counts.iloc[0]['Nama FRA'] if not fra_counts.empty else "N/A"
    
    st.markdown(f'''
        <div class="rekomendasi-box">
            <b>Kesimpulan Analisis:</b> Berdasarkan filter saat ini, rasio temuan tercatat pada angka <b>{rasio_temuan:.1f}%</b>. 
            Kategori <b>{top_masalah}</b> mendominasi dengan kontribusi sebesar <b>{persen_masalah}%</b> dari total seluruh kasus yang tercatat.<br><br>
            Wilayah pengawasan di bawah area <b>{top_fra}</b> mencatatkan volume temuan tertinggi yang dapat dijadikan fokus evaluasi operasional berkala.
        </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("<h5 style='color:#0f172a; font-weight:700; font-size:15px; margin-top:15px;'>Rekomendasi Standar Operasional:</h5>", unsafe_allow_html=True)
    
    if "SELISIH UANG" in top_masalah:
        st.warning("1. **Validasi Kas Fisik:** Mengagendakan proses cash opname secara acak saat pergantian shift.\n2. **Kepatuhan SOP:** Memastikan seluruh form serah terima kas ditandatangani sesuai prosedur.\n3. **Audit Fasilitas:** Mengevaluasi sudut pandang kamera pengawas (CCTV) di area laci kasir.")
    elif "STB" in top_masalah:
        st.info("1. **Disiplin Setoran:** Menetapkan tenggat waktu (SLA) setoran bank (STB) selambatnya H+1.\n2. **Verifikasi Resi:** Mewajibkan pelaporan bukti setoran harian pada grup koordinasi area.\n3. **Evaluasi Berkala:** Memberikan atensi khusus pada cabang yang sering mengalami penundaan setoran.")
    elif "BRANKAS" in top_masalah:
        st.error("1. **Protokol Kombinasi:** Melakukan perubahan PIN brankas secara berkala atau ketika terjadi mutasi personel.\n2. **Pembatasan Akses:** Memastikan kunci dan akses brankas hanya dipegang oleh Person in Charge (PIC) berwenang.\n3. **Kepatuhan Fisik:** Memeriksa secara ketat agar pintu brankas tidak dibiarkan terbuka/tidak terkunci.")
    elif "NOTA" in top_masalah:
        st.info("1. **Sistem Pengarsipan:** Menyediakan map/binder khusus berindeks tanggal di setiap unit toko.\n2. **Digitalisasi Dokumen:** Mengunggah foto bon/nota transaksi ke sistem sebelum berkas fisik dikirimkan.\n3. **Pemeriksaan Rutin:** Menjadikan kelengkapan berkas administrasi sebagai item utama saat kunjungan audit.")
    elif "KASBON" in top_masalah:
        st.error("1. **Penegasan Kebijakan:** Mensosialisasikan kembali aturan larangan penggunaan dana operasional toko untuk kepentingan pribadi.\n2. **Koordinasi Finansial:** Bekerja ulang dengan departemen terkait untuk penyelesaian status kasbon menggantung.\n3. **Monitoring Petty Cash:** Mengawasi pergerakan kas kecil harian secara ketat di setiap cabang.")
    else:
        st.success("1. **Program Penyegaran (Refreshment):** Mengadakan sesi penyegaran SOP operasional bagi kepala toko.\n2. **Fokus Lembar Kerja Audit:** Menyesuaikan poin checklist visit lapangan dengan tren temuan terbaru.\n3. **Korelasi Kinerja:** Menyelaraskan catatan kepatuhan operasional dengan penilaian kinerja berkala.")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#0f172a; font-weight:700; font-size:16px;'>Tabel Arsip Data Temuan Operasional</h4>", unsafe_allow_html=True)
    
    st.dataframe(
        df_tampil,
        column_config={
            "BISNIS UNIT": st.column_config.TextColumn("BU", width="small"),
            "FRA": st.column_config.TextColumn("Nama FRA", width="small"),
            "KODE STORE": st.column_config.TextColumn("Kode", width="small"),
            "NAMA STORE": st.column_config.TextColumn("Nama Cabang", width="medium"),
            "TANGGAL": st.column_config.TextColumn("Tanggal Audit"),
            "DETAIL TEMUAN": st.column_config.TextColumn("Deskripsi Detail", width="large"),
            "Kategori Temuan": st.column_config.TextColumn("Klasifikasi Sistem")
        },
        hide_index=True, use_container_width=True
    )

# ==========================================
# 7. AI ASISTEN (CHAT - MIXTRAL 32K TERSTABIL)
# ==========================================
st.markdown("<hr style='margin-top: 40px;'>", unsafe_allow_html=True)
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
st.markdown("<h3 style='color:#020617; font-weight:800; font-size:20px; margin-bottom:5px;'>🤖 AI Asisten</h3>", unsafe_allow_html=True)
st.caption("Saya adalah asisten M Khadafi dan siap menjawab pertanyaan tentang data yang ditampilkan.")

if "GROQ_API_KEY" in st.secrets:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        # Mengambil seluruh data temuan, Mixtral memiliki kapasitas 32.000 token sehingga aman dari error panjang
        ringkasan_data = df_mentah[df_mentah['Ada Temuan'] == True].groupby(['Bulan', 'Tahun', 'BISNIS UNIT', 'FRA', 'NAMA STORE', 'Kategori Temuan', 'DETAIL TEMUAN']).size().reset_index(name='Jumlah')
        context_data = ringkasan_data.to_markdown(index=False)
        
        pertanyaan = st.chat_input("Ketik pertanyaan Anda di sini (Contoh: Apakah ada temuan yang sama pada September dan Oktober 2026?)...")
        
        if pertanyaan:
            with st.chat_message("user"):
                st.write(pertanyaan)
            
            with st.chat_message("assistant"):
                with st.spinner('AI sedang menganalisis data...'):
                    
                    system_prompt = (
                        "Anda adalah AI Asisten profesional untuk M Khadafi yang mengelola data analitik operasional toko. "
                        "Berikut adalah data statistik lengkap seluruh temuan operasional teragregasi:\n\n"
                        f"{context_data}\n\n"
                        "Tugas Anda: Jawab pertanyaan analitik pengguna secara rinci berdasarkan data tabel di atas. "
                        "Jika pengguna menanyakan perbandingan antar bulan (seperti September dan Oktober 2026), teliti kolom Bulan, NAMA STORE, dan Kategori/Detail Temuan secara cermat untuk mendeteksi apakah ada kasus temuan yang berulang, sama, atau polanya mirip.\n"
                        "ATURAN MUTLAK:\n"
                        "1. DILARANG KERAS menggunakan kata 'bermasalah', 'kritis', atau 'perlu atensi'. \n"
                        "2. Gunakan istilah objektif seperti 'toko dengan temuan', 'frekuensi temuan', atau 'analisis data'. \n"
                        "3. Jawablah menggunakan Bahasa Indonesia yang sangat rapi, analitis, sopan, dan berstandar korporat."
                    )
                    
                    # Menggunakan model mixtral-8x7b-32768 yang sangat stabil dan support token besar
                    response = client.chat.completions.create(
                        model="mixtral-8x7b-32768",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": pertanyaan}
                        ],
                        temperature=0.1
                    )
                    
                    answer = response.choices[0].message.content
                    st.write(answer)
                    
    except Exception as e:
        st.error(f"Koneksi AI mengalami kendala teknis: {e}")
else:
    st.warning("⚠️ Kunci GROQ_API_KEY belum dikonfigurasi di menu Settings > Secrets Streamlit.")

st.markdown("</div>", unsafe_allow_html=True)
