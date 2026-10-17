import html
import re
from urllib.parse import quote

import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================
# 1. KONFIGURASI & TEMA
# ==========================================
st.set_page_config(
    page_title="Executive Dashboard - Temuan Visit FRA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

SHEET_ID = "1RfrC_LUAZbKrGEN15KPkBXhUz8ei2jyqGdUaKPS4WMY"
SHEET_NAME = "Sheet1"  # nama tab di Google Sheet
BATAS_ALERT = 50  # defect rate (%) di atas ini ditandai merah

st.markdown(
    """
    <style>
    .metric-container { display:flex; flex-wrap:wrap; gap:15px; margin-bottom:20px; }
    .metric-box { flex:1 1 170px; background:#ffffff; border:1px solid #e2e8f0; padding:18px;
                  border-radius:10px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);
                  border-top:4px solid #1E3A8A; }
    .metric-box.alert { border-top-color:#E11D48; }
    .metric-box.success { border-top-color:#10B981; }
    .metric-title { font-size:12px; font-weight:600; color:#64748b; text-transform:uppercase;
                    letter-spacing:0.5px; margin-bottom:8px; }
    .metric-value { font-size:28px; font-weight:800; color:#0f172a; }
    .metric-sub { font-size:12px; font-weight:500; color:#94a3b8; margin-top:5px; }
    .rekomendasi-box { background:#f8fafc; color:#0f172a; border-left:4px solid #3b82f6;
                       padding:15px 20px; border-radius:5px; margin-bottom:15px; }
    .item { background:#f8fafc; color:#0f172a; border-left:4px solid #3b82f6;
            padding:10px 14px; border-radius:6px; margin-bottom:8px; font-size:14px; }
    .badge { background:#1E3A8A; color:#ffffff; font-size:11px; padding:2px 9px;
             border-radius:10px; margin-right:6px; white-space:nowrap; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 2. MESIN PENGOLAH DATA
# ==========================================
# --- HELPER START ---
BULAN = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10,
    "november": 11, "desember": 12,
}
NAMA_BULAN = {v: k.capitalize() for k, v in BULAN.items()}

NO_FINDING = (
    "tidak ada temuan", "tidak ada", "tdk ada", "nihil",
    "tidak ditemukan temuan", "secara keseluruhan semua sudah sesuai",
)

# Urutan = prioritas. Satu butir temuan masuk ke SATU jenis (yang pertama cocok).
# Format: nama jenis: (pola kata kunci, arti singkat)
KATEGORI = {
    "Nota manual": (
        r"nota manual|kwitansi manual",
        "Nota manual tidak diinput, tidak lengkap, hilang, atau tidak ada lembar aslinya.",
    ),
    "Password & BA brankas": (
        r"brankas|pa?s{1,2}word",
        "Password brankas belum diganti, BA belum diperbarui atau belum lengkap tanda tangan.",
    ),
    "Kasbon / bon sementara": (
        r"kasbon|bon sementara|\bkb\b|cashbon",
        "Kasbon menggantung, belum settlement/realisasi, atau pencatatan bon tidak konsisten.",
    ),
    "STB (received / posted)": (
        r"\bstb\b",
        "STB terlambat di-received/posted, tidak sesuai standar, atau salah input.",
    ),
    "DBS / outing / kegiatan": (
        r"\bdbs\b|outing|kopkari|reward",
        "Pengeluaran DBS dan kegiatan: bukti, approval, atau rekap tidak lengkap/tidak sesuai.",
    ),
    "Tagihan & invoice": (
        r"catering|invoice|\binv\b|tagihan",
        "Tagihan catering atau invoice belum diupload, di-reject, perlu revisi, atau pemakaiannya tidak sesuai.",
    ),
    "SR / DP / fulfillment": (
        r"\bsr\b|\bdp\b|ful+fil+ment|ful+fill|\bttu\b|cust deposit|customer deposit",
        "SR, DP, atau deposit customer menggantung dan belum di-fulfill/diselesaikan.",
    ),
    "Omset / MOP / laporan harian": (
        r"om[sz]et|penjualan|\bbsc\b|\bmop\b|daily report|sumcard|summary card|ojol",
        "Omset tidak tercatat, salah MOP, atau laporan harian tidak sesuai.",
    ),
    "Selisih kas & balance": (
        r"selisih|minus|\bplus\b|uang pc|kembalian|modal|balance|remark|remak|confirmed|final",
        "Selisih uang PC/modal/kas, atau balance final tidak diberi remark.",
    ),
    "Kelengkapan dokumen & TTD": (
        r"\bttd\b|tanda tangan|lampiran|\bba\b|berita acara|upload|belum diinput|belum input|nota",
        "Dokumen, lampiran, atau tanda tangan belum lengkap.",
    ),
    "Kebersihan & kerapian": (
        r"debu|kotor|tidak rapi|berdebu|rapi",
        "Area kasir/komputer kotor, berdebu, atau tidak rapi.",
    ),
}
LAINNYA = "Temuan operasional lainnya"
DESKRIPSI = {k: v[1] for k, v in KATEGORI.items()}
DESKRIPSI[LAINNYA] = "Temuan yang tidak masuk jenis lain; periksa isinya satu per satu."

REKOMENDASI = {
    "Nota manual": [
        "Cocokkan nomor nota manual yang terpakai dengan input di sistem setiap kunjungan.",
        "Upload foto nota (termasuk yang cancel) ke sistem nota manual di hari yang sama.",
        "Buat BA bila nota tidak ditemukan atau hilang.",
    ],
    "Password & BA brankas": [
        "Perbarui BA password brankas setiap ada mutasi PIC/SM/DSM dan pada periode berkala.",
        "Pastikan BA lengkap dengan tanda tangan PIC terkait.",
        "Sesuaikan pemegang akses brankas besar dan kecil dengan kebijakan pengelolaan brankas.",
    ],
    "Kasbon / bon sementara": [
        "Selesaikan realisasi dan settlement kasbon di K2 tepat waktu.",
        "Lengkapi pencatatan Gsheet bon sementara sampai realisasi cashier.",
        "Follow up approver bila terjadi pergantian AM agar proses tidak tertahan.",
    ],
    "STB (received / posted)": [
        "Lakukan received STB sebelum store opening dan posting STB malam di hari yang sama.",
        "Beri remark dan buat BA bila terpaksa terlambat (misalnya gangguan internet).",
        "Pastikan nominal STB yang diinput sesuai fisik.",
    ],
    "DBS / outing / kegiatan": [
        "Lengkapi approval AM/SM serta nama PT dan stempel vendor pada nota.",
        "Cocokkan rekap DBS dengan pengeluaran dan bukti serah terima uang.",
        "Lengkapi tanda tangan, absensi, dan lampiran kegiatan.",
    ],
    "Tagihan & invoice": [
        "Upload ulang tagihan yang di-reject dengan revisi nomor invoice.",
        "Upload tagihan catering yang sudah diterima tepat waktu.",
    ],
    "SR / DP / fulfillment": [
        "Selesaikan SR/DP yang menggantung dan lakukan fulfillment tepat waktu.",
        "Follow up customer deposit yang sudah lama tidak bergerak.",
        "Pantau status received yang belum di-fulfill.",
    ],
    "Omset / MOP / laporan harian": [
        "Cocokkan Daily Report dengan SBD agar salah MOP atau salah nominal cepat terdeteksi.",
        "Beri remark pada selisih akibat salah MOP.",
        "Catat omset tunai di BSC book/logbook setiap hari.",
    ],
    "Selisih kas & balance": [
        "Hitung fisik uang PC dan modal pada setiap pergantian shift.",
        "Beri remark yang jelas pada setiap selisih balance.",
        "Buat BA untuk selisih yang belum terselesaikan.",
    ],
    "Kelengkapan dokumen & TTD": [
        "Lengkapi tanda tangan dan lampiran sebelum dokumen dikirim.",
        "Cek kelengkapan berkas pada setiap kunjungan rutin.",
    ],
    "Kebersihan & kerapian": [
        "Buat jadwal kebersihan rutin untuk area kasir dan komputer.",
        "Sertakan pengecekan kerapian area pada checklist visit.",
    ],
    LAINNYA: [
        "Tinjau isian temuan secara manual, lalu tambahkan kata kunci baru bila polanya berulang.",
    ],
}

PAT_A = re.compile(r"(?:^|\s)(\d{1,2})\s?[.)]\s?(?=[A-Za-z(])")  # 1. xxx / 1.xxx / 1) xxx
PAT_B = re.compile(r"(?:^|\s)(\d{1,2})\s+(?=[A-Z])")  # 1 XXX 2 XXX
PAT_C = re.compile(r"(?:^|\s)[-\u2013\u2022]\s+(?=[A-Za-z])")  # - xxx


def parse_tanggal(v):
    """Ubah '4 September 2026' (bahasa Indonesia) menjadi tanggal."""
    if v is None or str(v).strip() == "":
        return pd.NaT
    s = str(v).strip().lower()
    m = re.match(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", s)
    if m and m.group(2) in BULAN:
        try:
            return pd.Timestamp(int(m.group(3)), BULAN[m.group(2)], int(m.group(1)))
        except ValueError:
            return pd.NaT
    return pd.to_datetime(s, errors="coerce", dayfirst=True)


def is_clean(teks: str) -> bool:
    """True bila isian menyatakan tidak ada temuan (termasuk '-', '0', 'nihil')."""
    s = re.sub(r"[^a-z0-9 ]", " ", teks.lower())
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= 3:
        return True
    return s.startswith(NO_FINDING)


def _rantai(pola, teks):
    """Ambil penanda bernomor yang berurutan 1, 2, 3, ... saja."""
    tanda, harap = [], 1
    for m in pola.finditer(teks):
        if int(m.group(1)) == harap:
            tanda.append(m)
            harap += 1
    return tanda


def split_items(teks: str) -> list:
    """Pecah satu isian temuan menjadi butir-butir temuan."""
    teks = teks.strip()
    if not teks:
        return []

    tanda = _rantai(PAT_A, teks)
    if len(tanda) < 1:
        tanda = _rantai(PAT_B, teks)
        if len(tanda) < 2:
            tanda = []
    if tanda:
        butir = []
        awal = teks[: tanda[0].start()].strip()
        # buang kalimat pembuka seperti "Ada 3 temuan" / "Secara keseluruhan sudah ok"
        if awal and not (len(awal) < 60 and re.search(r"temuan|keseluruhan", awal.lower())):
            butir.append(awal)
        for i, m in enumerate(tanda):
            akhir = tanda[i + 1].start() if i + 1 < len(tanda) else len(teks)
            bagian = teks[m.end():akhir].strip()
            if bagian:
                butir.append(bagian)
        return butir or [teks]

    # tanpa nomor: coba pecah berdasarkan tanda "-"
    garis = list(PAT_C.finditer(teks))
    if len(garis) >= 2:
        butir = []
        awal = teks[: garis[0].start()].strip()
        if awal:
            butir.append(awal)
        for i, m in enumerate(garis):
            akhir = garis[i + 1].start() if i + 1 < len(garis) else len(teks)
            bagian = teks[m.end():akhir].strip()
            if bagian:
                butir.append(bagian)
        return butir or [teks]
    return [teks]


def kategori_utama(teks: str) -> str:
    s = teks.lower()
    for nama, (pola, _) in KATEGORI.items():
        if re.search(pola, s):
            return nama
    return LAINNYA


def olah_data(raw: pd.DataFrame):
    raw = raw.iloc[:, :6].copy()
    raw.columns = ["TANGGAL", "NAMA_FRA", "NIP", "KODE_STORE", "NAMA_STORE", "TEMUAN"]
    for c in raw.columns:
        raw[c] = raw[c].fillna("").astype(str).str.strip()
    raw = raw[(raw["NAMA_FRA"] != "") | (raw["NAMA_STORE"] != "")].copy()
    raw["NAMA_FRA"] = raw["NAMA_FRA"].str.upper()
    raw["NAMA_STORE"] = raw["NAMA_STORE"].str.upper()
    raw["KODE_STORE"] = raw["KODE_STORE"].str.upper()
    raw["TEMUAN"] = raw["TEMUAN"].str.replace(r"\s+", " ", regex=True)
    raw["TGL"] = raw["TANGGAL"].apply(parse_tanggal)
    raw["TAHUN"] = raw["TGL"].dt.year.astype("Int64").astype(str).replace("<NA>", "Tidak diketahui")
    raw["BULAN"] = raw["TGL"].dt.month.map(NAMA_BULAN).fillna("Tidak diketahui")
    raw = raw.reset_index(drop=True)
    raw["VID"] = raw.index

    def status(t):
        if t == "":
            return "Belum diisi"
        return "Tidak ada temuan" if is_clean(t) else "Ada temuan"

    raw["STATUS"] = raw["TEMUAN"].apply(status)

    baris = []
    for _, r in raw[raw["STATUS"] == "Ada temuan"].iterrows():
        for no, teks in enumerate(split_items(r["TEMUAN"]), 1):
            baris.append(
                {
                    "VID": r["VID"], "TANGGAL": r["TANGGAL"], "TGL": r["TGL"],
                    "TAHUN": r["TAHUN"], "BULAN": r["BULAN"],
                    "NAMA_FRA": r["NAMA_FRA"], "KODE_STORE": r["KODE_STORE"],
                    "NAMA_STORE": r["NAMA_STORE"], "NO": no,
                    "TEMUAN": teks, "KATEGORI": kategori_utama(teks),
                }
            )
    kolom = ["VID", "TANGGAL", "TGL", "TAHUN", "BULAN", "NAMA_FRA", "KODE_STORE",
             "NAMA_STORE", "NO", "TEMUAN", "KATEGORI"]
    items = pd.DataFrame(baris, columns=kolom)
    jumlah = items.groupby("VID").size()
    raw["JUMLAH_TEMUAN"] = raw["VID"].map(jumlah).fillna(0).astype(int)
    return raw, items
# --- HELPER END ---


@st.cache_data(ttl=300, show_spinner="Mengambil data dari Google Sheet...")
def load_data(sheet_id: str, sheet_name: str):
    url = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
        f"?tqx=out:csv&sheet={quote(sheet_name)}"
    )
    raw = pd.read_csv(url, dtype=str, keep_default_na=False)
    if raw.shape[1] < 6:
        raise ValueError("Sheet harus punya minimal 6 kolom (A sampai F).")
    return olah_data(raw)


try:
    visits, items = load_data(SHEET_ID, SHEET_NAME)
except Exception as e:
    st.error(f"Gagal membaca data dari Google Sheets: {e}")
    st.info(
        "Pastikan Sheet dibagikan dengan akses 'Anyone with the link' (Viewer) "
        "dan nama tab pada SHEET_NAME sudah benar."
    )
    st.stop()

if visits.empty:
    st.warning("Data kosong.")
    st.stop()

# ==========================================
# 3. SIDEBAR - FILTER
# ==========================================
st.sidebar.markdown("### 🎛️ Panel Filter Data")
if st.sidebar.button("🔄 Refresh data"):
    st.cache_data.clear()
    st.rerun()

tahun_list = sorted([t for t in visits["TAHUN"].unique() if t != "Tidak diketahui"], reverse=True)
pilih_tahun = st.sidebar.selectbox("📅 Tahun", ["Semua Tahun"] + tahun_list)
urut = list(NAMA_BULAN.values())
bulan_list = [b for b in urut if b in visits["BULAN"].unique()]
pilih_bulan = st.sidebar.selectbox("🗓️ Bulan", ["Semua Bulan"] + bulan_list)
fra_list = sorted(visits["NAMA_FRA"].unique())
pilih_fra = st.sidebar.selectbox("🧑‍💼 FRA", ["Semua FRA"] + fra_list)
kata = st.sidebar.text_input("🔎 Cari kata (toko / isi temuan)")

df = visits.copy()
if pilih_tahun != "Semua Tahun":
    df = df[df["TAHUN"] == pilih_tahun]
if pilih_bulan != "Semua Bulan":
    df = df[df["BULAN"] == pilih_bulan]
if pilih_fra != "Semua FRA":
    df = df[df["NAMA_FRA"] == pilih_fra]
if kata.strip():
    k = kata.strip().lower()
    df = df[
        df["TEMUAN"].str.lower().str.contains(k, regex=False)
        | df["NAMA_STORE"].str.lower().str.contains(k, regex=False)
        | df["KODE_STORE"].str.lower().str.contains(k, regex=False)
    ]

if df.empty:
    st.warning("Tidak ada data sesuai filter.")
    st.stop()

it = items[items["VID"].isin(df["VID"])].copy()

# ==========================================
# 4. HEADER & KPI
# ==========================================
total_visit = len(df)
ada = int((df["STATUS"] == "Ada temuan").sum())
bersih = int((df["STATUS"] == "Tidak ada temuan").sum())
terisi = ada + bersih
total_butir = len(it)
toko_bermasalah = df[df["STATUS"] == "Ada temuan"]["KODE_STORE"].nunique()
defect = (ada / terisi * 100) if terisi else 0

st.markdown(
    "<h2 style='margin-bottom:0px;'>📈 Executive Dashboard: Temuan Visit FRA</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#64748b; margin-bottom:20px;'>Analisa temuan lapangan: setiap isian "
    "dipecah menjadi butir temuan dan dikelompokkan per jenis.</p>",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="metric-container">
        <div class="metric-box">
            <div class="metric-title">Total Kunjungan</div>
            <div class="metric-value">{total_visit}</div>
            <div class="metric-sub">Visit pada filter ini</div>
        </div>
        <div class="metric-box alert">
            <div class="metric-title">Visit Ada Temuan</div>
            <div class="metric-value">{ada}</div>
            <div class="metric-sub">Dari {terisi} visit yang sudah terisi</div>
        </div>
        <div class="metric-box alert">
            <div class="metric-title">Total Butir Temuan</div>
            <div class="metric-value">{total_butir}</div>
            <div class="metric-sub">Rata-rata {(total_butir / ada if ada else 0):.1f} butir per visit bermasalah</div>
        </div>
        <div class="metric-box alert">
            <div class="metric-title">Toko Bermasalah</div>
            <div class="metric-value">{toko_bermasalah}</div>
            <div class="metric-sub">Toko unik yang memiliki temuan</div>
        </div>
        <div class="metric-box {'alert' if defect > BATAS_ALERT else 'success'}">
            <div class="metric-title">Defect Rate</div>
            <div class="metric-value">{defect:.1f}%</div>
            <div class="metric-sub">Visit bermasalah dari visit terisi</div>
        </div>
        <div class="metric-box success">
            <div class="metric-title">Visit Bersih</div>
            <div class="metric-value">{bersih}</div>
            <div class="metric-sub">Tanpa temuan</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if it.empty:
    st.success("🎉 Tidak ada butir temuan pada filter yang dipilih.")
    st.stop()

# Ringkasan per jenis (dipakai beberapa tab)
jenis = (
    it.groupby("KATEGORI")
    .agg(BUTIR=("NO", "size"), TOKO=("KODE_STORE", "nunique"), FRA=("NAMA_FRA", "nunique"))
    .reset_index()
    .sort_values("BUTIR", ascending=False)
)
jenis["PERSEN"] = (jenis["BUTIR"] / total_butir * 100).round(1)
jenis["ARTI"] = jenis["KATEGORI"].map(DESKRIPSI)
warna = px.colors.qualitative.Safe
peta_warna = {k: warna[i % len(warna)] for i, k in enumerate(jenis["KATEGORI"])}

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📊 Ringkasan Eksekutif",
        "🧩 Jenis Temuan",
        "🎯 Per FRA & Toko",
        "📋 Rincian Temuan",
        "💡 Kesimpulan & Rekomendasi",
    ]
)

# ------------------------------------------
# TAB 1: RINGKASAN
# ------------------------------------------
with tab1:
    c1, c2 = st.columns([6, 4])
    with c1:
        st.markdown("#### Jenis temuan terbanyak")
        d = jenis.sort_values("BUTIR", ascending=True).copy()
        d["Label"] = d.apply(lambda r: f"{r['BUTIR']} butir ({r['PERSEN']}%)", axis=1)
        fig = px.bar(
            d, x="BUTIR", y="KATEGORI", orientation="h", text="Label",
            color="KATEGORI", color_discrete_map=peta_warna,
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis_title="", yaxis_title="", showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(range=[0, d["BUTIR"].max() * 1.35]),
            height=max(320, 40 * len(d) + 60),
        )
        st.plotly_chart(fig)
    with c2:
        st.markdown("#### Status seluruh visit")
        st_cnt = df["STATUS"].value_counts().reset_index()
        st_cnt.columns = ["Status", "Jumlah"]
        fig = px.pie(
            st_cnt, names="Status", values="Jumlah", hole=0.6,
            color="Status",
            color_discrete_map={
                "Ada temuan": "#E11D48", "Tidak ada temuan": "#10B981", "Belum diisi": "#94a3b8",
            },
        )
        fig.update_traces(textinfo="value+percent")
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=360,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig)

    st.markdown("#### Tren kunjungan per hari")
    harian = (
        df.dropna(subset=["TGL"])
        .groupby([df["TGL"].dt.date.rename("Tanggal"), "STATUS"])
        .size()
        .reset_index(name="Jumlah visit")
    )
    if not harian.empty:
        fig = px.bar(
            harian, x="Tanggal", y="Jumlah visit", color="STATUS",
            color_discrete_map={
                "Ada temuan": "#E11D48", "Tidak ada temuan": "#10B981", "Belum diisi": "#94a3b8",
            },
        )
        fig.update_layout(xaxis_title="", plot_bgcolor="rgba(0,0,0,0)", height=320,
                          margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig)

# ------------------------------------------
# TAB 2: JENIS TEMUAN
# ------------------------------------------
with tab2:
    st.markdown("#### Kamus jenis temuan")
    st.caption(
        "Setiap butir temuan masuk ke satu jenis berdasarkan kata kunci. "
        "Kolom Toko = jumlah toko berbeda yang terkena."
    )
    tabel = jenis[["KATEGORI", "ARTI", "BUTIR", "PERSEN", "TOKO", "FRA"]].rename(
        columns={"KATEGORI": "Jenis temuan", "ARTI": "Arti", "BUTIR": "Butir",
                 "PERSEN": "% dari total", "TOKO": "Toko", "FRA": "FRA"}
    )
    st.dataframe(
        tabel, hide_index=True,
        column_config={
            "Arti": st.column_config.TextColumn("Arti", width="large"),
            "% dari total": st.column_config.ProgressColumn(
                "% dari total", format="%.1f%%", min_value=0, max_value=100),
        },
    )

    st.markdown("#### Sebaran jenis temuan per FRA")
    pivot = it.pivot_table(index="NAMA_FRA", columns="KATEGORI", values="NO",
                           aggfunc="count", fill_value=0)
    pivot = pivot[[k for k in jenis["KATEGORI"] if k in pivot.columns]]
    fig = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale="Blues")
    fig.update_layout(xaxis_title="", yaxis_title="", coloraxis_showscale=False,
                      height=max(300, 34 * len(pivot) + 160), margin=dict(l=0, r=0, t=10, b=0))
    fig.update_xaxes(tickangle=-35)
    st.plotly_chart(fig)

    st.markdown("#### Lihat isi temuan per jenis")
    pilih = st.selectbox("Pilih jenis temuan", jenis["KATEGORI"].tolist())
    sub = it[it["KATEGORI"] == pilih]
    m1, m2, m3 = st.columns(3)
    m1.metric("Jumlah butir", len(sub))
    m2.metric("Toko terkena", sub["KODE_STORE"].nunique())
    m3.metric("FRA terkait", sub["NAMA_FRA"].nunique())
    st.info(DESKRIPSI[pilih])
    st.dataframe(
        sub.sort_values("TGL", ascending=False)[
            ["TANGGAL", "NAMA_FRA", "KODE_STORE", "NAMA_STORE", "TEMUAN"]
        ],
        hide_index=True,
        column_config={"TEMUAN": st.column_config.TextColumn("Temuan", width="large")},
    )

# ------------------------------------------
# TAB 3: PER FRA & TOKO
# ------------------------------------------
with tab3:
    st.markdown("#### 🧑‍💼 Temuan per FRA (dirinci per jenis)")
    st.caption("Gunakan untuk melihat FRA mana yang menemukan paling banyak butir dan jenisnya.")
    fra_jenis = it.groupby(["NAMA_FRA", "KATEGORI"]).size().reset_index(name="Butir")
    urut_fra = it.groupby("NAMA_FRA").size().sort_values(ascending=True).index.tolist()
    fig = px.bar(
        fra_jenis, x="Butir", y="NAMA_FRA", color="KATEGORI", orientation="h",
        color_discrete_map=peta_warna, category_orders={"NAMA_FRA": urut_fra},
    )
    fig.update_layout(
        xaxis_title="", yaxis_title="", legend_title="", plot_bgcolor="rgba(0,0,0,0)",
        height=max(320, 34 * len(urut_fra) + 140), margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="top", y=-0.12),
    )
    st.plotly_chart(fig)

    fra_tab = (
        df.groupby("NAMA_FRA")
        .agg(
            VISIT=("VID", "size"),
            BERMASALAH=("STATUS", lambda s: int((s == "Ada temuan").sum())),
            BERSIH=("STATUS", lambda s: int((s == "Tidak ada temuan").sum())),
            BUTIR=("JUMLAH_TEMUAN", "sum"),
        )
        .reset_index()
    )
    penyebut = fra_tab["BERMASALAH"] + fra_tab["BERSIH"]
    fra_tab["DEFECT_RATE_%"] = (fra_tab["BERMASALAH"] / penyebut.where(penyebut > 0) * 100).round(1)
    fra_tab = fra_tab.sort_values("BUTIR", ascending=False)
    st.dataframe(
        fra_tab, hide_index=True,
        column_config={
            "NAMA_FRA": "FRA", "VISIT": "Visit", "BERMASALAH": "Visit bermasalah",
            "BERSIH": "Visit bersih", "BUTIR": "Total butir",
            "DEFECT_RATE_%": st.column_config.NumberColumn("Defect rate (%)", format="%.1f"),
        },
    )

    st.markdown("#### 🏪 Toko dengan temuan terbanyak")
    st.caption("Toko-toko ini perlu perhatian atau kunjungan lanjutan.")
    toko = (
        it.groupby(["KODE_STORE", "NAMA_STORE"])
        .agg(BUTIR=("NO", "size"), JENIS=("KATEGORI", "nunique"),
             UTAMA=("KATEGORI", lambda s: s.value_counts().index[0]))
        .reset_index()
        .sort_values("BUTIR", ascending=False)
        .head(15)
    )
    st.dataframe(
        toko, hide_index=True,
        column_config={
            "KODE_STORE": "Kode", "NAMA_STORE": "Nama toko",
            "BUTIR": st.column_config.ProgressColumn(
                "Butir temuan", format="%d", min_value=0, max_value=int(toko["BUTIR"].max())),
            "JENIS": "Jumlah jenis", "UTAMA": "Jenis dominan",
        },
    )

# ------------------------------------------
# TAB 4: RINCIAN TEMUAN
# ------------------------------------------
with tab4:
    mode = st.radio("Tampilkan", ["Per toko (mudah dibaca)", "Tabel semua butir"], horizontal=True)

    if mode.startswith("Per toko"):
        ada_df = df[df["STATUS"] == "Ada temuan"].sort_values("TGL", ascending=False)
        opsi = (ada_df["KODE_STORE"] + " - " + ada_df["NAMA_STORE"] + " (" + ada_df["TANGGAL"] + ")").tolist()
        vids = ada_df["VID"].tolist()
        pilih_toko = st.selectbox("Pilih toko / tanggal visit", opsi)
        vid = vids[opsi.index(pilih_toko)]
        r = df[df["VID"] == vid].iloc[0]
        st.markdown(
            f"**{r['NAMA_STORE']}** ({r['KODE_STORE']})  \n"
            f"FRA: **{r['NAMA_FRA']}** | Tanggal visit: **{r['TANGGAL']}** | "
            f"Jumlah butir temuan: **{r['JUMLAH_TEMUAN']}**"
        )
        for _, b in it[it["VID"] == vid].sort_values("NO").iterrows():
            st.markdown(
                f"<div class='item'><span class='badge'>{html.escape(b['KATEGORI'])}</span> "
                f"<b>{b['NO']}.</b> {html.escape(b['TEMUAN'])}</div>",
                unsafe_allow_html=True,
            )
    else:
        pilih_jenis = st.multiselect(
            "Filter jenis temuan", jenis["KATEGORI"].tolist(), default=jenis["KATEGORI"].tolist()
        )
        tampil = it[it["KATEGORI"].isin(pilih_jenis)].sort_values(["TGL", "VID", "NO"], ascending=[False, True, True])
        tampil = tampil[["TANGGAL", "NAMA_FRA", "KODE_STORE", "NAMA_STORE", "NO", "KATEGORI", "TEMUAN"]]
        st.caption(f"{len(tampil)} butir temuan")
        st.dataframe(
            tampil, hide_index=True,
            column_config={
                "NO": "No", "KATEGORI": "Jenis",
                "TEMUAN": st.column_config.TextColumn("Temuan", width="large"),
            },
        )
        st.download_button(
            "⬇️ Unduh CSV", tampil.to_csv(index=False).encode("utf-8"),
            file_name="rincian_temuan.csv", mime="text/csv",
        )

# ------------------------------------------
# TAB 5: KESIMPULAN & REKOMENDASI
# ------------------------------------------
with tab5:
    st.markdown("#### 💡 Kesimpulan & Usulan Tindak Lanjut")
    top3 = jenis.head(3)
    fra_top = it["NAMA_FRA"].value_counts().head(1)
    toko_top = it.groupby("NAMA_STORE").size().sort_values(ascending=False).head(1)
    kalimat_top3 = "; ".join(
        f"<b>{r.KATEGORI}</b> ({r.BUTIR} butir, {r.PERSEN}%)" for r in top3.itertuples()
    )
    st.markdown(
        f"""
        <div class="rekomendasi-box">
            <strong style="font-size:16px;">🔍 Kesimpulan:</strong><br>
            Dari <b>{terisi}</b> visit yang terisi, <b>{ada}</b> visit ({defect:.1f}%) memiliki temuan,
            dengan total <b>{total_butir}</b> butir temuan di <b>{toko_bermasalah}</b> toko.
            Tiga jenis temuan terbanyak: {kalimat_top3}.
            FRA dengan butir temuan terbanyak adalah <b>{fra_top.index[0]}</b> ({fra_top.iloc[0]} butir),
            dan toko dengan butir terbanyak adalah <b>{toko_top.index[0]}</b> ({toko_top.iloc[0]} butir).
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**📝 Usulan tindak lanjut untuk tiga jenis teratas:**")
    st.caption(
        "Usulan ini disusun dari pola temuan yang muncul di data. "
        "Sesuaikan dengan kebijakan dan SOP perusahaan."
    )
    for r in top3.itertuples():
        with st.expander(f"{r.KATEGORI} - {r.BUTIR} butir di {r.TOKO} toko", expanded=True):
            st.write(DESKRIPSI[r.KATEGORI])
            for poin in REKOMENDASI.get(r.KATEGORI, REKOMENDASI[LAINNYA]):
                st.markdown(f"- {poin}")
