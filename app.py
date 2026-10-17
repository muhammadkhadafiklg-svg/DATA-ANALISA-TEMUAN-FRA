import hmac
import re
from urllib.parse import quote

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Dashboard Temuan Visit FRA", layout="wide")

# ================= PENGATURAN (ubah di sini bila perlu) =================
SHEET_ID = "1RfrC_LUAZbKrGEN15KPkBXhUz8ei2jyqGdUaKPS4WMY"
SHEET_NAME = "Sheet1"  # nama tab di Google Sheet
# ========================================================================

# --- HELPER START ---
BULAN = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10,
    "november": 11, "desember": 12,
}

NO_FINDING = (
    "tidak ada temuan", "tidak ada", "tdk ada", "nihil",
    "tidak ditemukan temuan", "secara keseluruhan semua sudah sesuai",
)

KATEGORI = {
    "Password & BA brankas": r"brankas|pa?s{1,2}word",
    "STB (received / posted)": r"\bstb\b",
    "Nota manual": r"nota manual|kwitansi manual",
    "Kasbon / bon sementara": r"kasbon|bon sementara|\bkb\b",
    "Selisih kas / petty cash": r"selisih|minus|uang pc|petty cash|\bpc\b",
    "DBS / outing": r"\bdbs\b|outing",
    "Omset / BSC / MOP": r"om[sz]et|\bbsc\b|\bmop\b",
    "SR / DP / fulfillment": r"\bsr\b|\bdp\b|ful+fil+ment|ful+fill",
    "Catering / invoice": r"catering|invoice|\binv\b",
    "Kebersihan & kerapian": r"debu|kotor|tidak rapi|berdebu",
    "Kelengkapan TTD / lampiran": r"\bttd\b|tanda tangan|lampiran",
}


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


def count_items(teks: str) -> int:
    """Hitung butir temuan bernomor (1. ... 2. ... 3. ...). Minimal 1."""
    nums = re.findall(r"(?:^|\s)(\d{1,2})\s?[.)]\s?(?=[A-Za-z(])", teks)
    return len(set(int(n) for n in nums)) if nums else 1


def kategori(teks: str) -> list:
    s = teks.lower()
    return [k for k, p in KATEGORI.items() if re.search(p, s)]


def olah(raw: pd.DataFrame) -> pd.DataFrame:
    raw = raw.iloc[:, :6].copy()
    raw.columns = ["TANGGAL", "NAMA_FRA", "NIP", "KODE_STORE", "NAMA_STORE", "TEMUAN"]
    for c in raw.columns:
        raw[c] = raw[c].fillna("").astype(str).str.strip()
    raw = raw[(raw["NAMA_FRA"] != "") | (raw["NAMA_STORE"] != "")].copy()
    raw["NAMA_FRA"] = raw["NAMA_FRA"].str.upper()
    raw["NAMA_STORE"] = raw["NAMA_STORE"].str.upper()
    raw["TEMUAN"] = raw["TEMUAN"].str.replace(r"\s+", " ", regex=True)
    raw["TGL"] = raw["TANGGAL"].apply(parse_tanggal)

    def status(t):
        if t == "":
            return "Belum diisi"
        return "Tidak ada temuan" if is_clean(t) else "Ada temuan"

    raw["STATUS"] = raw["TEMUAN"].apply(status)
    raw["JUMLAH_TEMUAN"] = raw.apply(
        lambda r: count_items(r["TEMUAN"]) if r["STATUS"] == "Ada temuan" else 0,
        axis=1,
    )
    raw["KATEGORI"] = raw.apply(
        lambda r: kategori(r["TEMUAN"]) if r["STATUS"] == "Ada temuan" else [],
        axis=1,
    )
    return raw.reset_index(drop=True)
# --- HELPER END ---


def safe_secret(key, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return default


# ---------------- Login (aktif bila [users] diisi di Secrets) ----------------
def check_login() -> bool:
    users = safe_secret("users")
    if not users:
        return True  # tanpa login
    if st.session_state.get("auth"):
        return True
    st.title("Login")
    nip = st.text_input("NIP")
    pwd = st.text_input("Password", type="password")
    if st.button("Masuk"):
        stored = dict(users).get(nip.strip())
        if stored is not None and hmac.compare_digest(str(stored), pwd):
            st.session_state["auth"] = True
            st.session_state["nip"] = nip.strip()
            st.rerun()
        else:
            st.error("NIP atau password salah.")
    return False


if not check_login():
    st.stop()


# ---------------- Ambil data ----------------
@st.cache_data(ttl=300, show_spinner="Mengambil data dari Google Sheet...")
def load_data(sheet_id: str, sheet_name: str) -> pd.DataFrame:
    url = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
        f"?tqx=out:csv&sheet={quote(sheet_name)}"
    )
    raw = pd.read_csv(url, dtype=str, keep_default_na=False)
    if raw.shape[1] < 6:
        raise ValueError("Sheet harus punya minimal 6 kolom (A sampai F).")
    return olah(raw)


st.title("Dashboard Temuan Visit FRA")

if st.session_state.get("nip"):
    st.sidebar.write(f"Login sebagai: {st.session_state['nip']}")
    if st.sidebar.button("Keluar"):
        st.session_state.clear()
        st.rerun()

if st.sidebar.button("Refresh data"):
    st.cache_data.clear()

try:
    df = load_data(SHEET_ID, SHEET_NAME)
except Exception as e:
    st.error(f"Gagal membaca Google Sheet: {e}")
    st.info(
        "Pastikan Sheet dibagikan dengan akses 'Anyone with the link' (Viewer) "
        "dan nama tab di pengaturan SHEET_NAME sudah benar."
    )
    st.stop()

if df.empty:
    st.warning("Data kosong.")
    st.stop()

# ---------------- Filter ----------------
st.sidebar.header("Filter")
valid = df["TGL"].dropna()
if not valid.empty:
    picked = st.sidebar.date_input(
        "Rentang tanggal visit", (valid.min().date(), valid.max().date())
    )
    if isinstance(picked, (list, tuple)) and len(picked) == 2:
        s, e = picked
        df = df[(df["TGL"].dt.date >= s) & (df["TGL"].dt.date <= e)]

fra_opts = sorted(df["NAMA_FRA"].unique())
fra_pick = st.sidebar.multiselect("Nama FRA", fra_opts, default=fra_opts)
df = df[df["NAMA_FRA"].isin(fra_pick)]

stat_opts = ["Ada temuan", "Tidak ada temuan", "Belum diisi"]
stat_pick = st.sidebar.multiselect("Status", stat_opts, default=stat_opts)
df = df[df["STATUS"].isin(stat_pick)]

kata = st.sidebar.text_input("Cari kata (toko / isi temuan)")
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

# ---------------- KPI ----------------
total_visit = len(df)
ada = int((df["STATUS"] == "Ada temuan").sum())
tanpa = int((df["STATUS"] == "Tidak ada temuan").sum())
terisi = ada + tanpa
total_temuan = int(df["JUMLAH_TEMUAN"].sum())

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total visit", total_visit)
c2.metric("Visit tanpa temuan", tanpa)
c3.metric("% tanpa temuan", f"{(tanpa / terisi * 100):.0f}%" if terisi else "-")
c4.metric("Total butir temuan*", total_temuan)
c5.metric("Rata-rata temuan / visit", f"{(total_temuan / ada):.1f}" if ada else "-")
st.caption(
    "*Jumlah butir temuan dihitung otomatis dari penomoran (1., 2., 3., ...) "
    "pada kolom Temuan Visit, sehingga berupa perkiraan. "
    "Rata-rata dihitung dari visit yang ada temuan."
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Ringkasan", "Per FRA", "Per Store", "Jenis Temuan", "Data"]
)

# ---------------- Tab Ringkasan ----------------
with tab1:
    a, b = st.columns(2)
    harian = (
        df.dropna(subset=["TGL"])
        .groupby([df["TGL"].dt.date.rename("Tanggal"), "STATUS"])
        .size()
        .reset_index(name="Jumlah visit")
    )
    if not harian.empty:
        fig = px.bar(harian, x="Tanggal", y="Jumlah visit", color="STATUS",
                     title="Jumlah visit per hari")
        a.plotly_chart(fig)
    stat_cnt = df["STATUS"].value_counts().reset_index()
    stat_cnt.columns = ["Status", "Jumlah"]
    fig = px.pie(stat_cnt, names="Status", values="Jumlah", title="Komposisi status visit")
    b.plotly_chart(fig)

# ---------------- Tab Per FRA ----------------
with tab2:
    fra = (
        df.groupby("NAMA_FRA")
        .agg(
            NIP=("NIP", "first"),
            VISIT=("NAMA_STORE", "size"),
            STORE=("KODE_STORE", "nunique"),
            TEMUAN=("JUMLAH_TEMUAN", "sum"),
            TANPA_TEMUAN=("STATUS", lambda s: int((s == "Tidak ada temuan").sum())),
        )
        .reset_index()
        .sort_values("TEMUAN", ascending=False)
    )
    fra["RATA2_TEMUAN_PER_VISIT"] = (fra["TEMUAN"] / fra["VISIT"]).round(1)
    fig = px.bar(fra, x="TEMUAN", y="NAMA_FRA", orientation="h",
                 title="Total butir temuan per FRA")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig)
    st.dataframe(fra, hide_index=True)

# ---------------- Tab Per Store ----------------
with tab3:
    store = (
        df.groupby(["KODE_STORE", "NAMA_STORE"])
        .agg(VISIT=("TGL", "size"), TEMUAN=("JUMLAH_TEMUAN", "sum"))
        .reset_index()
        .sort_values("TEMUAN", ascending=False)
    )
    top = store.head(15)
    fig = px.bar(top, x="TEMUAN", y="NAMA_STORE", orientation="h",
                 title="15 store dengan temuan terbanyak")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig)
    st.dataframe(store, hide_index=True)

# ---------------- Tab Jenis Temuan ----------------
with tab4:
    kat = df[df["STATUS"] == "Ada temuan"].explode("KATEGORI").dropna(subset=["KATEGORI"])
    if kat.empty:
        st.info("Belum ada temuan yang terklasifikasi.")
    else:
        kat_cnt = kat["KATEGORI"].value_counts().reset_index()
        kat_cnt.columns = ["Jenis temuan", "Jumlah visit terkait"]
        fig = px.bar(kat_cnt, x="Jumlah visit terkait", y="Jenis temuan",
                     orientation="h", title="Jenis temuan yang paling sering muncul")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig)
        st.caption(
            "Klasifikasi memakai kata kunci, jadi satu visit bisa masuk beberapa jenis. "
            "Daftar kata kunci ada di bagian KATEGORI pada app.py."
        )
        pilih = st.selectbox("Lihat detail jenis temuan", kat_cnt["Jenis temuan"])
        det = kat[kat["KATEGORI"] == pilih][
            ["TANGGAL", "NAMA_FRA", "KODE_STORE", "NAMA_STORE", "TEMUAN"]
        ]
        st.dataframe(det, hide_index=True)

# ---------------- Tab Data ----------------
with tab5:
    tampil = df[["TANGGAL", "NAMA_FRA", "NIP", "KODE_STORE", "NAMA_STORE",
                 "STATUS", "JUMLAH_TEMUAN", "TEMUAN"]]
    st.dataframe(tampil, hide_index=True)
    st.download_button(
        "Unduh CSV",
        tampil.to_csv(index=False).encode("utf-8"),
        file_name="temuan_visit_terfilter.csv",
        mime="text/csv",
    )
    st.subheader("Baca temuan lengkap")
    opsi = (df["KODE_STORE"] + " - " + df["NAMA_STORE"] + " (" + df["TANGGAL"] + ")").tolist()
    sel = st.selectbox("Pilih store / tanggal", opsi)
    baris = df.iloc[opsi.index(sel)]
    st.write(f"**FRA:** {baris['NAMA_FRA']}  |  **Status:** {baris['STATUS']}")
    st.write(baris["TEMUAN"] if baris["TEMUAN"] else "(kosong)")
