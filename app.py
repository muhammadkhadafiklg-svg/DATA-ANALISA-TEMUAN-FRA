import streamlit as st
import pandas as pd
import plotly.express as px

# 1. KONFIGURASI HALAMAN (Harus paling atas)
st.set_page_config(page_title="Dashboard Analisa Visit", page_icon="🚀", layout="wide")

# CSS Tambahan untuk mempercantik KPI
st.markdown('''
    <style>
    .kpi-card { background-color: #ffffff; padding: 20px; border-radius: 15px; border-left: 5px solid #4318FF; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .kpi-card-2 { border-left-color: #FF9800; }
    .kpi-title { font-size: 14px; color: #a3aed1; font-weight: bold; margin-bottom: 5px; }
    .kpi-value { font-size: 32px; font-weight: bold; color: #1b2559; }
    </style>
''', unsafe_allow_html=True)

st.markdown("<h2 style='color:#111c44; font-weight:bold;'>🚀 Dashboard Analisa Visit</h2>", unsafe_allow_html=True)

# 2. KONEKSI KE GOOGLE SHEETS (Link Export CSV)
# ID Sheet Anda yang kita gunakan sebelumnya
SHEET_ID = "1RfrC_LUAZbKrGEN15KPkBXhUz8ei2jyqGdUaKPS4WMY"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=300) # Data disimpan sementara (cache) selama 5 menit agar web super cepat
def load_data():
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    df.fillna('', inplace=True)
    return df

try:
    df_mentah = load_data()
except Exception as e:
    st.error("Gagal membaca data dari Google Sheets. Pastikan akses link sheet sudah 'Anyone with the link'.")
    st.stop()

# 3. ALGORITMA KATEGORI PINTAR
def deteksi_kategori(teks):
    teks = str(teks).upper().strip()
    if any(x in teks for x in ["TIDAK ADA", "-", "0", "–", "NIHIL"]) or teks == "":
        return None
    if "STB" in teks: return "ISU STB (SETORAN)"
    if any(x in teks for x in ["BRANKAS", "PASS"]): return "AKSES/PASSWORD BRANKAS"
    if any(x in teks for x in ["NOTA", "BON"]): return "ADMINISTRASI NOTA/BON"
    if any(x in teks for x in ["SELISIH", "MINUS", "PLUS", "PC", "RP"]): return "SELISIH UANG / PC"
    if any(x in teks for x in ["KASBON", "KB"]): return "KASBON MENGGANTUNG"
    if any(x in teks for x in ["DBS", "PETTY CASH"]): return "PENGELUARAN DBS/PETTY CASH"
    if any(x in teks for x in ["MOP", "EDC"]): return "MESIN EDC / MOP"
    return "TEMUAN OPERASIONAL LAINNYA"

# 4. PENGOLAHAN DATA
if not df_mentah.empty:
    df_mentah['TANGGAL VISIT'] = df_mentah['TANGGAL VISIT'].astype(str)
    
    # Ambil Bulan dan Tahun
    df_mentah['Bulan'] = df_mentah['TANGGAL VISIT'].apply(lambda x: x.split(' ')[1] if len(x.split(' ')) >= 3 else 'Unknown')
    df_mentah['Tahun'] = df_mentah['TANGGAL VISIT'].apply(lambda x: x.split(' ')[2] if len(x.split(' ')) >= 3 else 'Unknown')
    
    df_mentah['Kategori Temuan'] = df_mentah['Temuan Visit'].apply(deteksi_kategori)
    df_mentah['Temuan Visit'] = df_mentah['Temuan Visit'].str.upper()

    # 5. AREA FILTER (KONTROL)
    st.markdown("---")
    col_f1, col_f2 = st.columns(2)
    
    urutan_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    bulan_tersedia = [b for b in urutan_bulan if b in df_mentah['Bulan'].unique()]
    tahun_tersedia = sorted(df_mentah[df_mentah['Tahun'] != 'Unknown']['Tahun'].unique(), reverse=True)
    
    with col_f1:
        pilih_bulan = st.selectbox("Pilih Bulan:", ["Semua"] + bulan_tersedia)
    with col_f2:
        pilih_tahun = st.selectbox("Pilih Tahun:", ["Semua"] + tahun_tersedia)

    # TERAPKAN FILTER KE DATA
    df_filter = df_mentah.copy()
    if pilih_bulan != "Semua":
        df_filter = df_filter[df_filter['Bulan'] == pilih_bulan]
    if pilih_tahun != "Semua":
        df_filter = df_filter[df_filter['Tahun'] == pilih_tahun]

    total_visit = len(df_filter)
    df_temuan = df_filter[df_filter['Kategori Temuan'].notnull()]
    total_temuan = len(df_temuan)

    # 6. TAMPILAN KPI BOX
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">TOTAL TOKO DIKUNJUNGI</div><div class="kpi-value">{total_visit}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card kpi-card-2"><div class="kpi-title">TOTAL TEMUAN PERIODE INI</div><div class="kpi-value">{total_temuan}</div></div>', unsafe_allow_html=True)
    
    st.write("") 

    # 7. GRAFIK DAN TABEL DETAIL
    if total_temuan > 0:
        st.subheader("📊 Persentase Top 5 Temuan Operasional")
        
        # Hitung Top 5
        top5_counts = df_temuan['Kategori Temuan'].value_counts().head(5)
        df_top5 = pd.DataFrame({
            'Kategori': top5_counts.index,
            'Jumlah': top5_counts.values,
            'Persentase': (top5_counts.values / total_temuan * 100).round(1)
        })
        
        df_top5 = df_top5.sort_values('Persentase', ascending=True)

        # Gambar Grafik
        fig = px.bar(
            df_top5, x='Persentase', y='Kategori', orientation='h', text='Persentase', color='Kategori',
            color_discrete_sequence=['#4318FF', '#39B8FF', '#FF9800', '#FF2D55', '#34C759'][::-1]
        )
        fig.update_traces(texttemplate='%{text}%', textposition='outside', showlegend=False)
        fig.update_layout(
            xaxis_title="", yaxis_title="", plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridcolor='#e9edf7', range=[0, df_top5['Persentase'].max() * 1.2]),
            margin=dict(l=0, r=0, t=10, b=0), font=dict(family="Arial", size=14, color="#1b2559"), height=350
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Detail Temuan (Maks. 5 Contoh per Kategori)")
        kategori_terbanyak = df_top5.sort_values('Jumlah', ascending=False)['Kategori'].tolist()
        
        # Looping Tabel per Kategori
        for kat in kategori_terbanyak:
            count_kat = top5_counts[kat]
            st.markdown(f"<div style='background-color: #f4f7fe; padding: 10px; border-left: 4px solid #4318FF; font-weight: bold; color: #1b2559; margin-top: 15px;'>{kat} &nbsp;|&nbsp; {count_kat} TEMUAN</div>", unsafe_allow_html=True)
            
            detail_kat = df_temuan[df_temuan['Kategori Temuan'] == kat].head(5)
            # Tampilkan Tabel
            st.dataframe(
                detail_kat[['TANGGAL VISIT', 'NAMA FRA', 'KODE STORE', 'NAMA STORE', 'Temuan Visit']],
                hide_index=True, use_container_width=True
            )
    else:
        st.info("Tidak ada data temuan pada filter yang dipilih.")
