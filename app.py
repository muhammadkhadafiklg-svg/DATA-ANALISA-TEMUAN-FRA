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
    .metric-box { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 22px; border-radius: 12px; width: 100%; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border-top: 5px solid #1E3A8A; }
    .metric-box.alert { border-top-color: #E11D48; }
    .metric-box.success { border-top-color: #10B981; }
    .metric-title { font-size: 14px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
    .metric-value { font-size: 32px; font-weight: 800; color: #0f172a; }
    .metric-sub { font-size: 13px; font-weight: 600; color: #64748b; margin-top: 5px;}
    .rekomendasi-box { background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 5px solid #2563eb; padding: 20px; border-radius: 8px; margin-bottom:20px; font-size: 15px; line-height: 1.6; color: #1e293b;}
    </style>
''', unsafe_allow_html=True)

# ==========================================
# 2. PENGAMBILAN DATA (KOLOM G UNTUK BU)
# ==========================================
SHEET_ID = "1RfrC_LUAZbKrGEN15KPkBXhUz8ei2jyqGdUaKPS4WMY"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def tarik_data_korporat():
    df = pd.read_csv(url)
    
    df_clean = pd.DataFrame({
        'TANGGAL': df.iloc[:, 0].astype(str),
        'FRA': df.iloc[:, 1].astype(str).str.upper().str.strip(),
        'KODE STORE': df.iloc[:, 3].astype(str).str.upper().str.strip(),
        'NAMA STORE': df.iloc[:, 4].astype(str).str.upper().str.strip(),
        'DETAIL TEMUAN': df.iloc[:, 5].astype(str).str.upper().str.strip(),
        'BISNIS UNIT': df.iloc[:, 6].astype(str).str.upper().str.strip() # Murni baca dari Kolom G
    })
    
    df_clean = df_clean.replace(['NAN', 'NAN ', ''], None)
    return df_clean

try:
    df_mentah = tarik_data_korporat()
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
st.sidebar.markdown("**Filter Spesifik:**")
pilih_bu = st.sidebar.selectbox("🏢 Filter Bisnis Unit", ["Semua Bisnis Unit"] + list_bu)
pilih_fra = st.sidebar.selectbox("🧑‍💼 Filter Area (FRA)", ["Semua Area"] + list_fra)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style='text-align: center; margin-top: 10px; padding: 15px; border-radius: 10px; background-color: #f1f5f9; border-left: 4px solid #1E3A8A;'>
        <span style='font-size: 11px; color: #64748b; font-weight:bold; letter-spacing:0.5px;'>⚡ POWERED & DEVELOPED BY:</span><br>
        <strong style='font-size: 16px; color: #0f172a;'>M Khadafi Zainal</strong><br>
        <span style='font-size: 13px; color: #2563eb; font-weight: 600;'>Finance Representative</span>
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
# 5. HEADER & KPI METRICS
# ==========================================
st.markdown("<h2 style='color:#0f172a; font-weight:800; margin-bottom:0px;'>📈 Executive Dashboard: Visit Operations</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#64748b; font-size:16px; font-weight:500; margin-bottom:25px;'>Analisa mendalam temuan operasional lapangan untuk mendukung keputusan strategis.</p>", unsafe_allow_html=True)

st.markdown(f'''
    <div class="metric-container">
        <div class="metric-box">
            <div class="metric-title">Total Kunjungan (Visit)</div>
            <div class="metric-value">{total_visit}</div>
            <div class="metric-sub">Toko diaudit pada periode ini</div>
        </div>
        <div class="metric-box alert">
            <div class="metric-title">Kasus Temuan</div>
            <div class="metric-value">{total_temuan}</div>
            <div class="metric-sub">Total rincian isu operasional</div>
        </div>
        <div class="metric-box alert">
            <div class="metric-title">Toko Kritis</div>
            <div class="metric-value">{toko_kritis}</div>
            <div class="metric-sub">Toko unik yang memiliki temuan</div>
        </div>
        <div class="metric-box {'alert' if rasio_temuan > 30 else 'success'}">
            <div class="metric-title">Defect Rate (Rasio Isu)</div>
            <div class="metric-value">{rasio_temuan:.1f}%</div>
            <div class="metric-sub">Persentase isu dari total visit</div>
        </div>
    </div>
''', unsafe_allow_html=True)

if total_temuan == 0:
    st.success("🎉 Luar biasa! Tidak ada data temuan pada Bisnis Unit / Filter yang Anda pilih. Operasional berjalan bersih.")
    st.stop()

# ==========================================
# 6. TAB NAVIGASI ANALISA KORPORAT
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Eksekutif", "🎯 Analisa Kinerja Area & Toko", "💡 Rekomendasi & Arsip Temuan"])

with tab1:
    col_chart1, col_chart2 = st.columns([6, 4])
    
    with col_chart1:
        st.markdown("#### **Distribusi Kategori Temuan Utama**")
        top_kategori = df_temuan['Kategori Temuan'].value_counts().reset_index()
        top_kategori.columns = ['Kategori', 'Jumlah']
        top_kategori['Persentase'] = (top_kategori['Jumlah'] / total_temuan * 100).round(1)
        top_kategori['Label Teks'] = top_kategori['Jumlah'].astype(str) + " kasus (" + top_kategori['Persentase'].astype(str) + "%)"
        top_kategori = top_kategori.sort_values('Jumlah', ascending=True)
        
        fig_bar = px.bar(top_kategori, x='Persentase', y='Kategori', orientation='h', text='Label Teks')
        fig_bar.update_traces(marker_color='#2563eb', textposition='outside', textfont=dict(size=13, color='#0f172a'))
        fig_bar.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=True, gridcolor='#f1f5f9', range=[0, top_kategori['Persentase'].max() * 1.3]), margin=dict(l=0, r=0, t=10, b=0), height=380)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        st.markdown("#### **Proporsi Kunjungan Bersih vs Ada Temuan**")
        kunjungan_bersih = total_visit - total_temuan if (total_visit - total_temuan) > 0 else 0
        fig_donut = px.pie(names=['Kunjungan Bersih', 'Ada Temuan'], values=[kunjungan_bersih, total_temuan], hole=0.6, color_discrete_sequence=['#10B981', '#E11D48'])
        fig_donut.update_traces(textinfo='percent', textfont_size=15, hoverinfo='label+value')
        fig_donut.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=380, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))
        st.plotly_chart(fig_donut, use_container_width=True)

with tab2:
    st.markdown("#### 🚨 **Rapor Beban Temuan per Bisnis Unit (BU)**")
    
    bu_counts = df_temuan['BISNIS UNIT'].value_counts().reset_index()
    bu_counts.columns = ['Bisnis Unit', 'Total Temuan']
    
    # GRAFIK BU BIRU SOLID (SANGAT NYAMAN DIBACA)
    fig_bu = px.bar(bu_counts, x='Bisnis Unit', y='Total Temuan', text='Total Temuan')
    fig_bu.update_traces(marker_color='#3b82f6', textposition='outside', textfont=dict(size=14, color='#0f172a', weight='bold'))
    fig_bu.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10), height=320)
    st.plotly_chart(fig_bu, use_container_width=True)
    
    st.markdown("---")
    col_deep1, col_deep2 = st.columns(2)
    
    with col_deep1:
        st.markdown("#### 🚩 **Kinerja Area (Top FRA Kritis)**")
        fra_counts = df_temuan['FRA'].value_counts().reset_index().head(10)
        fra_counts.columns = ['Nama FRA', 'Total Temuan']
        
        # GRAFIK FRA MERAH SOLID 
        fig_fra = px.bar(fra_counts, x='Nama FRA', y='Total Temuan', text='Total Temuan')
        fig_fra.update_traces(marker_color='#ef4444', textposition='outside', textfont=dict(size=13, color='#0f172a'))
        fig_fra.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10), height=350)
        st.plotly_chart(fig_fra, use_container_width=True)

    with col_deep2:
        st.markdown("#### 🏪 **Daftar Toko Kritis (Top 10)**")
        store_counts = df_temuan.groupby(['BISNIS UNIT', 'KODE STORE', 'NAMA STORE']).size().reset_index(name='Jumlah Temuan')
        store_counts = store_counts.sort_values(['Jumlah Temuan', 'BISNIS UNIT'], ascending=[False, True]).head(10)
        
        st.dataframe(
            store_counts,
            column_config={
                "BISNIS UNIT": st.column_config.TextColumn("Bisnis Unit", width="small"),
                "KODE STORE": st.column_config.TextColumn("Kode Toko", width="small"),
                "NAMA STORE": st.column_config.TextColumn("Nama Cabang", width="medium"),
                "Jumlah Temuan": st.column_config.NumberColumn("Total Isu", format="%d")
            },
            hide_index=True, use_container_width=True
        )

# Siapkan data master yang diurutkan rapi untuk Tab 3 dan AI
df_tampil = df_temuan[['BISNIS UNIT', 'FRA', 'KODE STORE', 'NAMA STORE', 'TANGGAL', 'DETAIL TEMUAN', 'Kategori Temuan']]
df_tampil = df_tampil.sort_values(by=['BISNIS UNIT', 'FRA', 'KODE STORE'])

with tab3:
    st.markdown("#### 💡 **Intelijen Bisnis: Kesimpulan Otomatis**")
    
    top_masalah = top_kategori.iloc[-1]['Kategori']
    persen_masalah = top_kategori.iloc[-1]['Persentase']
    top_fra = fra_counts.iloc[0]['Nama FRA'] if not fra_counts.empty else "Tidak diketahui"
    top_bu = bu_counts.iloc[0]['Bisnis Unit'] if not bu_counts.empty else "Tidak diketahui"
    teks_fokus = f"pada Bisnis Unit **{pilih_bu}**" if pilih_bu != "Semua Bisnis Unit" else f"secara keseluruhan (didominasi oleh BU **{top_bu}**)"
    
    st.markdown(f'''
        <div class="rekomendasi-box">
            Berdasarkan data {teks_fokus}, tingkat isu operasional (Defect Rate) berada di angka <b>{rasio_temuan:.1f}%</b>. 
            Kendala paling dominan yang menghambat efisiensi saat ini adalah <b>{top_masalah}</b>, menyumbang <b>{persen_masalah}%</b> dari seluruh total temuan audit.<br><br>
            Secara geografis/area, FRA atas nama <b>{top_fra}</b> mencatatkan rekor kelalaian terbanyak yang sangat memerlukan atensi pembinaan atau sidak khusus.
        </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### 📂 **Arsip Laporan Lengkap (Diurutkan per Bisnis Unit)**")
    
    st.dataframe(
        df_tampil,
        column_config={
            "BISNIS UNIT": st.column_config.TextColumn("BU", width="small"),
            "FRA": st.column_config.TextColumn("Nama FRA", width="small"),
            "KODE STORE": st.column_config.TextColumn("Kode", width="small"),
            "NAMA STORE": st.column_config.TextColumn("Nama Cabang", width="medium"),
            "TANGGAL": st.column_config.TextColumn("Tanggal Audit"),
            "DETAIL TEMUAN": st.column_config.TextColumn("Deskripsi Temuan", width="large"),
            "Kategori Temuan": st.column_config.TextColumn("Klasifikasi Masalah")
        },
        hide_index=True, use_container_width=True
    )

# ==========================================
# 7. ASISTEN AI EXECUTIVE (MENU CHAT DI BAWAH)
# ==========================================
st.markdown("---")
st.markdown("### 🤖 Asisten AI Executive (Tanya Jawab Data)")
st.caption("Ketik pertanyaan Anda tentang data di atas. AI akan merangkumnya secara otomatis dan cerdas.")

if "GROQ_API_KEY" in st.secrets:
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # Model LLaMA-3 yang dijamin stabil, cepat, dan ringan
        llm = ChatGroq(
            groq_api_key=st.secrets["GROQ_API_KEY"], 
            model_name="llama3-8b-8192", 
            temperature=0.1
        )
        
        # Ambil 50 data teratas agar AI tidak overload dan menjawab secepat kilat
        data_ringkas = df_tampil.head(50).to_markdown(index=False)
        
        pertanyaan = st.chat_input("Tanyakan sesuatu (Contoh: Area FRA mana yang paling rawan pelanggaran brankas?)")
        
        if pertanyaan:
            with st.chat_message("user"):
                st.write(pertanyaan)
            
            with st.chat_message("assistant"):
                with st.spinner('AI sedang menganalisa tabel data Anda...'):
                    
                    system_prompt = (
                        "Anda adalah Asisten AI Eksekutif korporat yang cerdas. Berikut adalah data temuan operasional toko:\n\n"
                        f"{data_ringkas}\n\n"
                        "Tugas Anda menjawab pertanyaan berdasarkan data tabel tersebut. "
                        "ATURAN MUTLAK: Jangan pernah gunakan kata 'bermasalah', gunakan istilah 'toko kritis' atau 'ada temuan'. "
                        "Jawablah dengan ringkas, sopan, dan menggunakan Bahasa Indonesia yang sangat profesional."
                    )
                    
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=pertanyaan)
                    ]
                    
                    response = llm.invoke(messages)
                    st.write(response.content)
                    
    except Exception as e:
        st.error("⚠️ Sistem AI sedang offline atau mengalami kendala teknis. Pastikan internet stabil dan Groq API Key valid.")
else:
    st.warning("⚠️ Kunci GROQ_API_KEY belum dipasang di menu Settings > Secrets Streamlit Anda.")
