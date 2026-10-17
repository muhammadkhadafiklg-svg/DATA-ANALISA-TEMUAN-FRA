import hashlib
import html
import json
import re
from urllib.parse import quote

import pandas as pd
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

    .bl-wrap {{ background:#FFFFFF; border:1px solid #94A3B8; border-radius:10px; padding:18px 20px; margin-bottom:18px; }}
    .bl-row {{ display:grid; grid-template-columns:minmax(160px,300px) 1fr 140px; gap:14px; align-items:center; margin-bottom:12px; }}
    .bl-row:last-child {{ margin-bottom:0; }}
    .bl-label {{ color:{TEKS}; font-size:13px; font-weight:800; text-transform:uppercase; letter-spacing:0.3px; line-height:1.3; }}
    .bl-track {{ background:#E2E8F0; height:20px; border-radius:10px; overflow:hidden; }}
    .bl-fill {{ height:100%; border-radius:10px; background:{BIRU}; }}
    .bl-val {{ color:{TEKS}; font-size:14px; font-weight:800; text-align:right; white-space:nowrap; }}
    @media (max-width:700px) {{ .bl-row {{ grid-template-columns:1fr 110px; }} .bl-label {{ grid-column:1 / -1; }} }}
    .cols-wrap {{ background:#FFFFFF; border:1px solid #94A3B8; border-radius:10px; padding:16px 18px 12px; margin-bottom:18px; overflow-x:auto; }}
    .cols {{ display:flex; align-items:flex-end; gap:12px; min-height:210px; }}
    .c {{ flex:0 0 58px; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; }}
    .c-val {{ color:{TEKS}; font-size:14px; font-weight:800; margin-bottom:4px; }}
    .c-bar {{ width:100%; background:{BIRU}; border-radius:6px 6px 0 0; }}
    .c-lab {{ color:{TEKS}; font-size:12px; font-weight:800; margin-top:6px; white-space:nowrap; }}
    .c-sub {{ color:{TEKS_SEKUNDER}; font-size:11px; font-weight:700; white-space:nowrap; }}
    .prio {{ display:inline-block; color:#FFFFFF; font-size:11px; font-weight:800; letter-spacing:0.5px;
        padding:3px 10px; border-radius:12px; margin-left:8px; vertical-align:middle; background:{BIRU}; }}
    .prio.tinggi {{ background:#B45309; }}
    .prio.rendah {{ background:#047857; }}
    .rec .r-lbl {{ color:{BIRU}; font-size:12px; font-weight:800; letter-spacing:0.6px; margin-top:10px; }}
    .rec .r-txt {{ color:{TEKS}; font-size:14px; font-weight:700; text-transform:uppercase; line-height:1.6; }}
    .ai-note {{ color:{TEKS_SEKUNDER}; font-size:12px; font-weight:700; text-transform:uppercase; margin:6px 0 14px 4px; }}

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
    raw = raw.copy()
    if raw.shape[1] < 7:
        raw["_G"] = ""  # kolom G kosong / belum terbaca
    raw = raw.iloc[:, :7].copy()
    raw.columns = ["TANGGAL", "NAMA_FRA", "NIP", "KODE_STORE", "NAMA_STORE", "TEMUAN", "KODE_BU"]
    for c in raw.columns:
        raw[c] = raw[c].fillna("").astype(str).str.strip()
    raw = raw[(raw["NAMA_FRA"] != "") | (raw["NAMA_STORE"] != "")].copy()
    raw["NAMA_FRA"] = raw["NAMA_FRA"].str.upper()
    raw["NAMA_STORE"] = raw["NAMA_STORE"].str.upper()
    raw["KODE_STORE"] = raw["KODE_STORE"].str.upper()
    raw["KODE_BU"] = raw["KODE_BU"].str.upper().replace("", "TANPA KODE BU")
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
                    "NAMA_STORE": r["NAMA_STORE"], "KODE_BU": r["KODE_BU"], "NO": no,
                    "TEMUAN": teks.upper(), "KATEGORI": kategori_utama(teks),
                }
            )
    kolom = ["VID", "TANGGAL", "TGL", "TAHUN", "BULAN", "NAMA_FRA", "KODE_STORE",
             "NAMA_STORE", "KODE_BU", "NO", "TEMUAN", "KATEGORI"]
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


def rahasia(kunci, bawaan=None):
    try:
        return st.secrets[kunci]
    except Exception:
        return bawaan


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


def bar_list(data) -> str:
    """Grafik batang horizontal sederhana. data = [(label, nilai, teks, warna_opsional), ...]"""
    if not data:
        return ""
    maks = max(d[1] for d in data) or 1
    baris = []
    for d in data:
        label, nilai, teks = d[0], d[1], d[2]
        warna = d[3] if len(d) > 3 else None
        lebar = max(2.0, nilai / maks * 100) if nilai > 0 else 0
        gaya = f"width:{lebar:.1f}%" + (f";background:{warna}" if warna else "")
        baris.append(
            f'<div class="bl-row"><div class="bl-label">{esc(label)}</div>'
            f'<div class="bl-track"><div class="bl-fill" style="{gaya}"></div></div>'
            f'<div class="bl-val">{esc(teks)}</div></div>'
        )
    return '<div class="bl-wrap">' + "".join(baris) + "</div>"


def kolom_chart(data) -> str:
    """Grafik batang vertikal sederhana. data = [(label, nilai, sub), ...]"""
    if not data:
        return ""
    maks = max(d[1] for d in data) or 1
    isi = []
    for label, nilai, sub in data:
        tinggi = max(4, int(nilai / maks * 170)) if nilai > 0 else 2
        isi.append(
            f'<div class="c"><div class="c-val">{esc(nilai)}</div>'
            f'<div class="c-bar" style="height:{tinggi}px"></div>'
            f'<div class="c-lab">{esc(label)}</div><div class="c-sub">{esc(sub)}</div></div>'
        )
    return f'<div class="cols-wrap"><div class="cols">{"".join(isi)}</div></div>'


def tgl_id(ts) -> str:
    return f"{ts.day:02d} {NAMA_BULAN[ts.month]} {ts.year}"


def fmt_persen(x) -> str:
    return "-" if pd.isna(x) else f"{x:.1f}%"


WARNA_STATUS = {"ADA TEMUAN": "#D97706", "TIDAK ADA TEMUAN": "#059669", "BELUM DIISI": "#64748B"}

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
bu_list = sorted(visits["KODE_BU"].unique())
pilih_bu = st.sidebar.selectbox("KODE BU", ["SEMUA BU"] + bu_list)
fra_list = sorted(visits["NAMA_FRA"].unique())
pilih_fra = st.sidebar.selectbox("FRA", ["SEMUA FRA"] + fra_list)
kata = st.sidebar.text_input("CARI KATA (STORE / ISI TEMUAN)")

df = visits.copy()
if pilih_tahun != "SEMUA TAHUN":
    df = df[df["TAHUN"] == pilih_tahun]
if pilih_bulan != "SEMUA BULAN":
    df = df[df["BULAN"] == pilih_bulan]
if pilih_bu != "SEMUA BU":
    df = df[df["KODE_BU"] == pilih_bu]
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
belum = int((df["STATUS"] == "BELUM DIISI").sum())
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
        <span class="b-chip">KODE BU: {esc(pilih_bu)}</span>
        <span class="b-chip">FRA: {esc(pilih_fra)}</span>
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
    ["RINGKASAN EKSEKUTIF", "JENIS TEMUAN", "REKAP BU, FRA & STORE", "RINCIAN TEMUAN", "KESIMPULAN & REKOMENDASI"]
)

# ------------------------------------------
# TAB 1: RINGKASAN
# ------------------------------------------
with tab1:
    tulis(
        f'<div class="insight"><div class="i-title">RINGKASAN HASIL ANALISA</div>'
        f"{kalimat_ringkasan()}</div>"
    )

    sec("KOMPOSISI JENIS TEMUAN", "JUMLAH TEMUAN PER JENIS DAN PERSENTASE TERHADAP TOTAL")
    tulis(bar_list([
        (r.KATEGORI, int(r.JUMLAH), f"{r.JUMLAH} ({r.PERSEN}%)") for r in jenis.itertuples()
    ]))

    sec("STATUS SELURUH VISIT", "JUMLAH VISIT BERDASARKAN HASIL PENCATATAN")
    status_data = [
        ("ADA TEMUAN", ada, f"{ada} VISIT", WARNA_STATUS["ADA TEMUAN"]),
        ("TIDAK ADA TEMUAN", bersih, f"{bersih} VISIT", WARNA_STATUS["TIDAK ADA TEMUAN"]),
    ]
    if belum:
        status_data.append(("BELUM DIISI", belum, f"{belum} VISIT", WARNA_STATUS["BELUM DIISI"]))
    tulis(bar_list(status_data))

    sec("TREN TEMUAN PER TANGGAL KUNJUNGAN", "ANGKA ATAS = JUMLAH TEMUAN; TEKS DI BAWAH TANGGAL = JUMLAH VISIT")
    hr = df.dropna(subset=["TGL"]).copy()
    if not hr.empty:
        hr["TGL_ONLY"] = hr["TGL"].dt.normalize()
        g = (
            hr.groupby("TGL_ONLY")
            .agg(TEMUAN=("JUMLAH_TEMUAN", "sum"), VISIT=("VID", "size"))
            .reset_index()
            .sort_values("TGL_ONLY")
        )
        tulis(kolom_chart([
            (f"{r.TGL_ONLY.day:02d} {NAMA_BULAN[r.TGL_ONLY.month][:3]}", int(r.TEMUAN), f"{int(r.VISIT)} VISIT")
            for r in g.itertuples()
        ]))

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
            "KODE BU": uraian["KODE_BU"],
            "FRA": uraian["NAMA_FRA"],
            "STORE": uraian["KODE_STORE"] + " - " + uraian["NAMA_STORE"],
            "URAIAN TEMUAN": uraian["TEMUAN"],
        }
    )
    tulis(tabel_html(tabel, kolom_lebar=("URAIAN TEMUAN",)))

# ------------------------------------------
# TAB 3: REKAP BU, FRA & STORE
# ------------------------------------------
with tab3:
    sec("REKAPITULASI PER KODE BU", "JUMLAH TEMUAN DAN VISIT PER KODE BU")
    bu_tab = (
        df.groupby("KODE_BU")
        .agg(
            VISIT=("VID", "size"),
            ADA=("STATUS", lambda s: int((s == "ADA TEMUAN").sum())),
            BERSIH=("STATUS", lambda s: int((s == "TIDAK ADA TEMUAN").sum())),
            TEMUAN=("JUMLAH_TEMUAN", "sum"),
        )
        .reset_index()
        .sort_values(["TEMUAN", "KODE_BU"], ascending=[False, True])
    )
    pb = bu_tab["ADA"] + bu_tab["BERSIH"]
    bu_tab["PERSEN"] = (bu_tab["ADA"] / pb.where(pb > 0) * 100).round(1)
    tulis(bar_list([(r.KODE_BU, int(r.TEMUAN), f"{r.TEMUAN} TEMUAN") for r in bu_tab.itertuples()]))
    tabel = pd.DataFrame(
        {
            "KODE BU": bu_tab["KODE_BU"],
            "TOTAL VISIT": bu_tab["VISIT"],
            "VISIT DENGAN TEMUAN": bu_tab["ADA"],
            "VISIT TANPA TEMUAN": bu_tab["BERSIH"],
            "TOTAL TEMUAN": bu_tab["TEMUAN"],
            "% VISIT DENGAN TEMUAN": bu_tab["PERSEN"].map(fmt_persen),
        }
    )
    tulis(tabel_html(
        tabel,
        kolom_angka=("TOTAL VISIT", "VISIT DENGAN TEMUAN", "VISIT TANPA TEMUAN",
                     "TOTAL TEMUAN", "% VISIT DENGAN TEMUAN"),
        tinggi=420,
    ))

    sec("REKAPITULASI PER FRA", "JUMLAH TEMUAN PER FRA")
    fra_tab = (
        df.groupby("NAMA_FRA")
        .agg(
            VISIT=("VID", "size"),
            ADA=("STATUS", lambda s: int((s == "ADA TEMUAN").sum())),
            BERSIH=("STATUS", lambda s: int((s == "TIDAK ADA TEMUAN").sum())),
            TEMUAN=("JUMLAH_TEMUAN", "sum"),
        )
        .reset_index()
        .sort_values(["TEMUAN", "NAMA_FRA"], ascending=[False, True])
    )
    pf = fra_tab["ADA"] + fra_tab["BERSIH"]
    fra_tab["PERSEN"] = (fra_tab["ADA"] / pf.where(pf > 0) * 100).round(1)
    dominan = it.groupby("NAMA_FRA")["KATEGORI"].agg(lambda s: s.value_counts().index[0])
    fra_tab["DOMINAN"] = fra_tab["NAMA_FRA"].map(dominan).fillna("-")
    tulis(bar_list([(r.NAMA_FRA, int(r.TEMUAN), f"{r.TEMUAN} TEMUAN") for r in fra_tab.itertuples()]))
    tabel = pd.DataFrame(
        {
            "FRA": fra_tab["NAMA_FRA"],
            "TOTAL VISIT": fra_tab["VISIT"],
            "VISIT DENGAN TEMUAN": fra_tab["ADA"],
            "VISIT TANPA TEMUAN": fra_tab["BERSIH"],
            "TOTAL TEMUAN": fra_tab["TEMUAN"],
            "% VISIT DENGAN TEMUAN": fra_tab["PERSEN"].map(fmt_persen),
            "JENIS TEMUAN DOMINAN": fra_tab["DOMINAN"],
        }
    )
    tulis(tabel_html(
        tabel,
        kolom_angka=("TOTAL VISIT", "VISIT DENGAN TEMUAN", "VISIT TANPA TEMUAN",
                     "TOTAL TEMUAN", "% VISIT DENGAN TEMUAN"),
        tinggi=480,
    ))

    sec("REKAPITULASI PER STORE", "JUMLAH TEMUAN PER STORE PADA PERIODE YANG DIPILIH")
    store = (
        it.groupby(["KODE_STORE", "NAMA_STORE", "KODE_BU"])
        .agg(JUMLAH=("NO", "size"), JENIS=("KATEGORI", "nunique"),
             UTAMA=("KATEGORI", lambda s: s.value_counts().index[0]))
        .reset_index()
        .sort_values(["JUMLAH", "NAMA_STORE"], ascending=[False, True])
    )
    tabel = pd.DataFrame(
        {
            "KODE STORE": store["KODE_STORE"],
            "NAMA STORE": store["NAMA_STORE"],
            "KODE BU": store["KODE_BU"],
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
            f'<div class="i-line">KODE BU: {esc(r["KODE_BU"])}</div>'
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
        pilihan_jenis = ["SEMUA JENIS TEMUAN"] + jenis["KATEGORI"].tolist()
        pilih_jenis = st.selectbox("JENIS TEMUAN", pilihan_jenis)
        semua = it if pilih_jenis == "SEMUA JENIS TEMUAN" else it[it["KATEGORI"] == pilih_jenis]
        semua = semua.sort_values(["TGL", "VID", "NO"], ascending=[False, True, True])
        tabel_penuh = pd.DataFrame(
            {
                "TANGGAL": semua["TANGGAL"],
                "KODE BU": semua["KODE_BU"],
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
# TAB 5: KESIMPULAN & REKOMENDASI (AI)
# ------------------------------------------
SISTEM_AI = (
    "ANDA ADALAH ANALIS PENGENDALIAN INTERNAL SENIOR DI PERUSAHAAN RITEL MULTI-BU. "
    "TUGAS ANDA MENYUSUN KESIMPULAN EKSEKUTIF DAN REKOMENDASI PERBAIKAN PROSES DARI HASIL VISIT FRA KE STORE. "
    "ATURAN: (1) TULIS DALAM BAHASA INDONESIA FORMAL, SELURUHNYA HURUF KAPITAL. "
    "(2) NETRAL DAN PROFESIONAL: JANGAN MENYALAHKAN, MENYEBUT, ATAU MEMBANDINGKAN INDIVIDU, FRA, ATAU STORE TERTENTU; "
    "FOKUS PADA PROSES, SISTEM, DAN KONTROL. "
    "(3) REKOMENDASI HARUS SPESIFIK DAN BERBEDA SATU SAMA LAIN, DISUSUN DARI POLA PADA DATA DAN CONTOH URAIAN YANG DIBERIKAN, "
    "BUKAN SARAN UMUM. SEBUTKAN ANGKA PENDUKUNGNYA. HINDARI KALIMAT YANG BERULANG ATAU KLISE. "
    "(4) JANGAN MENGARANG FAKTA ATAU ANGKA DI LUAR DATA. "
    "(5) KELUARKAN HANYA JSON VALID TANPA TEKS LAIN DENGAN BENTUK: "
    '{"kesimpulan": ["...", "..."], '
    '"rekomendasi": [{"judul": "...", "prioritas": "TINGGI|SEDANG|RENDAH", "dasar_temuan": "...", '
    '"langkah": ["...", "..."], "indikator": "..."}]}. '
    "KESIMPULAN: 3 SAMPAI 5 KALIMAT. REKOMENDASI: 3 SAMPAI 5 BUTIR, URUT DARI PRIORITAS TERTINGGI; "
    "SETIAP REKOMENDASI MEMILIKI 3 SAMPAI 4 LANGKAH KONKRET DAN SATU INDIKATOR KEBERHASILAN YANG TERUKUR."
)


def susun_prompt() -> str:
    contoh = {}
    for kat in jenis["KATEGORI"].head(6):
        teks = it[it["KATEGORI"] == kat]["TEMUAN"].drop_duplicates().head(6)
        contoh[kat] = [t[:220] for t in teks]
    per_bu = (
        df.groupby("KODE_BU")
        .agg(visit=("VID", "size"), temuan=("JUMLAH_TEMUAN", "sum"))
        .reset_index()
        .to_dict("records")
    )
    data = {
        "periode": periode.replace("PERIODE: ", ""),
        "filter_kode_bu": pilih_bu,
        "total_visit": total_visit,
        "visit_dengan_temuan": ada,
        "visit_tanpa_temuan": bersih,
        "total_temuan": total_temuan,
        "persentase_visit_dengan_temuan": round(persen_visit, 1),
        "jumlah_store_dikunjungi": store_dikunjungi,
        "jumlah_store_memiliki_temuan": store_ada_temuan,
        "jenis_temuan": [
            {"jenis": r.KATEGORI, "jumlah": int(r.JUMLAH), "persen": float(r.PERSEN), "jumlah_store": int(r.STORE_N)}
            for r in jenis.itertuples()
        ],
        "rekap_per_kode_bu": per_bu,
        "contoh_uraian_per_jenis": contoh,
    }
    return "DATA RINGKAS HASIL VISIT FRA (JSON):\n" + json.dumps(data, ensure_ascii=False, indent=1)


@st.cache_data(ttl=21600, show_spinner=False)
def minta_ai(prompt: str, model: str) -> str:
    import anthropic

    klien = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    jawab = klien.messages.create(
        model=model,
        max_tokens=3000,
        system=SISTEM_AI,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in jawab.content if getattr(b, "type", "") == "text")


def baca_json_ai(teks: str):
    t = teks.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    a, b = t.find("{"), t.rfind("}")
    if a < 0 or b <= a:
        return None
    try:
        d = json.loads(t[a:b + 1])
    except Exception:
        return None
    if not isinstance(d, dict) or not d.get("kesimpulan") or not d.get("rekomendasi"):
        return None
    return d


def tampil_ai(d: dict):
    kal = d.get("kesimpulan", [])
    if isinstance(kal, str):
        kal = [kal]
    baris = "".join(f'<div class="i-line">{i}. {esc(str(k).upper())}</div>' for i, k in enumerate(kal, 1))
    tulis(f'<div class="insight"><div class="i-title">KESIMPULAN</div>{baris}</div>')

    sec("REKOMENDASI PERBAIKAN PROSES", "DISUSUN AI DARI POLA TEMUAN; VALIDASI DAN SESUAIKAN DENGAN SOP SEBELUM DIGUNAKAN")
    for no, rk in enumerate(d.get("rekomendasi", []), 1):
        if not isinstance(rk, dict):
            continue
        prio = str(rk.get("prioritas", "SEDANG")).upper().strip()
        kelas = {"TINGGI": "tinggi", "RENDAH": "rendah"}.get(prio, "")
        langkah = rk.get("langkah", [])
        if isinstance(langkah, str):
            langkah = [langkah]
        poin = "".join(f"<li>{esc(str(p).upper())}</li>" for p in langkah)
        tulis(
            f"""
            <div class="rec">
                <div class="r-title">{no}. {esc(str(rk.get("judul", "")).upper())}
                    <span class="prio {kelas}">PRIORITAS {esc(prio)}</span></div>
                <div class="r-lbl">DASAR TEMUAN</div>
                <div class="r-txt">{esc(str(rk.get("dasar_temuan", "")).upper())}</div>
                <div class="r-lbl">LANGKAH PERBAIKAN</div>
                <ul>{poin}</ul>
                <div class="r-lbl">INDIKATOR KEBERHASILAN</div>
                <div class="r-txt">{esc(str(rk.get("indikator", "")).upper())}</div>
            </div>
            """
        )


def tampil_standar():
    sec("REKOMENDASI PERBAIKAN PROSES (STANDAR)", "DISUSUN OTOMATIS DARI TIGA JENIS TEMUAN TERATAS; SESUAIKAN DENGAN SOP PERUSAHAAN")
    for no, r in enumerate(top3.itertuples(), 1):
        poin = "".join(f"<li>{esc(p)}</li>" for p in REKOMENDASI.get(r.KATEGORI, REKOMENDASI[LAINNYA]))
        tulis(
            f"""
            <div class="rec">
                <div class="r-title">{no}. {esc(r.KATEGORI)}</div>
                <div class="r-lbl">{r.JUMLAH} TEMUAN | {r.STORE_N} STORE | {r.PERSEN}% DARI TOTAL</div>
                <div class="r-txt">{esc(DESKRIPSI[r.KATEGORI])}</div>
                <ul>{poin}</ul>
            </div>
            """
        )


with tab5:
    sec("KESIMPULAN & REKOMENDASI", "BERDASARKAN FILTER YANG DIPILIH DI PANEL FILTER")
    prompt = susun_prompt()
    kunci_data = hashlib.md5(prompt.encode("utf-8")).hexdigest()
    model_ai = rahasia("ANTHROPIC_MODEL", "claude-sonnet-5-5")

    if rahasia("ANTHROPIC_API_KEY"):
        if st.button("BUAT KESIMPULAN & REKOMENDASI DENGAN AI"):
            with st.spinner("AI SEDANG MENYUSUN ANALISA..."):
                try:
                    hasil = baca_json_ai(minta_ai(prompt, model_ai))
                    if hasil is None:
                        st.error("FORMAT JAWABAN AI TIDAK DAPAT DIBACA. SILAKAN COBA LAGI.")
                    else:
                        st.session_state["hasil_ai"] = (kunci_data, hasil)
                except Exception as e:
                    st.error(f"AI TIDAK DAPAT DIAKSES: {e}")
        simpan = st.session_state.get("hasil_ai")
        tulis('<div class="ai-note">AI HANYA MENERIMA DATA RINGKAS (JUMLAH PER JENIS DAN CONTOH URAIAN). '
              "NAMA FRA, NAMA STORE, DAN NIP TIDAK DIKIRIM.</div>")
        if simpan and simpan[0] == kunci_data:
            tampil_ai(simpan[1])
        else:
            tulis(f'<div class="insight"><div class="i-title">RINGKASAN OTOMATIS</div>{kalimat_ringkasan()}</div>')
            tulis('<div class="ai-note">TEKAN TOMBOL DI ATAS UNTUK MEMBUAT KESIMPULAN DAN REKOMENDASI '
                  "YANG DISUSUN AI SESUAI DATA PADA FILTER INI.</div>")
            tampil_standar()
    else:
        tulis('<div class="ai-note">FITUR AI BELUM AKTIF. TAMBAHKAN ANTHROPIC_API_KEY PADA SECRETS STREAMLIT '
              "UNTUK MENGAKTIFKANNYA. SEMENTARA ITU DITAMPILKAN RINGKASAN OTOMATIS.</div>")
        tulis(f'<div class="insight"><div class="i-title">RINGKASAN OTOMATIS</div>{kalimat_ringkasan()}</div>')
        tampil_standar()

tulis('<div class="foot">SUMBER DATA: GOOGLE SHEET TEMUAN | DIPERBARUI OTOMATIS SETIAP 5 MENIT</div>')
