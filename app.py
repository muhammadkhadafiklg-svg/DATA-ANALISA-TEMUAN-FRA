import html
import re
from urllib.parse import quote

import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================
# 1. KONFIGURASI
# ==========================================
st.set_page_config(
    page_title="DASHBOARD ANALISA TEMUAN VISIT FRA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

SHEET_ID = "1RfrC_LUAZbKrGEN15KPkBXhUz8ei2jyqGdUaKPS4WMY"
SHEET_NAME = "Sheet1"  # nama tab di Google Sheet
BATAS_AMBER = 50  # persentase visit dengan temuan di atas ini ditandai kuning

TEKS = "#0F172A"           # warna teks utama (hampir hitam)
TEKS_SEKUNDER = "#1E293B"  # warna keterangan (tetap gelap dan terbaca)
NAVY = "#0B2545"
BIRU = "#1E3A8A"


def tulis(isi: str):
    """Tampilkan HTML (spasi dan baris baru dirapatkan agar tidak dianggap kode)."""
    st.markdown(re.sub(r"\s*\n\s*", " ", isi), unsafe_allow_html=True)


tulis(
    f"""
    <style>
    :root {{ color-scheme: light; }}
    .stApp, [data-testid="stAppViewContainer"] {{ background:#F4F6FA; color:{TEKS}; font-size:16px; }}
    [data-testid="stSidebar"] {{ background:#E2E8F0; }}
    [data-testid="stSidebar"] * {{ color:{TEKS}; }}
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
    [data-testid="stWidgetLabel"] p, label, [data-testid="stCaptionContainer"],
    [data-testid="stRadio"] p {{ color:{TEKS} !important; }}
    [data-testid="stWidgetLabel"] p, [data-testid="stRadio"] label p {{
        font-weight:800; text-transform:uppercase; font-size:13px; letter-spacing:0.5px; }}
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, input {{
        background:#FFFFFF !important; color:{TEKS} !important; font-weight:700; }}
    div[data-baseweb="select"] * {{ color:{TEKS} !important; }}
    [data-baseweb="popover"] ul, [data-baseweb="popover"] li {{ background:#FFFFFF !important; color:{TEKS} !important; }}
    .stButton button, .stDownloadButton button {{ background:{BIRU}; border:0; }}
    .stButton button *, .stDownloadButton button * {{ color:#FFFFFF !important; font-weight:800; letter-spacing:0.4px; }}
    #MainMenu, footer {{ visibility:hidden; }}
    .block-container {{ padding-top:1.5rem; padding-bottom:3rem; }}

    .stTabs [data-baseweb="tab-list"] {{ gap:6px; border-bottom:2px solid #94A3B8; }}
    .stTabs [data-baseweb="tab"] {{ background:#E2E8F0; border-radius:8px 8px 0 0; padding:10px 18px; }}
    .stTabs [data-baseweb="tab"] p {{ color:{TEKS} !important; font-weight:800; font-size:13px;
        letter-spacing:0.5px; text-transform:uppercase; }}
    .stTabs [aria-selected="true"] {{ background:{BIRU}; }}
    .stTabs [aria-selected="true"] p {{ color:#FFFFFF !important; }}

    .banner {{ background:linear-gradient(135deg,{NAVY} 0%,{BIRU} 100%); border-radius:14px;
        padding:26px 30px; margin-bottom:22px; box-shadow:0 8px 20px rgba(11,37,69,0.25); }}
    .b-title {{ color:#FFFFFF; font-size:28px; font-weight:800; letter-spacing:1px; }}
    .b-sub {{ color:#FFFFFF; font-size:14px; font-weight:700; letter-spacing:1.2px; margin-top:4px; }}
    .b-chip {{ display:inline-block; background:#FFFFFF; color:{NAVY};
        font-size:12px; font-weight:800; letter-spacing:0.6px; padding:6px 14px;
        border-radius:20px; margin-top:14px; margin-right:8px; }}

    .metric-container {{ display:flex; flex-wrap:wrap; gap:14px; margin-bottom:22px; }}
    .metric-box {{ flex:1 1 180px; background:#FFFFFF; border:1px solid #94A3B8; padding:18px 18px 16px;
        border-radius:12px; box-shadow:0 4px 10px rgba(15,23,42,0.08); border-top:5px solid {BIRU}; }}
    .k-amber {{ border-top-color:#D97706; }}
    .k-green {{ border-top-color:#059669; }}
    .metric-title {{ font-size:12px; font-weight:800; color:{TEKS}; letter-spacing:0.8px; margin-bottom:8px; }}
    .metric-value {{ font-size:34px; font-weight:800; color:{TEKS}; line-height:1.1; }}
    .metric-sub {{ font-size:12px; font-weight:700; color:{TEKS_SEKUNDER}; margin-top:8px; letter-spacing:0.3px; }}

    .sec {{ color:{NAVY}; font-size:18px; font-weight:800; letter-spacing:0.8px; text-transform:uppercase;
        border-left:6px solid {BIRU}; padding-left:12px; margin:28px 0 6px; }}
    .note {{ color:{TEKS_SEKUNDER}; font-size:13px; font-weight:700; letter-spacing:0.3px;
        text-transform:uppercase; margin:0 0 12px 18px; }}

    .insight {{ background:#FFFFFF; border:1px solid #94A3B8; border-left:6px solid {BIRU};
        border-radius:10px; padding:18px 22px; margin-bottom:18px; box-shadow:0 4px 10px rgba(15,23,42,0.07); }}
    .insight .i-title {{ color:{NAVY}; font-size:16px; font-weight:800; letter-spacing:0.8px; margin-bottom:10px; }}
    .insight .i-line {{ color:{TEKS}; font-size:15px; font-weight:700; line-height:1.6;
        text-transform:uppercase; margin-bottom:6px; }}

    .rec {{ background:#FFFFFF; border:1px solid #94A3B8; border-radius:10px; padding:16px 22px;
        margin-bottom:14px; box-shadow:0 4px 10px rgba(15,23,42,0.07); }}
    .rec .r-title {{ color:{NAVY}; font-size:16px; font-weight:800; letter-spacing:0.6px; }}
    .rec .r-meta {{ color:{BIRU}; font-size:13px; font-weight:800; letter-spacing:0.5px; margin:2px 0 8px; }}
    .rec .r-desc {{ color:{TEKS_SEKUNDER}; font-size:13px; font-weight:700; text-transform:uppercase; margin-bottom:8px; }}
    .rec ul {{ margin:0; padding-left:20px; }}
    .rec li {{ color:{TEKS}; font-size:14px; font-weight:700; line-height:1.7; text-transform:uppercase; }}

    .tbl-wrap {{ overflow:auto; border:1px solid #94A3B8; border-radius:10px; background:#FFFFFF; margin-bottom:18px; }}
    .tbl {{ width:100%; border-collapse:collapse; font-size:14px; color:{TEKS}; }}
    .tbl th {{ position:sticky; top:0; background:{NAVY}; color:#FFFFFF; text-align:left; padding:11px 14px;
        font-size:12px; letter-spacing:0.7px; font-weight:800; text-transform:uppercase; white-space:nowrap; }}
    .tbl td {{ padding:11px 14px; border-bottom:1px solid #CBD5E1; font-weight:700; vertical-align:top;
        line-height:1.55; text-transform:uppercase; color:{TEKS}; background:#FFFFFF; }}
    .tbl tr:nth-child(even) td {{ background:#F1F5F9; }}
    .tbl td.num {{ text-align:right; white-space:nowrap; }}
    .tbl td.wide {{ min-width:340px; }}

    .foot {{ color:{TEKS_SEKUNDER}; font-size:12px; font-weight:800; letter-spacing:0.5px;
        text-transform:uppercase; margin-top:30px; border-top:1px solid #94A3B8; padding-top:12px; }}
    </style>
    """
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
NAMA_BULAN = {v: k.upper() for k, v in BULAN.items()}

NO_FINDING = (
    "tidak ada temuan", "tidak ada", "tdk ada", "nihil",
    "tidak ditemukan temuan", "secara keseluruhan semua sudah sesuai",
)

# Urutan = prioritas. Satu butir temuan masuk ke SATU jenis (yang pertama cocok).
KATEGORI = {
    "NOTA MANUAL": (
        r"nota manual|kwitansi manual",
        "Nota manual tidak diinput, tidak lengkap, hilang, atau tidak ada lembar aslinya.",
    ),
    "PASSWORD & BA BRANKAS": (
        r"brankas|pa?s{1,2}word",
        "Password brankas belum diganti, BA belum diperbarui atau belum lengkap tanda tangan.",
    ),
    "KASBON / BON SEMENTARA": (
        r"kasbon|bon sementara|\bkb\b|cashbon",
        "Kasbon menggantung, belum settlement/realisasi, atau pencatatan bon tidak konsisten.",
    ),
    "STB (RECEIVED / POSTED)": (
        r"\bstb\b",
        "STB terlambat di-received/posted, tidak sesuai standar, atau salah input.",
    ),
    "DBS / OUTING / KEGIATAN": (
        r"\bdbs\b|outing|kopkari|reward",
        "Pengeluaran DBS dan kegiatan: bukti, approval, atau rekap tidak lengkap/tidak sesuai.",
    ),
    "TAGIHAN & INVOICE": (
        r"catering|invoice|\binv\b|tagihan",
        "Tagihan catering atau invoice belum diupload, di-reject, perlu revisi, atau pemakaiannya tidak sesuai.",
    ),
    "SR / DP / FULFILLMENT": (
        r"\bsr\b|\bdp\b|ful+fil+ment|ful+fill|\bttu\b|cust deposit|customer deposit",
        "SR, DP, atau deposit customer menggantung dan belum di-fulfill/diselesaikan.",
    ),
    "OMSET / MOP / LAPORAN HARIAN": (
        r"om[sz]et|penjualan|\bbsc\b|\bmop\b|daily report|sumcard|summary card|ojol",
        "Omset tidak tercatat, salah MOP, atau laporan harian tidak sesuai.",
    ),
    "SELISIH KAS & BALANCE": (
        r"selisih|minus|\bplus\b|uang pc|kembalian|modal|balance|remark|remak|confirmed|final",
        "Selisih uang PC/modal/kas, atau balance final tidak diberi remark.",
    ),
    "KELENGKAPAN DOKUMEN & TTD": (
        r"\bttd\b|tanda tangan|lampiran|\bba\b|berita acara|upload|belum diinput|belum input|nota",
        "Dokumen, lampiran, atau tanda tangan belum lengkap.",
    ),
    "KEBERSIHAN & KERAPIAN": (
        r"debu|kotor|tidak rapi|berdebu|rapi",
        "Area kasir/komputer kotor, berdebu, atau tidak rapi.",
    ),
}
LAINNYA = "TEMUAN OPERASIONAL LAINNYA"
DESKRIPSI = {k: v[1].upper() for k, v in KATEGORI.items()}
DESKRIPSI[LAINNYA] = "TEMUAN YANG TIDAK MASUK JENIS LAIN; PERIKSA ISINYA SATU PER SATU."

_REK = {
    "NOTA MANUAL": [
        "Cocokkan nomor nota manual yang terpakai dengan input di sistem setiap kunjungan.",
        "Upload foto nota (termasuk yang cancel) ke sistem nota manual di hari yang sama.",
        "Buat BA bila nota tidak ditemukan atau hilang.",
    ],
    "PASSWORD & BA BRANKAS": [
        "Perbarui BA password brankas setiap ada mutasi PIC/SM/DSM dan pada periode berkala.",
        "Pastikan BA lengkap dengan tanda tangan PIC terkait.",
        "Sesuaikan pemegang akses brankas besar dan kecil dengan kebijakan pengelolaan brankas.",
    ],
    "KASBON / BON SEMENTARA": [
        "Selesaikan realisasi dan settlement kasbon di K2 tepat waktu.",
        "Lengkapi pencatatan Gsheet bon sementara sampai realisasi cashier.",
        "Follow up approver bila terjadi pergantian AM agar proses tidak tertahan.",
    ],
    "STB (RECEIVED / POSTED)": [
        "Lakukan received STB sebelum store opening dan posting STB malam di hari yang sama.",
        "Beri remark dan buat BA bila terpaksa terlambat (misalnya gangguan internet).",
        "Pastikan nominal STB yang diinput sesuai fisik.",
    ],
    "DBS / OUTING / KEGIATAN": [
        "Lengkapi approval AM/SM serta nama PT dan stempel vendor pada nota.",
        "Cocokkan rekap DBS dengan pengeluaran dan bukti serah terima uang.",
        "Lengkapi tanda tangan, absensi, dan lampiran kegiatan.",
    ],
    "TAGIHAN & INVOICE": [
        "Upload ulang tagihan yang di-reject dengan revisi nomor invoice.",
        "Upload tagihan catering yang sudah diterima tepat waktu.",
    ],
    "SR / DP / FULFILLMENT": [
        "Selesaikan SR/DP yang menggantung dan lakukan fulfillment tepat waktu.",
        "Follow up customer deposit yang sudah lama tidak bergerak.",
        "Pantau status received yang belum di-fulfill.",
    ],
    "OMSET / MOP / LAPORAN HARIAN": [
        "Cocokkan Daily Report dengan SBD agar salah MOP atau salah nominal cepat terdeteksi.",
        "Beri remark pada selisih akibat salah MOP.",
        "Catat omset tunai di BSC book/logbook setiap hari.",
    ],
    "SELISIH KAS & BALANCE": [
        "Hitung fisik uang PC dan modal pada setiap pergantian shift.",
        "Beri remark yang jelas pada setiap selisih balance.",
        "Buat BA untuk selisih yang belum terselesaikan.",
    ],
    "KELENGKAPAN DOKUMEN & TTD": [
        "Lengkapi tanda tangan dan lampiran sebelum dokumen dikirim.",
        "Cek kelengkapan berkas pada setiap kunjungan rutin.",
    ],
    "KEBERSIHAN & KERAPIAN": [
        "Buat jadwal kebersihan rutin untuk area kasir dan komputer.",
        "Sertakan pengecekan kerapian area pada checklist visit.",
    ],
    LAINNYA: [
        "Tinjau isian temuan secara manual, lalu tambahkan kata kunci baru bila polanya berulang.",
    ],
}
REKOMENDASI = {k: [p.upper() for p in v] for k, v in _REK.items()}

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
    raw["TANGGAL"] = raw["TANGGAL"].str.upper()
    raw["TAHUN"] = raw["TGL"].dt.year.astype("Int64").astype(str).replace("<NA>", "TIDAK DIKETAHUI")
    raw["BULAN"] = raw["TGL"].dt.month.map(NAMA_BULAN).fillna("TIDAK DIKETAHUI")
    raw = raw.reset_index(drop=True)
    raw["VID"] = raw.index

    def status(t):
        if t == "":
            return "BELUM DIISI"
        return "TIDAK ADA TEMUAN" if is_clean(t) else "ADA TEMUAN"

    raw["STATUS"] = raw["TEMUAN"].apply(status)

    baris = []
    for _, r in raw[raw["STATUS"] == "ADA TEMUAN"].iterrows():
        for no, teks in enumerate(split_items(r["TEMUAN"]), 1):
            baris.append(
                {
                    "VID": r["VID"], "TANGGAL": r["TANGGAL"], "TGL": r["TGL"],
                    "TAHUN": r["TAHUN"], "BULAN": r["BULAN"],
                    "NAMA_FRA": r["NAMA_FRA"], "KODE_STORE": r["KODE_STORE"],
                    "NAMA_STORE": r["NAMA_STORE"], "NO": no,
                    "TEMUAN": teks.upper(), "KATEGORI": kategori_utama(teks),
                }
            )
    kolom = ["VID", "TANGGAL", "TGL", "TAHUN", "BULAN", "NAMA_FRA", "KODE_STORE",
             "NAMA_STORE", "NO", "TEMUAN", "KATEGORI"]
    items = pd.DataFrame(baris, columns=kolom)
    jumlah = items.groupby("VID").size()
    raw["JUMLAH_TEMUAN"] = raw["VID"].map(jumlah).fillna(0).astype(int)
    raw["TEMUAN"] = raw["TEMUAN"].str.upper()
    return raw, items
# --- HELPER END ---


@st.cache_data(ttl=300, show_spinner="MENGAMBIL DATA DARI GOOGLE SHEET...")
def load_data(sheet_id: str, sheet_name: str):
    url = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
        f"?tqx=out:csv&sheet={quote(sheet_name)}"
    )
    raw = pd.read_csv(url, dtype=str, keep_default_na=False)
    if raw.shape[1] < 6:
        raise ValueError("Sheet harus punya minimal 6 kolom (A sampai F).")
    return olah_data(raw)


# ---------- fungsi tampilan ----------
def esc(x) -> str:
    return html.escape(str(x))


def sec(judul: str, catatan: str = ""):
    isi = f'<div class="sec">{esc(judul)}</div>'
    if catatan:
        isi += f'<div class="note">{esc(catatan)}</div>'
    tulis(isi)


def kartu(judul, nilai, sub, warna=""):
    return (
        f'<div class="metric-box {warna}"><div class="metric-title">{esc(judul)}</div>'
        f'<div class="metric-value">{esc(nilai)}</div><div class="metric-sub">{esc(sub)}</div></div>'
    )


def tabel_html(data: pd.DataFrame, kolom_angka=(), kolom_lebar=(), tinggi=520):
    """Tabel sederhana: teks gelap, huruf besar, header navy. Selalu terbaca di tema apa pun."""
    kepala = "".join(f"<th>{esc(c)}</th>" for c in data.columns)
    baris = []
    for _, r in data.iterrows():
        sel = []
        for c in data.columns:
            kelas = "num" if c in kolom_angka else ("wide" if c in kolom_lebar else "")
            sel.append(f'<td class="{kelas}">{esc(r[c])}</td>')
        baris.append("<tr>" + "".join(sel) + "</tr>")
    return (
        f'<div class="tbl-wrap" style="max-height:{tinggi}px"><table class="tbl">'
        f"<thead><tr>{kepala}</tr></thead><tbody>{''.join(baris)}</tbody></table></div>"
    )


def rapikan(fig, tinggi):
    fig.update_layout(
        font=dict(color=TEKS, size=14),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=tinggi, margin=dict(l=0, r=10, t=10, b=0),
        legend=dict(font=dict(color=TEKS, size=13), title_text=""),
    )
    fig.update_xaxes(gridcolor="#CBD5E1", linecolor="#64748B",
                     tickfont=dict(color=TEKS, size=13), title_font=dict(color=TEKS))
    fig.update_yaxes(gridcolor="#CBD5E1", linecolor="#64748B",
                     tickfont=dict(color=TEKS, size=13), title_font=dict(color=TEKS))
    return fig


def tampil(fig):
    st.plotly_chart(fig, theme=None)


def tgl_id(ts) -> str:
    return f"{ts.day:02d} {NAMA_BULAN[ts.month]} {ts.year}"


def fmt_persen(x) -> str:
    return "-" if pd.isna(x) else f"{x:.1f}%"


WARNA_STATUS = {"ADA TEMUAN": "#DC2626", "TIDAK ADA TEMUAN": "#059669", "BELUM DIISI": "#64748B"}
PALET = ["#1E3A8A", "#2563EB", "#0891B2", "#059669", "#D97706", "#7C3AED",
         "#DB2777", "#475569", "#65A30D", "#0EA5E9", "#B45309", "#94A3B8"]

# ==========================================
# 3. AMBIL DATA
# ==========================================
try:
    visits, items = load_data(SHEET_ID, SHEET_NAME)
except Exception as e:
    st.error(f"GAGAL MEMBACA DATA DARI GOOGLE SHEETS: {e}")
    st.info(
        "PASTIKAN SHEET DIBAGIKAN DENGAN AKSES 'ANYONE WITH THE LINK' (VIEWER) "
        "DAN NAMA TAB PADA SHEET_NAME SUDAH BENAR."
    )
    st.stop()

if visits.empty:
    st.warning("DATA KOSONG.")
    st.stop()

# ==========================================
# 4. SIDEBAR - FILTER
# ==========================================
st.sidebar.markdown("### PANEL FILTER")
if st.sidebar.button("REFRESH DATA"):
    st.cache_data.clear()
    st.rerun()

tahun_list = sorted([t for t in visits["TAHUN"].unique() if t != "TIDAK DIKETAHUI"], reverse=True)
pilih_tahun = st.sidebar.selectbox("TAHUN", ["SEMUA TAHUN"] + tahun_list)
bulan_list = [b for b in NAMA_BULAN.values() if b in visits["BULAN"].unique()]
pilih_bulan = st.sidebar.selectbox("BULAN", ["SEMUA BULAN"] + bulan_list)
fra_list = sorted(visits["NAMA_FRA"].unique())
pilih_fra = st.sidebar.selectbox("FRA", ["SEMUA FRA"] + fra_list)
kata = st.sidebar.text_input("CARI KATA (STORE / ISI TEMUAN)")

df = visits.copy()
if pilih_tahun != "SEMUA TAHUN":
    df = df[df["TAHUN"] == pilih_tahun]
if pilih_bulan != "SEMUA BULAN":
    df = df[df["BULAN"] == pilih_bulan]
if pilih_fra != "SEMUA FRA":
    df = df[df["NAMA_FRA"] == pilih_fra]
if kata.strip():
    k = kata.strip().upper()
    df = df[
        df["TEMUAN"].str.contains(k, regex=False)
        | df["NAMA_STORE"].str.contains(k, regex=False)
        | df["KODE_STORE"].str.contains(k, regex=False)
    ]

if df.empty:
    st.warning("TIDAK ADA DATA SESUAI FILTER.")
    st.stop()

it = items[items["VID"].isin(df["VID"])].copy()

# ==========================================
# 5. HEADER & KPI
# ==========================================
total_visit = len(df)
ada = int((df["STATUS"] == "ADA TEMUAN").sum())
bersih = int((df["STATUS"] == "TIDAK ADA TEMUAN").sum())
terisi = ada + bersih
total_temuan = len(it)
store_dikunjungi = df["KODE_STORE"].nunique()
store_ada_temuan = df[df["STATUS"] == "ADA TEMUAN"]["KODE_STORE"].nunique()
persen_visit = (ada / terisi * 100) if terisi else 0
rata = total_temuan / ada if ada else 0

tgl_valid = df["TGL"].dropna()
periode = (
    f"PERIODE: {tgl_id(tgl_valid.min())} - {tgl_id(tgl_valid.max())}"
    if not tgl_valid.empty else "PERIODE: -"
)
tulis(
    f"""
    <div class="banner">
        <div class="b-title">DASHBOARD ANALISA TEMUAN VISIT FRA</div>
        <div class="b-sub">LAPORAN EKSEKUTIF HASIL KUNJUNGAN LAPANGAN</div>
        <span class="b-chip">{esc(periode)}</span>
        <span class="b-chip">FRA: {esc(pilih_fra)}</span>
        <span class="b-chip">SUMBER: GOOGLE SHEET (OTOMATIS)</span>
    </div>
    """
)

tulis(
    '<div class="metric-container">'
    + kartu("TOTAL VISIT", total_visit, f"{store_dikunjungi} STORE DIKUNJUNGI")
    + kartu("VISIT DENGAN TEMUAN", ada, f"DARI {terisi} VISIT TERDOKUMENTASI", "k-amber")
    + kartu("TOTAL TEMUAN", total_temuan, f"RATA-RATA {rata:.1f} TEMUAN PER VISIT", "k-amber")
    + kartu("PERSENTASE VISIT DENGAN TEMUAN", f"{persen_visit:.1f}%", "TERHADAP VISIT TERDOKUMENTASI",
            "k-amber" if persen_visit > BATAS_AMBER else "k-green")
    + kartu("VISIT TANPA TEMUAN", bersih, "HASIL KUNJUNGAN SESUAI STANDAR", "k-green")
    + "</div>"
)

if it.empty:
    st.success("TIDAK ADA TEMUAN PADA FILTER YANG DIPILIH.")
    st.stop()

# Ringkasan per jenis (dipakai beberapa tab)
jenis = (
    it.groupby("KATEGORI")
    .agg(JUMLAH=("NO", "size"), STORE_N=("KODE_STORE", "nunique"), FRA_N=("NAMA_FRA", "nunique"))
    .reset_index()
    .sort_values("JUMLAH", ascending=False)
    .reset_index(drop=True)
)
jenis["PERSEN"] = (jenis["JUMLAH"] / total_temuan * 100).round(1)
jenis["ARTI"] = jenis["KATEGORI"].map(DESKRIPSI)
peta_warna = {k: PALET[i % len(PALET)] for i, k in enumerate(jenis["KATEGORI"])}
top3 = jenis.head(3)
top = jenis.iloc[0]


def kalimat_ringkasan() -> str:
    return (
        f'<div class="i-line">1. DARI {terisi} VISIT YANG TERDOKUMENTASI, TERDAPAT {ada} VISIT '
        f"({persen_visit:.1f}%) DENGAN CATATAN TEMUAN, DENGAN TOTAL {total_temuan} TEMUAN.</div>"
        f'<div class="i-line">2. JENIS TEMUAN DENGAN FREKUENSI TERTINGGI ADALAH {esc(top.KATEGORI)} '
        f"({top.JUMLAH} TEMUAN, {top.PERSEN}% DARI TOTAL).</div>"
        f'<div class="i-line">3. TEMUAN TERSEBAR PADA {store_ada_temuan} DARI {store_dikunjungi} STORE '
        f"YANG DIKUNJUNGI.</div>"
        f'<div class="i-line">4. PERBAIKAN PROSES SEBAIKNYA DIPRIORITASKAN PADA TIGA JENIS TEMUAN TERATAS.</div>'
    )


tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["RINGKASAN EKSEKUTIF", "JENIS TEMUAN", "REKAP FRA & STORE", "RINCIAN TEMUAN", "KESIMPULAN & REKOMENDASI"]
)

# ------------------------------------------
# TAB 1: RINGKASAN
# ------------------------------------------
with tab1:
    tulis(
        f'<div class="insight"><div class="i-title">RINGKASAN HASIL ANALISA</div>'
        f"{kalimat_ringkasan()}</div>"
    )

    c1, c2 = st.columns([6, 4])
    with c1:
        sec("KOMPOSISI JENIS TEMUAN", "JUMLAH TEMUAN PER JENIS")
        d = jenis.sort_values("JUMLAH", ascending=True).copy()
        d["LABEL"] = d.apply(lambda r: f"{r['JUMLAH']} TEMUAN ({r['PERSEN']}%)", axis=1)
        fig = px.bar(
            d, x="JUMLAH", y="KATEGORI", orientation="h", text="LABEL",
            color="KATEGORI", color_discrete_map=peta_warna,
        )
        fig.update_traces(textposition="outside", textfont=dict(color=TEKS, size=13))
        fig.update_layout(xaxis_title="", yaxis_title="", showlegend=False)
        fig.update_xaxes(range=[0, d["JUMLAH"].max() * 1.45])
        tampil(rapikan(fig, max(360, 44 * len(d) + 60)))
    with c2:
        sec("STATUS SELURUH VISIT", "KOMPOSISI HASIL KUNJUNGAN")
        st_cnt = df["STATUS"].value_counts().reset_index()
        st_cnt.columns = ["STATUS", "JUMLAH"]
        fig = px.pie(
            st_cnt, names="STATUS", values="JUMLAH", hole=0.55,
            color="STATUS", color_discrete_map=WARNA_STATUS,
        )
        fig.update_traces(textinfo="value+percent", textfont=dict(color="#FFFFFF", size=15))
        fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5))
        tampil(rapikan(fig, 400))

    sec("TREN KUNJUNGAN PER HARI", "JUMLAH VISIT PER TANGGAL BERDASARKAN STATUS")
    harian = df.dropna(subset=["TGL"]).copy()
    if not harian.empty:
        harian["TGL_ONLY"] = harian["TGL"].dt.normalize()
        g = harian.groupby(["TGL_ONLY", "STATUS"]).size().reset_index(name="JUMLAH VISIT")
        g["HARI"] = g["TGL_ONLY"].apply(lambda t: f"{t.day:02d} {NAMA_BULAN[t.month][:3]}")
        urut_hari = g[["TGL_ONLY", "HARI"]].drop_duplicates().sort_values("TGL_ONLY")["HARI"].tolist()
        fig = px.bar(
            g, x="HARI", y="JUMLAH VISIT", color="STATUS",
            color_discrete_map=WARNA_STATUS, category_orders={"HARI": urut_hari},
        )
        fig.update_layout(xaxis_title="")
        tampil(rapikan(fig, 360))

# ------------------------------------------
# TAB 2: JENIS TEMUAN
# ------------------------------------------
with tab2:
    sec("KLASIFIKASI JENIS TEMUAN", "SETIAP TEMUAN DIKELOMPOKKAN KE SATU JENIS BERDASARKAN KATA KUNCI")
    tabel = pd.DataFrame(
        {
            "NO": range(1, len(jenis) + 1),
            "JENIS TEMUAN": jenis["KATEGORI"],
            "PENJELASAN": jenis["ARTI"],
            "JUMLAH TEMUAN": jenis["JUMLAH"],
            "% DARI TOTAL": jenis["PERSEN"].map(lambda x: f"{x:.1f}%"),
            "JUMLAH STORE": jenis["STORE_N"],
        }
    )
    tulis(tabel_html(tabel, kolom_angka=("NO", "JUMLAH TEMUAN", "% DARI TOTAL", "JUMLAH STORE"),
                     kolom_lebar=("PENJELASAN",), tinggi=560))

    sec("SEBARAN JENIS TEMUAN PER FRA", "ANGKA = JUMLAH TEMUAN")
    pivot = it.pivot_table(index="NAMA_FRA", columns="KATEGORI", values="NO",
                           aggfunc="count", fill_value=0)
    pivot = pivot[[k for k in jenis["KATEGORI"] if k in pivot.columns]]
    fig = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale="Blues")
    fig.update_layout(xaxis_title="", yaxis_title="", coloraxis_showscale=False)
    fig.update_xaxes(tickangle=-35)
    tampil(rapikan(fig, max(340, 36 * len(pivot) + 200)))

    sec("URAIAN TEMUAN PER JENIS", "PILIH JENIS UNTUK MELIHAT SELURUH URAIAN TEMUANNYA")
    pilih = st.selectbox("PILIH JENIS TEMUAN", jenis["KATEGORI"].tolist())
    sub = it[it["KATEGORI"] == pilih]
    tulis(
        '<div class="metric-container">'
        + kartu("JUMLAH TEMUAN", len(sub), "PADA JENIS INI", "k-amber")
        + kartu("JUMLAH STORE", sub["KODE_STORE"].nunique(), "STORE BERBEDA")
        + kartu("JUMLAH FRA", sub["NAMA_FRA"].nunique(), "FRA BERBEDA")
        + "</div>"
    )
    tulis(f'<div class="note">{esc(DESKRIPSI[pilih])}</div>')
    uraian = sub.sort_values("TGL", ascending=False)
    tabel = pd.DataFrame(
        {
            "TANGGAL": uraian["TANGGAL"],
            "FRA": uraian["NAMA_FRA"],
            "STORE": uraian["KODE_STORE"] + " - " + uraian["NAMA_STORE"],
            "URAIAN TEMUAN": uraian["TEMUAN"],
        }
    )
    tulis(tabel_html(tabel, kolom_lebar=("URAIAN TEMUAN",)))

# ------------------------------------------
# TAB 3: REKAP FRA & STORE
# ------------------------------------------
with tab3:
    sec("REKAPITULASI PER FRA", "JUMLAH TEMUAN PER FRA, DIRINCI PER JENIS")
    fra_jenis = it.groupby(["NAMA_FRA", "KATEGORI"]).size().reset_index(name="JUMLAH TEMUAN")
    urut_fra = it.groupby("NAMA_FRA").size().sort_values(ascending=True).index.tolist()
    fig = px.bar(
        fra_jenis, x="JUMLAH TEMUAN", y="NAMA_FRA", color="KATEGORI", orientation="h",
        color_discrete_map=peta_warna, category_orders={"NAMA_FRA": urut_fra},
    )
    fig.update_layout(xaxis_title="", yaxis_title="",
                      legend=dict(orientation="h", yanchor="top", y=-0.1))
    tampil(rapikan(fig, max(360, 36 * len(urut_fra) + 190)))

    fra_tab = (
        df.groupby("NAMA_FRA")
        .agg(
            VISIT=("VID", "size"),
            ADA=("STATUS", lambda s: int((s == "ADA TEMUAN").sum())),
            BERSIH=("STATUS", lambda s: int((s == "TIDAK ADA TEMUAN").sum())),
            TEMUAN=("JUMLAH_TEMUAN", "sum"),
        )
        .reset_index()
        .sort_values("NAMA_FRA")
    )
    penyebut = fra_tab["ADA"] + fra_tab["BERSIH"]
    fra_tab["PERSEN"] = (fra_tab["ADA"] / penyebut.where(penyebut > 0) * 100).round(1)
    tabel = pd.DataFrame(
        {
            "FRA": fra_tab["NAMA_FRA"],
            "TOTAL VISIT": fra_tab["VISIT"],
            "VISIT DENGAN TEMUAN": fra_tab["ADA"],
            "VISIT TANPA TEMUAN": fra_tab["BERSIH"],
            "TOTAL TEMUAN": fra_tab["TEMUAN"],
            "% VISIT DENGAN TEMUAN": fra_tab["PERSEN"].map(fmt_persen),
        }
    )
    tulis(tabel_html(
        tabel,
        kolom_angka=("TOTAL VISIT", "VISIT DENGAN TEMUAN", "VISIT TANPA TEMUAN",
                     "TOTAL TEMUAN", "% VISIT DENGAN TEMUAN"),
    ))

    sec("REKAPITULASI PER STORE", "JUMLAH TEMUAN PER STORE PADA PERIODE YANG DIPILIH")
    store = (
        it.groupby(["KODE_STORE", "NAMA_STORE"])
        .agg(JUMLAH=("NO", "size"), JENIS=("KATEGORI", "nunique"),
             UTAMA=("KATEGORI", lambda s: s.value_counts().index[0]))
        .reset_index()
        .sort_values(["JUMLAH", "NAMA_STORE"], ascending=[False, True])
    )
    tabel = pd.DataFrame(
        {
            "KODE STORE": store["KODE_STORE"],
            "NAMA STORE": store["NAMA_STORE"],
            "JUMLAH TEMUAN": store["JUMLAH"],
            "JUMLAH JENIS": store["JENIS"],
            "JENIS TEMUAN DOMINAN": store["UTAMA"],
        }
    )
    tulis(tabel_html(tabel, kolom_angka=("JUMLAH TEMUAN", "JUMLAH JENIS"), tinggi=480))

# ------------------------------------------
# TAB 4: RINCIAN TEMUAN
# ------------------------------------------
with tab4:
    sec("RINCIAN TEMUAN", "PILIH TAMPILAN: PER STORE ATAU SELURUH TEMUAN")
    mode = st.radio("TAMPILAN", ["PER STORE", "SELURUH TEMUAN"], horizontal=True)

    if mode == "PER STORE":
        ada_df = df[df["STATUS"] == "ADA TEMUAN"].sort_values(["NAMA_STORE", "TGL"])
        opsi = (ada_df["KODE_STORE"] + " - " + ada_df["NAMA_STORE"] + " | " + ada_df["TANGGAL"]).tolist()
        vids = ada_df["VID"].tolist()
        pilih_store = st.selectbox("PILIH STORE DAN TANGGAL VISIT", opsi)
        vid = vids[opsi.index(pilih_store)]
        r = df[df["VID"] == vid].iloc[0]
        tulis(
            f'<div class="insight"><div class="i-title">{esc(r["KODE_STORE"])} - {esc(r["NAMA_STORE"])}</div>'
            f'<div class="i-line">FRA: {esc(r["NAMA_FRA"])}</div>'
            f'<div class="i-line">TANGGAL VISIT: {esc(r["TANGGAL"])}</div>'
            f'<div class="i-line">JUMLAH TEMUAN: {r["JUMLAH_TEMUAN"]}</div></div>'
        )
        satu = it[it["VID"] == vid].sort_values("NO")
        tabel = pd.DataFrame(
            {"NO": satu["NO"], "JENIS TEMUAN": satu["KATEGORI"], "URAIAN TEMUAN": satu["TEMUAN"]}
        )
        tulis(tabel_html(tabel, kolom_angka=("NO",), kolom_lebar=("URAIAN TEMUAN",), tinggi=600))
    else:
        pilih_jenis = st.multiselect(
            "FILTER JENIS TEMUAN", jenis["KATEGORI"].tolist(), default=jenis["KATEGORI"].tolist()
        )
        semua = it[it["KATEGORI"].isin(pilih_jenis)].sort_values(
            ["TGL", "VID", "NO"], ascending=[False, True, True]
        )
        tabel_penuh = pd.DataFrame(
            {
                "TANGGAL": semua["TANGGAL"],
                "FRA": semua["NAMA_FRA"],
                "STORE": semua["KODE_STORE"] + " - " + semua["NAMA_STORE"],
                "JENIS TEMUAN": semua["KATEGORI"],
                "URAIAN TEMUAN": semua["TEMUAN"],
            }
        )
        batas = 300
        tulis(f'<div class="note">MENAMPILKAN {min(len(tabel_penuh), batas)} DARI {len(tabel_penuh)} TEMUAN'
              f'{" (UNDUH CSV UNTUK DATA LENGKAP)" if len(tabel_penuh) > batas else ""}</div>')
        tulis(tabel_html(tabel_penuh.head(batas), kolom_lebar=("URAIAN TEMUAN",), tinggi=650))
        st.download_button(
            "UNDUH CSV", tabel_penuh.to_csv(index=False).encode("utf-8"),
            file_name="rincian_temuan.csv", mime="text/csv",
        )

# ------------------------------------------
# TAB 5: KESIMPULAN & REKOMENDASI
# ------------------------------------------
with tab5:
    sec("KESIMPULAN", "RINGKASAN HASIL ANALISA BERDASARKAN FILTER YANG DIPILIH")
    tulis(f'<div class="insight">{kalimat_ringkasan()}</div>')

    sec("REKOMENDASI PERBAIKAN PROSES", "DISUSUN DARI POLA TEMUAN; SESUAIKAN DENGAN KEBIJAKAN DAN SOP PERUSAHAAN")
    for no, r in enumerate(top3.itertuples(), 1):
        poin = "".join(f"<li>{esc(p)}</li>" for p in REKOMENDASI.get(r.KATEGORI, REKOMENDASI[LAINNYA]))
        tulis(
            f"""
            <div class="rec">
                <div class="r-title">{no}. {esc(r.KATEGORI)}</div>
                <div class="r-meta">{r.JUMLAH} TEMUAN | {r.STORE_N} STORE | {r.PERSEN}% DARI TOTAL</div>
                <div class="r-desc">{esc(DESKRIPSI[r.KATEGORI])}</div>
                <ul>{poin}</ul>
            </div>
            """
        )

tulis('<div class="foot">SUMBER DATA: GOOGLE SHEET TEMUAN | DIPERBARUI OTOMATIS SETIAP 5 MENIT</div>')
