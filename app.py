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
# 2. PENGAMBILAN DATA (KEMBALI KE CARA KE-2 YANG AMAN)
# ==========================================
SHEET_ID = "1RfrC_LUAZbKrGEN15KPkBXhUz8ei2jyqGdUaKPS4WMY"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(url)
    
    # Python otomatis mengekstrak BU dari gabungan kode (Kolom ke-4 / Index 3)
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

list_bu = sorted([b for b in df_mentah['BISNIS UNIT'].dropna().unique() if b and b != 'BU LAINNYA' and b != 'NONE'])
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
    st.success("🎉 Luar biasa! Tidak ada data temuan pada Bisnis Unit / Filter yang Anda pilih. Operasional berjalan bersih.")
    st.stop()

# ==========================================
# 6. TAB NAVIGASI ANALISA
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Eksekutif", "🎯 Analisa Mendalam (BU, Area & Toko)", "💡 Kesimpulan & Action Plan"])

# ------------------------------------------
# TAB 1: RINGKASAN EKSEKUTIF
# ------------------------------------------
with tab1:
    col_chart1, col_chart2 = st.columns([6, 4])
    
    with col_chart1:
        st.markdown("#### Distribusi Kategori Temuan Utama")
        top_kategori = df_temuan['Kategori Temuan'].value_counts().reset_index()
        top_kategori.columns = ['Kategori', 'Jumlah']
        top_kategori['Persentase'] = (top_kategori['Jumlah'] / total_temuan * 100).round(1)
        
        top_kategori['Label Teks'] = top_kategori['Jumlah'].astype(str) + " kasus (" + top_kategori['Persentase'].astype(str) + "%)"
        top_kategori = top_kategori.sort_values('Jumlah', ascending=True)
        
        fig_bar = px.bar(
            top_kategori, 
            x='Persentase', 
            y='Kategori', 
            orientation='h',
            text='Label Teks',
            color_discrete_sequence=['#2563eb']
        )
        
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=True, gridcolor='#f1f5f9', range=[0, top_kategori['Persentase'].max() * 1.3]), margin=dict(l=0, r=0, t=10, b=0), height=380)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        st.markdown("#### Proporsi Kunjungan Bersih vs Bermasalah")
        kunjungan_bersih = total_visit - total_temuan if (total_visit - total_temuan) > 0 else 0
        fig_donut = px.pie(names=['Kunjungan Bersih', 'Ada Temuan'], values=[kunjungan_bersih, total_temuan], hole=0.6, color_discrete_sequence=['#10B981', '#E11D48'])
        fig_donut.update_traces(textinfo='percent', textfont_size=14, hoverinfo='label+value')
        fig_donut.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=380, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))
        st.plotly_chart(fig_donut, use_container_width=True)

# ------------------------------------------
# TAB 2: ANALISA MENDALAM (BU, FRA, TOKO)
# ------------------------------------------
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
        
        st.dataframe(
            store_counts,
            column_config={
                "BISNIS UNIT": st.column_config.TextColumn("BU", width="small"),
                "KODE STORE": st.column_config.TextColumn("Kode", width="small"),
                "NAMA STORE": st.column_config.TextColumn("Nama Toko", width="medium"),
                "Jumlah Temuan": st.column_config.ProgressColumn("Frekuensi", format="%f", min_value=0, max_value=int(store_counts['Jumlah Temuan'].max()))
            },
            hide_index=True, use_container_width=True
        )

# ------------------------------------------
# TAB 3: KESIMPULAN & ACTION PLAN (AI BASE)
# ------------------------------------------
with tab3:
    st.markdown("#### 💡 Intelijen Bisnis: Insight & Rekomendasi Tindakan")
    
    top_masalah = top_kategori.iloc[-1]['Kategori']
    persen_masalah = top_kategori.iloc[-1]['Persentase']
    top_fra = fra_counts.iloc[0]['Nama FRA'] if not fra_counts.empty else "Tidak diketahui"
    top_bu = bu_counts.iloc[0]['Bisnis Unit'] if not bu_counts.empty else "Tidak diketahui"
    teks_fokus = f"pada Bisnis Unit **{pilih_bu}**" if pilih_bu != "Semua Bisnis Unit" else f"secara keseluruhan (didominasi oleh BU **{top_bu}**)"
    
    st.markdown(f'''
        <div class="rekomendasi-box">
            <strong style="font-size:16px;">🔍 Kesimpulan Eksekutif:</strong><br>
            Berdasarkan data {teks_fokus}, tingkat kecacatan operasional (Defect Rate) berada di angka <b>{rasio_temuan:.1f}%</b>. 
            Masalah paling dominan yang merusak kinerja saat ini adalah <b>{top_masalah}</b>, menyumbang <b>{persen_masalah}%</b> dari seluruh total temuan. 
            Secara geografis/area, FRA atas nama <b>{top_fra}</b> mencatatkan rekor kelalaian terbanyak yang memerlukan atensi pembinaan khusus.
        </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("**📝 Rekomendasi Tindakan Perbaikan (Corrective Action):**")
    
    if "SELISIH UANG" in top_masalah:
        st.warning("1. **Sidak Cash Opname:** Lakukan perhitungan fisik uang dadakan (cash opname) mingguan pada shift kasir.\n2. **Training SOP Serah Terima:** Wajibkan kasir melakukan check-balance setiap pergantian shift dan disetujui oleh Kepala Toko.\n3. **Cek Sistem CCTV:** Pastikan CCTV menyorot jelas ke arah laci kasir di toko-toko kritis.")
    elif "STB" in top_masalah:
        st.info("1. **Disiplin Setoran:** Buat SLA ketat bahwa Setoran Tunai Bank (STB) harus dilakukan h+1, dilarang menunda.\n2. **Verifikasi Bukti:** Area Manager (FRA) harus memvalidasi foto resi bank harian via grup WhatsApp operasional.\n3. **Sanksi Keterlambatan:** Terapkan surat teguran bagi Kepala Toko yang menahan setoran.")
    elif "BRANKAS" in top_masalah:
        st.error("1. **Reset Password Berkala:** Wajibkan penggantian PIN brankas setiap kali ada mutasi/resign karyawan pemegang kunci.\n2. **Pembatasan Akses:** Kunci brankas fisik hanya boleh dipegang oleh Kepala Toko / PIC Shift yang bertugas.\n3. **Audit Kepatuhan:** Berikan penalti berat jika ditemukan kombinasi brankas dalam keadaan 'pass/nyangkut' atau sengaja terbuka.")
    elif "NOTA" in top_masalah:
        st.info("1. **Filing System:** Wajibkan setiap toko memiliki bantex/map khusus berdasarkan tanggal untuk nota & bon.\n2. **Digitalisasi:** Jika memungkinkan, biasakan foto nota menggunakan HP kantor dan upload ke sistem sebelum nota fisik hilang.\n3. **Audit Berkas:** FRA harus mengecek kelengkapan bon setiap kunjungan rutin.")
    elif "KASBON" in top_masalah:
        st.error("1. **Stop Kasbon:** Tegaskan kembali aturan perusahaan bahwa uang toko TIDAK BOLEH digunakan untuk pinjaman/kasbon pribadi karyawan.\n2. **Potong Gaji:** Lakukan pemotongan gaji langsung bagi karyawan yang terbukti melakukan kasbon gantung.\n3. **Teguran FRA:** Berikan peringatan kepada FRA yang membiarkan budaya kasbon terjadi di areanya.")
    else:
        st.success("1. **Refreshment Training:** Kumpulkan Kepala Toko bermasalah via Zoom untuk evaluasi kesalahan operasional.\n2. **Checklist Kunjungan:** Update form visit FRA agar lebih fokus mengecek poin-poin krusial yang sering dilanggar.\n3. **Reward & Punishment:** Terapkan pemotongan KPI/Bonus bagi toko dengan temuan terbanyak, dan berikan reward bagi toko yang Zero Defect.")

    st.markdown("---")
    st.markdown("#### 📂 Arsip Detail Temuan (Diurutkan / Sorted by BU)")
    
    df_tampil = df_temuan[['BISNIS UNIT', 'FRA', 'KODE STORE', 'NAMA STORE', 'TANGGAL', 'DETAIL TEMUAN', 'Kategori Temuan']]
    df_tampil = df_tampil.sort_values(by=['BISNIS UNIT', 'FRA', 'KODE STORE'])
    
    st.dataframe(df_tampil, hide_index=True, use_container_width=True)
