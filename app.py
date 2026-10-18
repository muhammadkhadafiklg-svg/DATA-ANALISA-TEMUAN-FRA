import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. KONFIGURASI & TEMA DASHBOARD PREMIUM
# ==========================================
st.set_page_config(page_title="Executive Dashboard - Audit Visit", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown('''
    <style>
    /* Styling Premium Minimalis */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .kpi-container { display: flex; gap: 20px; margin-bottom: 30px; }
    .kpi-card { 
        background: #ffffff; 
        border: 1px solid #e2e8f0; 
        padding: 24px; 
        border-radius: 12px; 
        width: 100%; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02), 0 2px 4px -1px rgba(0,0,0,0.02);
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: #1E3A8A;
    }
    .kpi-card.alert::before { background: #E11D48; }
    .kpi-card.success::before { background: #10B981; }
    
    .kpi-label { font-size: 13px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
    .kpi-value { font-size: 32px; font-weight: 800; color: #0f172a; line-height: 1.2; }
    .kpi-desc { font-size: 13px; font-weight: 500; color: #94a3b8; margin-top: 6px; }
    
    .rekomendasi-box { 
        background-color: #f8fafc; 
        border: 1px solid #cbd5e1; 
        border-left: 4px solid #2563eb; 
        padding: 20px 24px; 
        border-radius: 8px; 
        margin-bottom: 25px; 
        font-size: 15px; 
        line-height: 1.7; 
        color: #334155; 
    }
    hr { border-color: #f1f5f9; margin: 2rem 0; }
    </style>
''', unsafe_allow_html=True)

# ==========================================
# 2. DATA EXTRACTION (TEPAT DI KOLOM G)
# ==========================================
SHEET_ID = "1RfrC_LUAZbKrGEN15KPkBXhUz8ei2jyqGdUaKPS4WMY"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(url)
    
    # Cleansing & Pemisahan
    raw_kode = df.iloc[:, 3].astype(str).str.upper().str.strip()
    kode_toko_bersih = raw_kode.apply(lambda x: x[:4] if len(x) >= 4 else x)
    
    # Ekstraksi MURNI sesuai indeks kolom di Google Sheet
    df_clean = pd.DataFrame({
        'TANGGAL': df.iloc[:, 0].astype(str),
        'FRA': df.iloc[:, 1].astype(str).str.upper().str.strip(),
        'KODE STORE': kode_toko_bersih,
        'NAMA STORE': df.iloc[:, 4].astype(str).str.upper().str.strip(),
        'DETAIL TEMUAN': df.iloc[:, 5].astype(str).str.upper().str.strip(),
        'BISNIS UNIT': df.iloc[:, 6].astype(str).str.upper().str.strip() # BACA KOLOM G (Index 6)
    })
    
    return df_clean.replace(['NAN', 'NAN ', ''], None)

try:
    df_mentah = load_data()
except Exception as e:
    st.error("Gagal membaca sambungan data.")
    st.stop()

# ==========================================
# 3. KATEGORISASI (ENGINE)
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
# 4. SIDEBAR - PANEL KONTROL
# ==========================================
st.sidebar.markdown("<h3 style='color:#0f172a; font-weight:700;'>🎛️ Control Panel</h3>", unsafe_allow_html=True)

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
    <div style='text-align: center; margin-top: 30px; padding: 18px; border-radius: 8px; background: linear-gradient(145deg, #f8fafc, #f1f5f9); border: 1px solid #e2e8f0;'>
        <div style='font-size: 10px; color: #64748b; font-weight:800; letter-spacing:1px; margin-bottom:5px;'>POWERED & DEVELOPED BY</div>
        <div style='font-size: 16px; color: #0f172a; font-weight: 800;'>M Khadafi Zainal</div>
        <div style='font-size: 13px; color: #2563eb; font-weight: 600; margin-top:2px;'>Finance Representative</div>
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
toko_kritis = df_temuan['NAMA STORE'].nunique()
rasio_temuan = (total_temuan / total_visit * 100) if total_visit > 0 else 0

# ==========================================
# 5. HEADER & KPI (SAAS STYLE)
# ==========================================
st.markdown("<h2 style='color:#0f172a; font-weight:800; margin-bottom:5px; letter-spacing:-0.5px;'>Executive Dashboard: Audit Operations</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#64748b; font-size:15px; margin-bottom:30px;'>Laporan ringkasan kepatuhan operasional cabang dan analisa insight strategis.</p>", unsafe_allow_html=True)

st.markdown(f'''
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">Total Visit Audit</div>
            <div class="kpi-value">{total_visit}</div>
            <div class="kpi-desc">Toko diaudit pada periode ini</div>
        </div>
        <div class="kpi-card alert">
            <div class="kpi-label">Volume Temuan</div>
            <div class="kpi-value">{total_temuan}</div>
            <div class="kpi-desc">Total pelanggaran operasional</div>
        </div>
        <div class="kpi-card alert">
            <div class="kpi-label">Toko Kritis</div>
            <div class="kpi-value">{toko_kritis}</div>
            <div class="kpi-desc">Toko unik yang memiliki isu</div>
        </div>
        <div class="kpi-card {'alert' if rasio_temuan > 30 else 'success'}">
            <div class="kpi-label">Defect Rate</div>
            <div class="kpi-value">{rasio_temuan:.1f}%</div>
            <div class="kpi-desc">Rasio kecacatan dari total visit</div>
        </div>
    </div>
''', unsafe_allow_html=True)

if total_temuan == 0:
    st.success("🎉 Luar biasa! Tidak ditemukan anomali operasional pada filter yang Anda pilih.")
    st.stop()

# ==========================================
# 6. ANALYTICS TABS (PROFESSIONAL CORPORATE BLUE)
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Executive Summary", "🏢 Area & Branch Analysis", "📋 Action Plan & Database"])

# --- TAB 1 ---
with tab1:
    col_chart1, col_chart2 = st.columns([6, 4])
    with col_chart1:
        st.markdown("<h4 style='color:#1e293b; font-weight:700;'>Distribusi Kategori Isu Utama</h4>", unsafe_allow_html=True)
        top_kategori = df_temuan['Kategori Temuan'].value_counts().reset_index()
        top_kategori.columns = ['Kategori', 'Jumlah']
        top_kategori['Persentase'] = (top_kategori['Jumlah'] / total_temuan * 100).round(1)
        top_kategori['Label'] = top_kategori['Jumlah'].astype(str) + " kasus (" + top_kategori['Persentase'].astype(str) + "%)"
        top_kategori = top_kategori.sort_values('Jumlah', ascending=True)
        
        # Grafik Biru Profesional
        fig_bar = px.bar(top_kategori, x='Persentase', y='Kategori', orientation='h', text='Label')
        fig_bar.update_traces(marker_color='#1E3A8A', textposition='outside', textfont=dict(color='#334155', size=13))
        fig_bar.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', xaxis_title="", yaxis_title="", xaxis=dict(showgrid=True, gridcolor='#f1f5f9', range=[0, top_kategori['Persentase'].max() * 1.3]), margin=dict(l=0, r=0, t=10, b=0), height=380)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        st.markdown("<h4 style='color:#1e293b; font-weight:700;'>Proporsi Kepatuhan Audit</h4>", unsafe_allow_html=True)
        kunjungan_bersih = total_visit - total_temuan if (total_visit - total_temuan) > 0 else 0
        fig_donut = px.pie(names=['Toko Bersih / Sesuai SOP', 'Terdapat Temuan'], values=[kunjungan_bersih, total_temuan], hole=0.65)
        fig_donut.update_traces(marker=dict(colors=['#10B981', '#E11D48']), textinfo='percent', textfont_size=14, hoverinfo='label+value')
        fig_donut.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=380, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))
        st.plotly_chart(fig_donut, use_container_width=True)

# --- TAB 2 ---
with tab2:
    st.markdown("<h4 style='color:#1e293b; font-weight:700;'>Rapor Volume Temuan per Bisnis Unit</h4>", unsafe_allow_html=True)
    bu_counts = df_temuan['BISNIS UNIT'].value_counts().reset_index()
    bu_counts.columns = ['Bisnis Unit', 'Total Temuan']
    
    # Grafik BU Biru Profesional
    fig_bu = px.bar(bu_counts, x='Bisnis Unit', y='Total Temuan', text='Total Temuan')
    fig_bu.update_traces(marker_color='#2563eb', textposition='outside', textfont=dict(size=14, color='#1e293b', weight='bold'))
    fig_bu.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', xaxis_title="", yaxis_title="", margin=dict(t=10, b=0), height=320)
    st.plotly_chart(fig_bu, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_deep1, col_deep2 = st.columns(2)
    
    with col_deep1:
        st.markdown("<h4 style='color:#1e293b; font-weight:700;'>Top 10 Area (FRA) Perlu Atensi</h4>", unsafe_allow_html=True)
        fra_counts = df_temuan['FRA'].value_counts().reset_index().head(10)
        fra_counts.columns = ['Nama FRA', 'Total Temuan']
        
        # Grafik FRA Biru Gelap
        fig_fra = px.bar(fra_counts, x='Nama FRA', y='Total Temuan', text='Total Temuan')
        fig_fra.update_traces(marker_color='#1E3A8A', textposition='outside', textfont=dict(size=13, color='#1e293b'))
        fig_fra.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', xaxis_title="", yaxis_title="", margin=dict(t=10, b=0), height=360)
        st.plotly_chart(fig_fra, use_container_width=True)

    with col_deep2:
        st.markdown("<h4 style='color:#1e293b; font-weight:700;'>Daftar Toko Kritis (Tertinggi)</h4>", unsafe_allow_html=True)
        store_counts = df_temuan.groupby(['BISNIS UNIT', 'KODE STORE', 'NAMA STORE']).size().reset_index(name='Frekuensi Isu')
        store_counts = store_counts.sort_values(['Frekuensi Isu', 'BISNIS UNIT'], ascending=[False, True]).head(10)
        
        # Tabel Cantik dengan Progress Bar
        st.dataframe(
            store_counts,
            column_config={
                "BISNIS UNIT": st.column_config.TextColumn("BU", width="small"),
                "KODE STORE": st.column_config.TextColumn("Kode", width="small"),
                "NAMA STORE": st.column_config.TextColumn("Nama Cabang", width="medium"),
                "Frekuensi Isu": st.column_config.ProgressColumn("Volume", format="%d", min_value=0, max_value=int(store_counts['Frekuensi Isu'].max()))
            },
            hide_index=True, use_container_width=True, height=360
        )

# --- TAB 3 ---
df_tampil = df_temuan[['BISNIS UNIT', 'FRA', 'KODE STORE', 'NAMA STORE', 'TANGGAL', 'DETAIL TEMUAN', 'Kategori Temuan']]
df_tampil = df_tampil.sort_values(by=['BISNIS UNIT', 'FRA', 'KODE STORE'])

with tab3:
    st.markdown("<h4 style='color:#1e293b; font-weight:700;'>Intelijen Bisnis: Insight & Rekomendasi Eksekutif</h4>", unsafe_allow_html=True)
    
    top_masalah = top_kategori.iloc[-1]['Kategori']
    persen_masalah = top_kategori.iloc[-1]['Persentase']
    top_fra = fra_counts.iloc[0]['Nama FRA'] if not fra_counts.empty else "N/A"
    top_bu = bu_counts.iloc[0]['Bisnis Unit'] if not bu_counts.empty else "N/A"
    teks_fokus = f"pada Bisnis Unit <b>{pilih_bu}</b>" if pilih_bu != "Semua Bisnis Unit" else f"secara keseluruhan (didominasi oleh BU <b>{top_bu}</b>)"
    
    st.markdown(f'''
        <div class="rekomendasi-box">
            Berdasarkan matriks data {teks_fokus}, tingkat deviasi/kecacatan operasional (Defect Rate) tercatat di angka <b>{rasio_temuan:.1f}%</b>. 
            Kendala paling dominan yang berisiko menekan efisiensi adalah isu <b>{top_masalah}</b>, menyumbang <b>{persen_masalah}%</b> dari total seluruh temuan audit lapangan.<br><br>
            Secara demografi pengelolaan, area di bawah pengawasan FRA <b>{top_fra}</b> mencatatkan rekor temuan tertinggi yang mendesak untuk dilakukan evaluasi pembinaan secara terukur.
        </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("<h5 style='color:#0f172a; margin-top:20px; font-weight:700;'>Rencana Tindakan Korektif (Corrective Action Plan):</h5>", unsafe_allow_html=True)
    
    # Menggunakan multi-line text aman (Triple quotes)
    if "SELISIH UANG" in top_masalah:
        st.warning("""1. **Instruksi Sidak Fisik (Cash Opname):** Terbitkan memo wajib penghitungan fisik laci kasir secara acak mingguan.\n2. **Kepatuhan Check-Balance:** Validasi serah terima shift kasir harus ditandatangani langsung oleh Kepala Toko.\n3. **Audit Keamanan Visual:** FRA wajib memastikan visibilitas CCTV menyorot langsung ke laci kasir di titik-titik kritis.""")
    elif "STB" in top_masalah:
        st.info("""1. **Penegakan SLA Setoran:** Wajibkan Setoran Tunai Bank (STB) diselesaikan pada H+1 pagi tanpa toleransi penundaan.\n2. **Digitalisasi Pelaporan:** Wajibkan unggah bukti resi STB via grup Telegram/WhatsApp operasional sebelum pukul 12:00 siang.\n3. **Penerapan Surat Peringatan (SP):** Eskalasi sanksi administratif bagi cabang yang sengaja menahan dana operasional.""")
    elif "BRANKAS" in top_masalah:
        st.error("""1. **Protokol Reset Keamanan:** Integrasikan SOP reset kombinasi sandi brankas setiap ada pergantian struktur karyawan toko.\n2. **Otorisasi Terbatas:** Kunci akses fisik brankas merupakan hak eksklusif yang hanya dipegang oleh Person In Charge (PIC) Shift.\n3. **Zero Tolerance Policy:** Penjatuhan sanksi berat (SP3) bila brankas ditemukan tidak terkunci atau sengaja di-bypass.""")
    elif "NOTA" in top_masalah:
        st.info("""1. **Standardisasi Pengarsipan:** Alokasikan map akordion khusus berindeks tanggal di setiap cabang untuk sentralisasi arsip bon.\n2. **Backup Digital:** Implementasi budaya foto bukti transaksi langsung menggunakan perangkat operasional toko.\n3. **Compliance Check FRA:** FRA wajib menjadikan verifikasi fisik nota pengeluaran sebagai poin pertama checklist visit.""")
    elif "KASBON" in top_masalah:
        st.error("""1. **Deklarasi Larangan Kasbon:** Sosialisasikan ulang kebijakan perusahaan terkait pelarangan mutlak penggunaan dana toko untuk pribadi.\n2. **Pemotongan Payroll Instan:** Koordinasi dengan tim HRD untuk deduksi gaji langsung bagi oknum yang terbukti menggantung kasbon.\n3. **Teguran Supervisor:** Penurunan KPI Area Manager/FRA yang terbukti membiarkan praktik kasbon di wilayahnya.""")
    else:
        st.success("""1. **Pelatihan Ulang (Refreshment Program):** Agendakan sesi kalibrasi operasional virtual untuk jajaran Kepala Toko terkait kelalaian SOP.\n2. **Penajaman Parameter Visit:** Perbarui form audit lapangan FRA untuk lebih agresif membidik celah operasional berulang.\n3. **Skema Reward & Consequence:** Korelasi langsung antara persentase Zero Defect toko dengan pencairan insentif/bonus akhir bulan.""")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#1e293b; font-weight:700;'>Database Log Temuan (Korporat)</h4>", unsafe_allow_html=True)
    
    st.dataframe(
        df_tampil,
        column_config={
            "BISNIS UNIT": st.column_config.TextColumn("BU", width="small"),
            "FRA": st.column_config.TextColumn("Nama FRA", width="small"),
            "KODE STORE": st.column_config.TextColumn("Kode", width="small"),
            "NAMA STORE": st.column_config.TextColumn("Nama Cabang", width="medium"),
            "TANGGAL": st.column_config.TextColumn("Tanggal Audit"),
            "DETAIL TEMUAN": st.column_config.TextColumn("Deskripsi Spesifik Temuan", width="large"),
            "Kategori Temuan": st.column_config.TextColumn("Klasifikasi Sistem")
        },
        hide_index=True, use_container_width=True
    )

# ==========================================
# 7. AI EXECUTIVE ASSISTANT (CHAT)
# ==========================================
st.markdown("<hr style='margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<h3 style='color:#0f172a; font-weight:800;'>🤖 AI Executive Assistant</h3>", unsafe_allow_html=True)
st.caption("Berikan instruksi atau pertanyaan kepada AI untuk menganalisa data laporan di atas secara otomatis.")

if "GROQ_API_KEY" in st.secrets:
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # AI Engine (Llama3 8B)
        llm = ChatGroq(
            groq_api_key=st.secrets["GROQ_API_KEY"], 
            model_name="llama3-8b-8192", 
            temperature=0.1
        )
        
        # Batasan data untuk mempercepat respons AI
        data_ringkas = df_tampil.head(30).to_markdown(index=False)
        
        pertanyaan = st.chat_input("Ketik di sini (Contoh: Area mana yang perlu pembinaan mendesak dan alasannya?)")
        
        if pertanyaan:
            with st.chat_message("user"):
                st.write(pertanyaan)
            
            with st.chat_message("assistant"):
                with st.spinner('Memproses data analitik...'):
                    
                    system_prompt = (
                        "Anda adalah Asisten AI Eksekutif korporat tingkat tinggi. "
                        "Berikut adalah cuplikan data laporan audit operasional toko:\n\n"
                        f"{data_ringkas}\n\n"
                        "Tugas Anda: Jawab pertanyaan manajemen secara akurat berdasarkan data tabel tersebut. "
                        "ATURAN MUTLAK: \n"
                        "1. DILARANG KERAS menggunakan kata 'bermasalah' atau bahasa santai. Gunakan istilah 'toko kritis', 'anomali', atau 'temuan operasional'. \n"
                        "2. Jawablah menggunakan gaya bahasa konsultan bisnis yang sangat rapi, analitis, dan profesional."
                    )
                    
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=pertanyaan)
                    ]
                    
                    response = llm.invoke(messages)
                    st.write(response.content)
                    
    except Exception as e:
        st.error(f"Sistem AI terkendala: {e}")
else:
    st.warning("⚠️ Kunci GROQ_API_KEY belum dikonfigurasi di menu Settings > Secrets.")
