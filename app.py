"""
app.py
Aplikasi optimasi penjadwalan kuliah berbasis Algoritma Genetika.
Desain mengacu pada DESIGN.md (WattVision Dark Dashboard System) & antigravity-design-expert.
Kelompok KKA-05.
"""

import os
import random
import time
import pandas as pd
import streamlit as st

from algoritma_ga import analisis_defisit_sumber_daya
from optimasi_multi_seed import buat_jadwal_multi_seed
from kurikulum_data import (
    KURIKULUM_2023,
    DEFAULT_DOSEN_DATA,
    DEFAULT_RUANG_DATA,
    DEFAULT_SLOT_DATA,
    NO_CLASSROOM_NAME_KEYWORDS,
    SKPB_NAME_KEYWORDS,
)

st.set_page_config(
    page_title="Penjadwalan Kuliah - GA KKA-05",
    layout="wide",
    initial_sidebar_state="expanded",
)

def safe_html(html_str: str) -> str:
    """Membersihkan indentasi pada setiap baris agar Markdown tidak menafsirkannya sebagai blok kode <pre><code>."""
    return "\n".join(line.strip() for line in html_str.strip().splitlines())

def render_html(html_str: str, target=None) -> None:
    """Merender HTML secara bersih ke target atau st tanpa jebakan indentasi Markdown."""
    cleaned = safe_html(html_str)
    if target is not None:
        target.markdown(cleaned, unsafe_allow_html=True)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

    /* Global Dark Mode Tokens */
    .stApp {
        background-color: #121212;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }

    /* Container Header */
    .dashboard-header {
        background-color: #1E1E1E;
        border-radius: 16px;
        padding: 22px 26px;
        margin-bottom: 20px;
        border: 1px solid #2C2C2E;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
    }
    .dashboard-header h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 24px;
        color: #FFFFFF;
        margin: 0 0 6px 0;
        letter-spacing: -0.01em;
    }
    .dashboard-header p {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        color: #98989D;
        margin: 0;
    }

    /* Kartu KPI Dashboard */
    .kpi-card {
        background-color: #1E1E1E;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #2C2C2E;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35);
        transition: transform 0.25s ease, border-color 0.25s ease;
    }
    .kpi-card:hover {
        border-color: #3A3A3C;
        transform: translateY(-2px);
    }
    .kpi-card .label {
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 600;
        color: #98989D;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-card .value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 32px;
        font-weight: 700;
        color: #00E5FF;
        margin: 8px 0 4px 0;
        line-height: 1.1;
    }
    .kpi-card .sub {
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        color: #98989D;
    }

    /* Status Badge */
    .status-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }
    .badge-live {
        background-color: #1B3824;
        color: #32D74B;
        border: 1px solid #255832;
    }
    .badge-suboptimal {
        background-color: #3A2F1C;
        color: #FFD60A;
        border: 1px solid #574521;
    }
    .badge-alert {
        background-color: #3A1C1C;
        color: #FF453A;
        border: 1px solid #582424;
    }

    /* Panel Peringatan dan Alert */
    .alert-panel {
        background-color: #3A1C1C;
        color: #FF453A;
        border-left: 4px solid #FF453A;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 8px 0;
        font-size: 13px;
        font-family: 'Inter', sans-serif;
        line-height: 1.4;
    }
    .live-panel {
        background-color: #1B3824;
        color: #32D74B;
        border-left: 4px solid #32D74B;
        border-radius: 8px;
        padding: 14px 18px;
        font-size: 14px;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
    }

    /* Scrollable Conflict Box */
    .conflict-scroll-container {
        max-height: 400px;
        overflow-y: auto;
        padding-right: 6px;
        margin-top: 8px;
    }
    .conflict-scroll-container::-webkit-scrollbar {
        width: 6px;
    }
    .conflict-scroll-container::-webkit-scrollbar-track {
        background: #181818;
        border-radius: 4px;
    }
    .conflict-scroll-container::-webkit-scrollbar-thumb {
        background: #2C2C2E;
        border-radius: 4px;
    }
    .conflict-scroll-container::-webkit-scrollbar-thumb:hover {
        background: #3A3A3C;
    }

    /* Structured Issue Cards */
    .issue-item {
        background-color: #231818;
        border: 1px solid #3A2323;
        border-left: 4px solid #FF453A;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-family: 'Inter', sans-serif;
    }
    .issue-item.soft {
        background-color: #241F15;
        border-color: #4A3A1B;
        border-left-color: #FFD60A;
    }
    .issue-tag {
        display: inline-block;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 2px 6px;
        border-radius: 4px;
        margin-bottom: 4px;
        background-color: #3A1C1C;
        color: #FF453A;
    }
    .issue-item.soft .issue-tag {
        background-color: #3A2F1C;
        color: #FFD60A;
    }
    .issue-text {
        font-size: 12.5px;
        color: #E5E5EA;
        line-height: 1.4;
    }

    /* Diagnostic Deficit Cards */
    .diagnostic-card {
        background-color: #1E1E1E;
        border: 1px solid #2C2C2E;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 10px;
    }
    .diagnostic-card.critical {
        border-left: 4px solid #FF453A;
        background-color: #241616;
    }
    .diagnostic-card.warning {
        border-left: 4px solid #FFD60A;
        background-color: #242015;
    }
    .diagnostic-card.optimal {
        border-left: 4px solid #32D74B;
        background-color: #152419;
    }

    /* Category Summary Metric Badges */
    .category-summary-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        margin: 10px 0 14px 0;
    }
    .category-summary-item {
        background-color: #181818;
        border: 1px solid #2C2C2E;
        border-radius: 8px;
        padding: 8px 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .category-summary-item .cat-name {
        font-size: 11px;
        color: #98989D;
        font-weight: 500;
    }
    .category-summary-item .cat-count {
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        font-weight: 700;
    }

    /* Section Titles */
    .section-title {
        font-family: 'Inter', sans-serif;
        font-size: 18px;
        font-weight: 600;
        color: #FFFFFF;
        border-bottom: 1px solid #2C2C2E;
        padding-bottom: 8px;
        margin: 20px 0 12px 0;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #1E1E1E;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #2C2C2E;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #98989D;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 600;
        padding: 8px 18px;
        background-color: transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2C2C2E !important;
        color: #00E5FF !important;
    }

    /* Button Styling */
    div[data-testid="stButton"] > button {
        background-color: #00E5FF !important;
        color: #121212 !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 15px;
        border-radius: 12px;
        border: none;
        padding: 10px 26px;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        box-shadow: 0 4px 18px rgba(0, 229, 255, 0.28);
    }
    div[data-testid="stButton"] > button p,
    div[data-testid="stButton"] > button span {
        color: #121212 !important;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #33ebff !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 26px rgba(0, 229, 255, 0.45);
    }
    div[data-testid="stButton"] > button:hover p,
    div[data-testid="stButton"] > button:hover span {
        color: #121212 !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"], [data-testid="stSidebar"] > div {
        background-color: #161616 !important;
        border-right: 1px solid #2C2C2E;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #FFFFFF !important;
    }
    /* Pastikan teks tombol di dalam sidebar tetap konsisten dengan warna teks tombol utama (#121212) */
    [data-testid="stSidebar"] div[data-testid="stButton"] > button,
    [data-testid="stSidebar"] div[data-testid="stButton"] > button p,
    [data-testid="stSidebar"] div[data-testid="stButton"] > button span {
        color: #121212 !important;
    }

    /* Dataframe / Table styling */
    [data-testid="stDataFrame"] {
        border: 1px solid #2C2C2E;
        border-radius: 12px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="dashboard-header">
        <h1>Sistem Penjadwalan Perkuliahan</h1>
        <p>Dashboard Optimasi Algoritma Genetika dengan Crossover 3 Parents (Kelompok KKA-05).</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Laporan & Benchmark")
    if st.button("Konsol Telemetri Riset", key="btn_open_web_sidebar", use_container_width=True):
        import os, webbrowser
        dash_path = os.path.abspath("laporan_pengujian/web/index.html")
        webbrowser.open(f"file:///{dash_path.replace(os.sep, '/')}")
        st.toast("Membuka Konsol Telemetri Riset di browser...")
    st.divider()
    st.markdown("### Parameter Algoritma")
    populasi_size = st.slider("Ukuran Populasi", 10, 300, 100, 10)
    generasi = st.slider(
        "Jumlah Generasi",
        min_value=10,
        max_value=2000,
        value=500,
        step=10,
        help="Generasi lebih banyak memberi waktu pencarian lebih panjang, tetapi tidak menjamin hard = 0.",
    )
    mutation_rate = st.slider("Laju Mutasi (Mutation Rate)", 0.0, 1.0, 0.1, 0.01)
    if "random_seed" not in st.session_state:
        st.session_state.random_seed = random.SystemRandom().randrange(0, 2**31)
    random_seed = st.number_input(
        "Seed Reproduksi",
        min_value=0,
        max_value=2**31 - 1,
        step=1,
        key="random_seed",
        help="Dibuat acak sekali saat sesi Streamlit dimulai dan dipakai ulang selama sesi.",
    )
    jumlah_run = st.slider(
        "Jumlah Run Multi-Seed",
        min_value=1,
        max_value=10,
        value=3,
        help="Menjalankan GA yang sama beberapa kali dan memilih hasil hard/soft terbaik.",
    )
    computation_mode = st.selectbox(
        "Mode Komputasi",
        options=["Normal", "Cepat", "Cerdas"],
        index=0,
        help=(
            "Normal memakai satu proses. Cepat memakai maksimal 16 worker. "
            "Cerdas memakai seluruh core yang tersedia dengan menyisakan 2 core."
        ),
    )
    available_cores = getattr(os, "process_cpu_count", os.cpu_count)() or 1
    if computation_mode == "Normal":
        ga_workers = 1
        mode_description = "1 proses CPU"
    elif computation_mode == "Cepat":
        ga_workers = min(16, available_cores)
        mode_description = f"maksimal {ga_workers} worker CPU"
    else:
        ga_workers = max(1, available_cores - 2)
        mode_description = (
            f"{ga_workers} worker CPU, menyisakan "
            f"{max(0, available_cores - ga_workers)} core"
        )
    if computation_mode != "Normal":
        st.info(
            f"Mode {computation_mode.lower()} aktif: {mode_description}. "
            f"Worker mengambil tugas berikutnya segera setelah selesai."
        )
    st.divider()
    st.markdown(
        """
        <div style="font-size: 13px; color: #98989D; line-height: 1.6;">
        <strong style="color: #FFFFFF;">Spesifikasi Mesin GA:</strong><br>
        • Seleksi: Tournament (ukuran 3) + elitisme<br>
        • Crossover: Uni-One-Point (3 Parents)<br>
        • Mutasi: Reshuffle Ruang & Waktu<br>
        • Prioritas seleksi hasil: <span style="color: #FF453A; font-family: monospace;">Hard terendah</span> → Soft terendah → Fitness tertinggi<br>
        • Target: <span style="color: #00E5FF; font-family: monospace;">Hard = 0</span><br>
        • Multi-seed: {jumlah_run} run, memilih hard/soft terendah<br>
        • Mode: {computation_mode} ({mode_description})
        </div>
        """,
        unsafe_allow_html=True,
    )

# Data Dosen Default
DEFAULT_DOSEN = pd.DataFrame(DEFAULT_DOSEN_DATA)

# Data Ruang Kuliah Default (25 Ruangan: SKPB & Departemen Teknik Informatika ITS)
DEFAULT_RUANG = pd.DataFrame(DEFAULT_RUANG_DATA)

# Data Slot Waktu Default (Senin s/d Jumat, 5 Sesi per Hari = 25 Slot Pertemuan)
DEFAULT_SLOT = pd.DataFrame(DEFAULT_SLOT_DATA)

tab_mk, tab_dosen, tab_ruang, tab_slot, tab_report = st.tabs([
    "Mata Kuliah", "Dosen", "Ruang", "Slot Waktu", "Laporan & Riset Benchmark"
])

with tab_mk:
    st.markdown('<div class="section-title">Data Mata Kuliah (Kurikulum 2023 Teknik Informatika)</div>', unsafe_allow_html=True)
    
    col_filter, col_info_kur = st.columns([3, 2])
    with col_filter:
        pilihan_semester = st.selectbox(
            "Pilih Preset Data Semester Kurikulum 2023:",
            [
                "Semester 1 (5 Mata Kuliah)",
                "Semester 2 (6 Mata Kuliah)",
                "Semester 3 (7 Mata Kuliah)",
                "Semester 4 (7 Mata Kuliah)",
                "Semester 5 (20 Mata Kuliah)",
                "Semester 6 (37 Mata Kuliah)",
                "Semester 7 (28 Mata Kuliah)",
                "Semester 8 (Tugas Akhir)",
                "Semester Ganjil (1, 3, 5, 7)",
                "Semester Genap (2, 4, 6, 8)",
                "Semua Semester (110+ Mata Kuliah)",
            ],
            index=0,
            key="pilihan_semester_preset",
        )
    with col_info_kur:
        st.caption("Data kurikulum resmi Program Studi Teknik Informatika Tahun 2023. Anda dapat mengedit, menambah, atau menghapus baris di bawah.")

    # Filter data kurikulum sesuai pilihan
    if "Semester 1 (" in pilihan_semester:
        filtered_kur = [mk for mk in KURIKULUM_2023 if mk["semester"] == 1]
    elif "Semester 2 (" in pilihan_semester:
        filtered_kur = [mk for mk in KURIKULUM_2023 if mk["semester"] == 2]
    elif "Semester 3 (" in pilihan_semester:
        filtered_kur = [mk for mk in KURIKULUM_2023 if mk["semester"] == 3]
    elif "Semester 4 (" in pilihan_semester:
        filtered_kur = [mk for mk in KURIKULUM_2023 if mk["semester"] == 4]
    elif "Semester 5 (" in pilihan_semester:
        filtered_kur = [mk for mk in KURIKULUM_2023 if mk["semester"] == 5]
    elif "Semester 6 (" in pilihan_semester:
        filtered_kur = [mk for mk in KURIKULUM_2023 if mk["semester"] == 6]
    elif "Semester 7 (" in pilihan_semester:
        filtered_kur = [mk for mk in KURIKULUM_2023 if mk["semester"] == 7]
    elif "Semester 8 (" in pilihan_semester:
        filtered_kur = [mk for mk in KURIKULUM_2023 if mk["semester"] == 8]
    elif "Ganjil" in pilihan_semester:
        filtered_kur = [mk for mk in KURIKULUM_2023 if mk["semester"] in [1, 3, 5, 7]]
    elif "Genap" in pilihan_semester:
        filtered_kur = [mk for mk in KURIKULUM_2023 if mk["semester"] in [2, 4, 6, 8]]
    else:
        filtered_kur = list(KURIKULUM_2023)

    df_kur_init = pd.DataFrame(filtered_kur)

    df_mk = st.data_editor(
        df_kur_init,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_mk_{pilihan_semester}",
        column_config={
            "id": st.column_config.TextColumn("Kode MK", width="small"),
            "nama": st.column_config.TextColumn("Nama Mata Kuliah", width="large"),
            "prodi": st.column_config.TextColumn("Program Studi", width="medium"),
            "rmk": st.column_config.TextColumn("RMK / Bidang Minat", width="medium"),
            "semester": st.column_config.NumberColumn("Semester", min_value=1, max_value=8, step=1, width="small"),
            "sks": st.column_config.NumberColumn("SKS", min_value=1, max_value=8, step=1, width="small"),
            "kelas": st.column_config.TextColumn("Kelas", width="small"),
            "dosen": st.column_config.TextColumn("Dosen Pengampu", width="large"),
            "mhs": st.column_config.NumberColumn("Jumlah Mahasiswa", min_value=1, max_value=500, width="small"),
            "lokasi": st.column_config.SelectboxColumn("Lokasi Peruntukan", options=["SKPB", "Departemen"], width="small"),
        },
    )

with tab_dosen:
    st.markdown('<div class="section-title">Data Dosen Pengampu & Preferensi (50 Dosen per RMK)</div>', unsafe_allow_html=True)
    st.caption("Daftar 50 dosen Departemen Teknik Informatika ITS terpetakan ke 8 RMK + Tim Dosen SKPB. pref_slot: indeks baris 0 s/d 24.")
    df_dosen = st.data_editor(
        DEFAULT_DOSEN,
        num_rows="dynamic",
        use_container_width=True,
        key="editor_dosen",
        column_config={
            "nama": st.column_config.TextColumn("Nama Dosen Pengampu", width="large"),
            "email": st.column_config.TextColumn("Email ITS", width="medium"),
            "rmk": st.column_config.TextColumn("RMK / Bidang Minat", width="medium"),
            "role": st.column_config.TextColumn("Jabatan", width="small"),
            "pref_slot": st.column_config.TextColumn("Preferensi Slot Waktu (CSV)", width="medium"),
            "pref_ruang": st.column_config.TextColumn("Preferensi Ruang (CSV)", width="large"),
        },
    )

with tab_ruang:
    st.markdown('<div class="section-title">Data Ruang Kuliah (25 Ruangan: SKPB & Departemen IF)</div>', unsafe_allow_html=True)
    st.caption("Daftar 25 ruang perkuliahan beserta kapasitas kursi dan penempatan gedung (SKPB ITS vs Departemen Teknik Informatika).")
    df_ruang = st.data_editor(
        DEFAULT_RUANG,
        num_rows="dynamic",
        use_container_width=True,
        key="editor_ruang",
        column_config={
            "id": st.column_config.TextColumn("ID Ruang", width="medium"),
            "cap": st.column_config.NumberColumn("Kapasitas Kursi", min_value=1, max_value=1000, width="small"),
            "gedung": st.column_config.TextColumn("Gedung / Lokasi", width="large"),
            "tipe": st.column_config.SelectboxColumn("Kategori Ruang", options=["SKPB", "Departemen"], width="small"),
        },
    )

with tab_slot:
    st.markdown('<div class="section-title">Slot Waktu Pertemuan (25 Sesi: Senin s/d Jumat)</div>', unsafe_allow_html=True)
    st.caption("Jadwal 5 sesi perkuliahan per hari (Sesi 1: 07:00-09:30, Sesi 2: 09:40-12:10, Sesi 3: 12:30-15:00, Sesi 4: 15:30-18:00, Sesi 5: 18:30-21:00).")
    df_slot = st.data_editor(
        DEFAULT_SLOT,
        num_rows="dynamic",
        use_container_width=True,
        key="editor_slot",
        column_config={
            "hari": st.column_config.TextColumn("Hari", width="small"),
            "sesi": st.column_config.TextColumn("Sesi", width="small"),
            "jam_mulai": st.column_config.TextColumn("Jam Mulai", width="small"),
            "jam_selesai": st.column_config.TextColumn("Jam Selesai", width="small"),
        },
    )

with tab_report:
    st.markdown('<div class="section-title">Hasil Riset & Laporan Benchmark Algoritma Genetika</div>', unsafe_allow_html=True)
    st.caption("Hasil pengujian komprehensif parameter GA pada 18 Core, 12 Core, 6 Core, dan Stress Test Beban Berat.")

    col_rep_btn, col_rep_info = st.columns([1, 2])
    with col_rep_btn:
        if st.button("Buka Konsol Telemetri Riset", key="btn_open_web_tab", use_container_width=True):
            import os, webbrowser
            dash_path = os.path.abspath("laporan_pengujian/web/index.html")
            webbrowser.open(f"file:///{dash_path.replace(os.sep, '/')}")
            st.toast("Membuka Konsol Telemetri Riset di browser...")

        st.markdown(
            """
            <div style="margin-top: 10px;">
                <a href="file:///C:/Users/LEGION/Downloads/ETS-KKA/laporan_pengujian/web/index.html" target="_blank" style="text-decoration: none;">
                    <div style="background: rgba(0, 229, 255, 0.08); border: 1px solid #00E5FF; border-radius: 6px; padding: 10px; text-align: center; color: #00E5FF; font-weight: 600; font-size: 12.5px;">
                        Buka Konsol Telemetri di Tab Baru
                    </div>
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_rep_info:
        st.markdown(
            """
            <div style="background: #1E1E1E; border: 1px solid #2C2C2E; border-radius: 12px; padding: 16px 20px; font-size: 13px; color: #E5E5EA; line-height: 1.6;">
                <strong style="color: #00E5FF; font-size: 14px;">Ringkasan Temuan Riset 18 Core:</strong><br>
                • <strong>Rasio Sukses Hard = 0:</strong> 11 dari 18 skenario mencapai <span style="color:#32D74B; font-weight:700;">Hard = 0</span>.<br>
                • <strong>Full Ganjil Realistis (50 MK):</strong> Tembus <span style="color:#32D74B; font-weight:700;">Hard = 0</span> pada Generasi 260 dengan kelas paralel A & B.<br>
                • <strong>Preset Rekomendasi Resmi:</strong> Populasi 100-150, Generasi 500, Mutasi 0.07, Multi-Seed 3 Runs.<br>
                • <strong>Teorema Dirichlet:</strong> Terbukti matematis bahwa rombel > 25 MK wajib dipecah ke rombel paralel agar Hard = 0.
            </div>
            """,
            unsafe_allow_html=True,
        )

def validasi_input(df_mk, df_dosen, df_ruang, df_slot):
    errors = []
    if df_mk.empty:
        errors.append("Tabel mata kuliah belum berisi data.")
    if df_ruang.empty:
        errors.append("Tabel ruang perkuliahan belum berisi data.")
    if df_slot.empty:
        errors.append("Tabel slot waktu belum berisi data.")
    if "mhs" in df_mk.columns and df_mk["mhs"].isnull().any():
        errors.append("Terdapat mata kuliah dengan jumlah mahasiswa kosong.")
    if "cap" in df_ruang.columns and df_ruang["cap"].isnull().any():
        errors.append("Terdapat ruang dengan kapasitas kosong.")
    
    dosen_mk = set(df_mk["dosen"].dropna().unique())
    dosen_data = set(df_dosen["nama"].dropna().unique()) if not df_dosen.empty else set()
    dosen_tidak_ada = dosen_mk - dosen_data
    if dosen_tidak_ada:
        errors.append(
            f"Dosen berikut belum terdaftar pada tab Dosen: {', '.join(dosen_tidak_ada)}. "
            "Sistem akan menggunakan preferensi terbuka secara otomatis."
        )
    return errors

def parse_csv_list(val: str) -> list:
    if pd.isnull(val) or str(val).strip() == "":
        return []
    return [v.strip() for v in str(val).split(",") if v.strip()]

def df_to_mk(df: pd.DataFrame) -> list:
    result = []
    for _, row in df.iterrows():
        cid = str(row.get("id", ""))
        nama = str(row.get("nama", row.get("id", "")))
        nama_lower = nama.lower()
        is_no_classroom = any(
            keyword in nama_lower for keyword in NO_CLASSROOM_NAME_KEYWORDS
        )
        default_lokasi = (
            "SKPB"
            if cid.startswith(("SM", "UG"))
            or any(keyword in nama_lower for keyword in SKPB_NAME_KEYWORDS)
            else "Departemen"
        )
        result.append({
            "id": cid,
            "nama": nama,
            "prodi": str(row.get("prodi", row.get("Program Studi", "Teknik Informatika"))),
            "rmk": str(row.get("rmk", "-")),
            "semester": int(row.get("semester", 1)),
            "sks": int(row.get("sks", 3)) if "sks" in row and not pd.isnull(row["sks"]) else 3,
            "kelas": str(row.get("kelas", "A")),
            "dosen": str(row.get("dosen", "")),
            "mhs": int(row.get("mhs", 0)),
            "lokasi": str(row.get("lokasi", default_lokasi)),
            "requires_room": not is_no_classroom,
        })
    return result

def df_to_dosen(df: pd.DataFrame) -> list:
    result = []
    for _, row in df.iterrows():
        raw_slot = parse_csv_list(row.get("pref_slot", ""))
        pref_slot = []
        for s in raw_slot:
            try:
                pref_slot.append(int(s))
            except ValueError:
                pass
        result.append({
            "nama": str(row.get("nama", "")),
            "email": str(row.get("email", "")),
            "rmk": str(row.get("rmk", "-")),
            "role": str(row.get("role", "")),
            "pref_slot": pref_slot,
            "pref_ruang": parse_csv_list(row.get("pref_ruang", "")),
        })
    return result

def df_to_ruang(df: pd.DataFrame) -> list:
    result = []
    for _, row in df.iterrows():
        rid = str(row.get("id", ""))
        default_tipe = "SKPB" if rid in ["SKPB", "SKPB IUP"] else "Departemen"
        default_gedung = "SKPB (Tower Kuliah Bersama ITS)" if default_tipe == "SKPB" else "Departemen Teknik Informatika"
        result.append({
            "id": rid,
            "cap": int(row.get("cap", 0)),
            "gedung": str(row.get("gedung", default_gedung)),
            "tipe": str(row.get("tipe", default_tipe)),
        })
    return result

def df_to_slot(df: pd.DataFrame) -> list:
    result = []
    for _, row in df.iterrows():
        result.append({
            "hari": str(row.get("hari", "")),
            "sesi": str(row.get("sesi", "")),
            "jam_mulai": str(row.get("jam_mulai", "")),
            "jam_selesai": str(row.get("jam_selesai", "")),
        })
    return result

with st.expander("Audit Kelayakan & Defisit Sumber Daya (Pra-Optimasi)"):
    preview_mk = df_to_mk(df_mk)
    preview_ruang = df_to_ruang(df_ruang)
    preview_dosen = df_to_dosen(df_dosen)
    preview_slot = df_to_slot(df_slot)
    diag_pre = analisis_defisit_sumber_daya(
        preview_mk, preview_ruang, preview_dosen, preview_slot
    )
    col_pre1, col_pre2, col_pre3 = st.columns(3)
    with col_pre1:
        render_html(f"""
        <div class="diagnostic-card">
            <div style="font-size: 11px; text-transform: uppercase; color: #98989D; font-weight: 600;">Utilisasi Ruang Global</div>
            <div style="font-size: 22px; font-family: 'JetBrains Mono', monospace; color: #00E5FF; font-weight: 700; margin: 4px 0;">
                {diag_pre['global']['utilization_rate']}%
            </div>
            <div style="font-size: 11px; color: #98989D;">{diag_pre['global']['total_courses']} kelas / {diag_pre['global']['total_slot_capacity']} total slot</div>
        </div>
        """)
    with col_pre2:
        skpb_c = "#FF453A" if diag_pre['zonasi']['skpb_deficit'] > 0 else "#32D74B"
        render_html(f"""
        <div class="diagnostic-card">
            <div style="font-size: 11px; text-transform: uppercase; color: #98989D; font-weight: 600;">Kebutuhan Ruang SKPB</div>
            <div style="font-size: 22px; font-family: 'JetBrains Mono', monospace; color: {skpb_c}; font-weight: 700; margin: 4px 0;">
                {diag_pre['zonasi']['skpb_demand']} / {diag_pre['zonasi']['skpb_supply']} Slot
            </div>
            <div style="font-size: 11px; color: #98989D;">{diag_pre['zonasi']['skpb_rooms_count']} ruang SKPB ({diag_pre['zonasi']['skpb_util']}%)</div>
        </div>
        """)
    with col_pre3:
        dosen_c = "#FF453A" if diag_pre['dosen']['bottlenecks'] else "#32D74B"
        render_html(f"""
        <div class="diagnostic-card">
            <div style="font-size: 11px; text-transform: uppercase; color: #98989D; font-weight: 600;">Ketersediaan Waktu Dosen</div>
            <div style="font-size: 22px; font-family: 'JetBrains Mono', monospace; color: {dosen_c}; font-weight: 700; margin: 4px 0;">
                {len(diag_pre['dosen']['bottlenecks'])} Defisit Slot
            </div>
            <div style="font-size: 11px; color: #98989D;">{diag_pre['dosen']['total_dosen_active']} dosen pengampu aktif</div>
        </div>
        """)

    with st.container(height=260, border=True):
        for issue in diag_pre["issues"]:
            tingkat = issue.get("tingkat", "INFO")
            t_color = "#FF453A" if tingkat == "KRITIS" else ("#FFD60A" if tingkat == "PERINGATAN" else "#32D74B")
            bg_color = "#241616" if tingkat == "KRITIS" else ("#242015" if tingkat == "PERINGATAN" else "#152419")
            pre_issue_html = (
                f"<div style='background-color: {bg_color}; border: 1px solid #2C2C2E; border-left: 4px solid {t_color}; "
                f"border-radius: 8px; padding: 10px 14px; margin-bottom: 6px; font-family: sans-serif;'>"
                f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;'>"
                f"<strong style='color: {t_color}; font-size: 12px;'>{issue.get('kategori')} ({tingkat})</strong>"
                f"</div>"
                f"<div style='font-size: 12px; color: #FFFFFF; margin-top: 2px;'>{issue.get('pesan')}</div>"
                f"<div style='font-size: 11.5px; color: #98989D; margin-top: 4px;'><strong style='color: #00E5FF;'>Solusi:</strong> {issue.get('solusi')}</div>"
                f"</div>"
            )
            st.markdown(pre_issue_html, unsafe_allow_html=True)

st.divider()
run_btn = st.button("Jalankan Optimasi Jadwal", type="primary")

errors = validasi_input(df_mk, df_dosen, df_ruang, df_slot)

if run_btn:
    non_critical = [e for e in errors if "preferensi terbuka" in e]
    critical = [e for e in errors if "preferensi terbuka" not in e]

    for e in non_critical:
        st.warning(e)
    for e in critical:
        st.error(e)

    if not critical:
        data_mk = df_to_mk(df_mk)
        kelas_tanpa_ruang = [
            course for course in data_mk if not course.get("requires_room", True)
        ]
        data_mk_terjadwal = [
            course for course in data_mk if course.get("requires_room", True)
        ]
        data_dosen_parsed = df_to_dosen(df_dosen)
        data_ruang_parsed = df_to_ruang(df_ruang)
        data_slot_parsed = df_to_slot(df_slot)

        if kelas_tanpa_ruang:
            st.info(
                f"{len(kelas_tanpa_ruang)} mata kuliah tanpa ruangan kelas "
                "dikeluarkan dari optimasi ruang dan waktu kelas."
            )

        st.markdown("---")
        st.markdown('<div class="section-title">Monitor Transparansi Eksekusi Algoritma</div>', unsafe_allow_html=True)

        telemetry_container = st.container()
        with telemetry_container:
            phase_banner = st.empty()
            progress_bar = st.progress(0.0, text="Menginisialisasi mesin genetika...")

            col_t1, col_t2, col_t3, col_t4 = st.columns(4)
            with col_t1:
                metric_gen = st.empty()
            with col_t2:
                metric_eta = st.empty()
            with col_t3:
                metric_speed = st.empty()
            with col_t4:
                metric_fit = st.empty()

            st.caption("Log Transparansi Proses (Alur Kerja Real-Time):")
            log_terminal = st.empty()

        logs_list = []

        def telemetry_callback(data: dict):
            phase = data.get("phase", "Proses Berjalan")
            pct = data.get("progress", 0.0)
            msg = data.get("message", "")
            elapsed = data.get("elapsed", 0.0)
            eta = data.get("eta")
            speed = data.get("speed", 0.0)
            gen = data.get("gen", 0)
            total_gen = data.get("total_gen", generasi)
            fitness = data.get("fitness", 0.0)

            ts_str = f"[{int(elapsed//60):02d}:{elapsed%60:05.2f}]"
            logs_list.append(f"{ts_str} {msg}")

            render_html(
                f"""
                <div style="background-color: #1E1E1E; border: 1px solid #2C2C2E; border-left: 4px solid #00E5FF; border-radius: 8px; padding: 10px 16px; margin-bottom: 8px;">
                    <span style="color: #98989D; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;">Fase Aktif</span><br>
                    <span style="color: #FFFFFF; font-weight: 600; font-size: 14px;">{phase}</span>
                </div>
                """,
                target=phase_banner,
            )

            progress_bar.progress(min(1.0, max(0.0, pct)), text=f"Kemajuan: {int(pct*100)}% ({phase})")

            if eta is None or gen < 2:
                eta_display = "Menghitung..."
            elif eta == 0.0:
                eta_display = "0.0s (Selesai)"
            elif eta < 60:
                eta_display = f"~{eta:.1f} detik"
            else:
                eta_display = f"~{int(eta//60)}m {int(eta%60)}s"

            render_html(
                f"""
                <div class="kpi-card" style="padding: 12px 14px;">
                    <div class="label" style="font-size: 11px;">Generasi</div>
                    <div class="value" style="font-size: 22px; margin: 4px 0;">{gen} <span style="font-size: 13px; color: #98989D;">/ {total_gen}</span></div>
                    <div class="sub" style="font-size: 11px;">Iterasi berjalan</div>
                </div>
                """,
                target=metric_gen,
            )
            render_html(
                f"""
                <div class="kpi-card" style="padding: 12px 14px;">
                    <div class="label" style="font-size: 11px;">Estimasi Selesai (ETA)</div>
                    <div class="value" style="font-size: 22px; color: #32D74B; margin: 4px 0;">{eta_display}</div>
                    <div class="sub" style="font-size: 11px;">Waktu berjalan: {elapsed:.2f}s</div>
                </div>
                """,
                target=metric_eta,
            )
            render_html(
                f"""
                <div class="kpi-card" style="padding: 12px 14px;">
                    <div class="label" style="font-size: 11px;">Kecepatan Komputasi</div>
                    <div class="value" style="font-size: 22px; margin: 4px 0;">{speed:.1f} <span style="font-size: 12px; color: #98989D;">gen/s</span></div>
                    <div class="sub" style="font-size: 11px;">Throughput evolusi</div>
                </div>
                """,
                target=metric_speed,
            )
            render_html(
                f"""
                <div class="kpi-card" style="padding: 12px 14px;">
                    <div class="label" style="font-size: 11px;">Fitness Sementara</div>
                    <div class="value" style="font-size: 22px; color: {'#32D74B' if fitness >= 2.0 else '#00E5FF'}; margin: 4px 0;">{fitness:.4f}</div>
                    <div class="sub" style="font-size: 11px;">Skor individu terbaik</div>
                </div>
                """,
                target=metric_fit,
            )

            terminal_text = "\n".join(logs_list[-7:])
            log_terminal.code(terminal_text, language="bash")

        t0 = time.time()
        seeds = [int(random_seed) + offset for offset in range(jumlah_run)]
        jadwal_terbaik, nilai_fitness, history, seed_pemenang, ringkasan_run = buat_jadwal_multi_seed(
            data_mata_kuliah=data_mk_terjadwal,
            data_dosen=data_dosen_parsed,
            data_ruang=data_ruang_parsed,
            slot_waktu=data_slot_parsed,
            populasi_size=populasi_size,
            generasi=generasi,
            mutation_rate=mutation_rate,
            seeds=seeds,
            callback=telemetry_callback,
            parallel_workers=ga_workers,
        )

        elapsed = time.time() - t0

        st.markdown("---")
        st.markdown("## Hasil Optimasi Penjadwalan")

        if jadwal_terbaik.hard_violations == 0:
            badge_class = "badge-live"
            badge_label = "Solusi Feasible (Hard = 0)"
        elif nilai_fitness >= 1.0:
            badge_class = "badge-live"
            badge_label = "Solusi Terbaik yang Ditemukan"
        elif nilai_fitness >= 0.5:
            badge_class = "badge-suboptimal"
            badge_label = "Solusi Suboptimal (Terdapat Konflik)"
        else:
            badge_class = "badge-alert"
            badge_label = "Solusi Belum Konvergen"

        st.caption(
            f"Run pemenang: seed {seed_pemenang}. "
            f"Seleksi hasil memprioritaskan hard violation, lalu soft violation, lalu fitness."
        )

        # Baris Kartu KPI Dashboard (sesuai layout DESIGN.md 3-4 kolom atas)
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        with col_kpi1:
            render_html(f"""
            <div class="kpi-card">
                <div class="label">Nilai Fitness</div>
                <div class="value">{nilai_fitness:.4f}</div>
                <div class="sub">Maksimum: 2.0000</div>
            </div>
            """)
        with col_kpi2:
            hard_color = "#32D74B" if jadwal_terbaik.hard_violations == 0 else "#FF453A"
            render_html(f"""
            <div class="kpi-card">
                <div class="label">Pelanggaran Keras (Hard)</div>
                <div class="value" style="color: {hard_color};">{jadwal_terbaik.hard_violations}</div>
                <div class="sub">Ruang, Dosen, atau Kapasitas</div>
            </div>
            """)
        with col_kpi3:
            soft_color = "#32D74B" if jadwal_terbaik.soft_violations == 0 else "#FFD60A"
            render_html(f"""
            <div class="kpi-card">
                <div class="label">Pelanggaran Lunak (Soft)</div>
                <div class="value" style="color: {soft_color};">{jadwal_terbaik.soft_violations}</div>
                <div class="sub">Preferensi Dosen</div>
            </div>
            """)
        with col_kpi4:
            render_html(f"""
            <div class="kpi-card">
                <div class="label">Generasi Berjalan</div>
                <div class="value">{len(history)}</div>
                <div class="sub">Iterasi Selesai</div>
            </div>
            """)

        render_html(f'<div style="margin: 14px 0;"><span class="status-badge {badge_class}">{badge_label}</span></div>')

        # Layout Dashboard: 8 Kolom Utama (Tabel & Grafik) + 4 Kolom Samping (Panel Alertas)
        col_main, col_side = st.columns([8, 4])

        with col_main:
            if kelas_tanpa_ruang:
                st.markdown(
                    '<div class="section-title">Mata Kuliah Tanpa Ruangan Kelas</div>',
                    unsafe_allow_html=True,
                )
                st.caption(
                    "Mata kuliah ini tetap tercatat dalam kurikulum, tetapi tidak "
                    "dimasukkan ke alokasi ruang kelas."
                )
                st.dataframe(
                    pd.DataFrame([
                        {
                            "Kode MK": course["id"],
                            "Mata Kuliah": course["nama"],
                            "Semester": course["semester"],
                            "Dosen": course["dosen"],
                            "Status": "Tidak memerlukan ruang kelas",
                        }
                        for course in kelas_tanpa_ruang
                    ]),
                    use_container_width=True,
                    hide_index=True,
                )

            st.markdown('<div class="section-title">Tabel Alokasi Jadwal Kuliah</div>', unsafe_allow_html=True)
            tabel = jadwal_terbaik.get_schedule_table()
            df_hasil = pd.DataFrame(tabel)

            drop_cols = [c for c in ["Slot Waktu"] if c in df_hasil.columns]
            df_display = df_hasil.drop(columns=drop_cols, errors="ignore")

            def highlight_overcapacity(row):
                if row["Jumlah Mahasiswa"] > row["Kapasitas Ruang"]:
                    return ["background-color: #3A1C1C; color: #FF453A"] * len(row)
                return [""] * len(row)

            styled_table = df_display.style.apply(highlight_overcapacity, axis=1)
            st.dataframe(
                styled_table,
                use_container_width=True,
                height=420,
                column_config={
                    "Kode MK": st.column_config.TextColumn("Kode", width="small"),
                    "Mata Kuliah": st.column_config.TextColumn("Mata Kuliah", width="medium"),
                    "Program Studi": st.column_config.TextColumn("Program Studi", width="small"),
                    "RMK": st.column_config.TextColumn("RMK / Bidang Minat", width="medium"),
                    "Semester": st.column_config.NumberColumn("Sem", width="small"),
                    "SKS": st.column_config.NumberColumn("SKS", width="small"),
                    "Kelas": st.column_config.TextColumn("Kls", width="small"),
                    "Dosen": st.column_config.TextColumn("Dosen Pengampu", width="large"),
                    "Ruang": st.column_config.TextColumn("Ruang", width="medium"),
                    "Lokasi Gedung": st.column_config.TextColumn("Lokasi Gedung", width="large"),
                    "Kapasitas Ruang": st.column_config.NumberColumn("Kapasitas", width="small"),
                    "Jumlah Mahasiswa": st.column_config.NumberColumn("Mhs", width="small"),
                    "Hari": st.column_config.TextColumn("Hari", width="small"),
                    "Sesi": st.column_config.TextColumn("Sesi", width="small"),
                    "Jam": st.column_config.TextColumn("Jam Perkuliahan", width="medium"),
                },
            )

            csv_data = df_display.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Unduh Berkas Jadwal (.csv)",
                csv_data,
                file_name="jadwal_kuliah_optimal.csv",
                mime="text/csv",
            )

            if history:
                st.markdown('<div class="section-title">Konvergensi Nilai Fitness</div>', unsafe_allow_html=True)
                df_hist = pd.DataFrame(history).set_index("generasi")
                st.caption("Peningkatan Fitness per Generasi")
                st.line_chart(df_hist["fitness_terbaik"], height=220)

        with col_side:
            st.markdown('<div class="section-title">Panel Status & Peringatan</div>', unsafe_allow_html=True)

            conflict_summary = jadwal_terbaik.get_conflict_summary()
            counts = conflict_summary["counts"]
            detailed_conflicts = conflict_summary["detailed"]
            total_hard = conflict_summary["total_hard"]
            total_soft = conflict_summary["total_soft"]
            total_all = conflict_summary["total_all"]

            diag = analisis_defisit_sumber_daya(
                data_mata_kuliah=data_mk_terjadwal,
                data_ruang=data_ruang_parsed,
                data_dosen=data_dosen_parsed,
                slot_waktu=data_slot_parsed,
            )

            # 1. Status Ringkasan Eksekutif
            if total_hard == 0 and total_soft == 0:
                render_html('<div class="live-panel">Semua kelas teralokasi sempurna tanpa bentrok ruang, dosen, rombel prodi, atau kelebihan kapasitas kursi.</div>')
            else:
                status_color = "#FF453A" if total_hard > 0 else "#FFD60A"
                render_html(f"""
                <div style="background-color: #1E1E1E; border: 1px solid #2C2C2E; border-left: 4px solid {status_color}; border-radius: 8px; padding: 10px 14px; margin-bottom: 10px;">
                    <span style="font-size: 11px; text-transform: uppercase; color: #98989D; letter-spacing: 0.05em; font-weight: 600;">Status Evaluasi Solusi</span><br>
                    <span style="font-size: 13.5px; font-weight: 600; color: #FFFFFF;">
                        Terdeteksi <span style="color: #FF453A; font-family: 'JetBrains Mono', monospace;">{total_hard}</span> Pelanggaran Keras & <span style="color: #FFD60A; font-family: 'JetBrains Mono', monospace;">{total_soft}</span> Lunak
                    </span>
                </div>
                """)

            # 2. Ringkasan Kategori Masalah (Summary Badges Grid)
            render_html(f"""
            <div class="category-summary-grid">
                <div class="category-summary-item">
                    <span class="cat-name">Kapasitas Kursi</span>
                    <span class="cat-count" style="color: {'#FF453A' if counts['Kapasitas Terlampaui'] > 0 else '#32D74B'};">{counts['Kapasitas Terlampaui']}</span>
                </div>
                <div class="category-summary-item">
                    <span class="cat-name">Bentrok Ruang</span>
                    <span class="cat-count" style="color: {'#FF453A' if counts['Bentrok Ruang & Waktu'] > 0 else '#32D74B'};">{counts['Bentrok Ruang & Waktu']}</span>
                </div>
                <div class="category-summary-item">
                    <span class="cat-name">Bentrok Dosen</span>
                    <span class="cat-count" style="color: {'#FF453A' if counts['Bentrok Dosen Mengajar'] > 0 else '#32D74B'};">{counts['Bentrok Dosen Mengajar']}</span>
                </div>
                <div class="category-summary-item">
                    <span class="cat-name">Bentrok Rombel</span>
                    <span class="cat-count" style="color: {'#FF453A' if counts['Bentrok Rombel Mahasiswa'] > 0 else '#32D74B'};">{counts['Bentrok Rombel Mahasiswa']}</span>
                </div>
                <div class="category-summary-item">
                    <span class="cat-name">Alokasi Gedung</span>
                    <span class="cat-count" style="color: {'#FF453A' if counts['Alokasi Gedung Tidak Sesuai'] > 0 else '#32D74B'};">{counts['Alokasi Gedung Tidak Sesuai']}</span>
                </div>
                <div class="category-summary-item">
                    <span class="cat-name">Preferensi Dosen</span>
                    <span class="cat-count" style="color: {'#FFD60A' if counts['Preferensi Dosen'] > 0 else '#32D74B'};">{counts['Preferensi Dosen']}</span>
                </div>
            </div>
            """)

            # 3. Tab Interaktif Dalam Panel Samping
            side_tab_conflict, side_tab_diag, side_tab_trend = st.tabs([
                f"Konflik ({total_all})", "Audit Sumber Daya", "Tren Evolusi"
            ])

            with side_tab_conflict:
                if not detailed_conflicts:
                    st.caption("Tidak ada konflik atau pelanggaran jadwal terdeteksi.")
                else:
                    kategori_options = ["Semua Kategori"] + list(counts.keys())
                    selected_cat = st.selectbox(
                        "Filter Kategori Masalah:",
                        kategori_options,
                        key="filter_kategori_side",
                    )

                    filtered_list = detailed_conflicts
                    if selected_cat != "Semua Kategori":
                        filtered_list = [c for c in detailed_conflicts if c.get("kategori") == selected_cat]

                    st.caption(f"Menampilkan {len(filtered_list)} dari {len(detailed_conflicts)} isu:")

                    with st.container(height=380, border=True):
                        for c in filtered_list:
                            is_soft = c.get("jenis") == "soft"
                            border_col = "#FFD60A" if is_soft else "#FF453A"
                            bg_col = "#241F15" if is_soft else "#231818"
                            tag_bg = "#3A2F1C" if is_soft else "#3A1C1C"
                            tag_col = "#FFD60A" if is_soft else "#FF453A"
                            tag_cat = c.get("kategori", "Isu")
                            msg = c.get("pesan", "")
                            entitas = c.get("entitas", "")
                            badge_ent = f" &bull; <span style='color: #98989D; font-size: 11px;'>{entitas}</span>" if entitas else ""

                            card_html = (
                                f"<div style='background-color: {bg_col}; border: 1px solid #3A2323; border-left: 4px solid {border_col}; "
                                f"border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; font-family: sans-serif;'>"
                                f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;'>"
                                f"<div><span style='font-size: 10px; font-weight: 700; text-transform: uppercase; background-color: {tag_bg}; "
                                f"color: {tag_col}; padding: 2px 6px; border-radius: 4px;'>{tag_cat}</span>{badge_ent}</div>"
                                f"</div>"
                                f"<div style='font-size: 12.5px; color: #E5E5EA; line-height: 1.4;'>{msg}</div>"
                                f"</div>"
                            )
                            st.markdown(card_html, unsafe_allow_html=True)

            with side_tab_diag:
                st.caption("Riset mendalam utilisasi dan defisit sumber daya:")

                # Metrik Supply vs Demand Ruang
                render_html(f"""
                <div class="diagnostic-card">
                    <div style="font-size: 11px; text-transform: uppercase; color: #98989D; font-weight: 600;">Keseimbangan Ruang Kuliah</div>
                    <div style="display: flex; justify-content: space-between; margin-top: 6px; font-size: 12.5px;">
                        <span>Utilisasi Slot Global:</span>
                        <strong style="font-family: 'JetBrains Mono', monospace; color: {'#FF453A' if diag['global']['utilization_rate'] > 85 else '#00E5FF'};">{diag['global']['utilization_rate']}%</strong>
                    </div>
                    <div style="font-size: 11.5px; color: #98989D; margin-top: 2px;">
                        {diag['global']['total_courses']} kelas memperebutkan {diag['global']['total_slot_capacity']} slot ({diag['global']['total_rooms']} ruang x {diag['global']['total_slots']} sesi).
                    </div>
                    <hr style="border: none; border-top: 1px solid #2C2C2E; margin: 8px 0;">
                    <div style="font-size: 12px; display: flex; justify-content: space-between;">
                        <span>Slot SKPB ({diag['zonasi']['skpb_rooms_count']} ruang):</span>
                        <span style="font-family: 'JetBrains Mono', monospace; color: {'#FF453A' if diag['zonasi']['skpb_deficit'] > 0 else '#32D74B'};">
                            {diag['zonasi']['skpb_demand']}/{diag['zonasi']['skpb_supply']} ({diag['zonasi']['skpb_util']}%)
                        </span>
                    </div>
                    <div style="font-size: 12px; display: flex; justify-content: space-between; margin-top: 4px;">
                        <span>Slot Dept IF ({diag['zonasi']['dept_rooms_count']} ruang):</span>
                        <span style="font-family: 'JetBrains Mono', monospace; color: {'#FF453A' if diag['zonasi']['dept_deficit'] > 0 else '#32D74B'};">
                            {diag['zonasi']['dept_demand']}/{diag['zonasi']['dept_supply']} ({diag['zonasi']['dept_util']}%)
                        </span>
                    </div>
                </div>
                """)

                # Analisis Kapasitas Kursi Besar
                render_html(f"""
                <div class="diagnostic-card">
                    <div style="font-size: 11px; text-transform: uppercase; color: #98989D; font-weight: 600;">Kapasitas Ruang & Kursi Besar</div>
                    <div style="font-size: 12px; display: flex; justify-content: space-between; margin-top: 6px;">
                        <span>Kelas Besar (>= {diag['kapasitas']['large_threshold']} mhs):</span>
                        <strong style="font-family: 'JetBrains Mono', monospace; color: {'#FF453A' if diag['kapasitas']['large_deficit'] > 0 else '#00E5FF'};">
                            {diag['kapasitas']['large_demand']} kelas
                        </strong>
                    </div>
                    <div style="font-size: 12px; display: flex; justify-content: space-between; margin-top: 4px;">
                        <span>Kapasitas Ruang Besar (>= {diag['kapasitas']['large_threshold']} kursi):</span>
                        <strong style="font-family: 'JetBrains Mono', monospace;">
                            {diag['kapasitas']['large_rooms_count']} ruang ({diag['kapasitas']['large_supply']} slot)
                        </strong>
                    </div>
                    <div style="font-size: 11.5px; color: #98989D; margin-top: 4px;">
                        Kursi fisik terbesar: {diag['global']['max_room_cap']} kursi. Ruang lab/kecil (<= 25 kursi): {diag['kapasitas']['small_rooms_count']} ruang.
                    </div>
                </div>
                """)

                # Beban Dosen & Keterbatasan Waktu
                render_html(f"""
                <div class="diagnostic-card">
                    <div style="font-size: 11px; text-transform: uppercase; color: #98989D; font-weight: 600;">Beban & Ketersediaan Dosen</div>
                    <div style="font-size: 12px; margin-top: 6px;">
                        <span>Dosen Aktif Mengajar: <strong>{diag['dosen']['total_dosen_active']} dosen</strong></span>
                    </div>
                    <div style="font-size: 12px; margin-top: 4px;">
                        <span>Defisit Slot Preferensi: <strong style="color: {'#FF453A' if diag['dosen']['bottlenecks'] else '#32D74B'};">{len(diag['dosen']['bottlenecks'])} dosen</strong></span>
                    </div>
                </div>
                """)

                # Isu Defisit & Rekomendasi Solusi Teknis
                st.markdown("<div style='font-size: 12px; font-weight: 600; color: #FFFFFF; margin: 10px 0 6px 0;'>Daftar Temuan Defisit & Solusi:</div>", unsafe_allow_html=True)
                with st.container(height=380, border=True):
                    for issue in diag["issues"]:
                        tingkat = issue.get("tingkat", "INFO")
                        t_color = "#FF453A" if tingkat == "KRITIS" else ("#FFD60A" if tingkat == "PERINGATAN" else "#32D74B")
                        bg_color = "#241616" if tingkat == "KRITIS" else ("#242015" if tingkat == "PERINGATAN" else "#152419")
                        issue_card_html = (
                            f"<div style='background-color: {bg_color}; border: 1px solid #2C2C2E; border-left: 4px solid {t_color}; "
                            f"border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; font-family: sans-serif;'>"
                            f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;'>"
                            f"<span style='font-size: 10px; font-weight: 700; text-transform: uppercase; color: {t_color};'>{issue.get('kategori')}</span>"
                            f"<span style='font-size: 10px; font-weight: 700; color: {t_color}; background-color: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px;'>{tingkat}</span>"
                            f"</div>"
                            f"<div style='font-size: 12px; color: #FFFFFF; line-height: 1.4; margin-bottom: 6px;'>{issue.get('pesan')}</div>"
                            f"<div style='font-size: 11.5px; color: #98989D; background-color: rgba(0,0,0,0.3); padding: 6px 8px; border-radius: 4px; line-height: 1.35;'>"
                            f"<strong style='color: #00E5FF;'>Solusi:</strong> {issue.get('solusi')}</div>"
                            f"</div>"
                        )
                        st.markdown(issue_card_html, unsafe_allow_html=True)

            with side_tab_trend:
                if history:
                    df_hist = pd.DataFrame(history).set_index("generasi")
                    st.caption("Trend Penurunan Pelanggaran per Generasi:")
                    st.line_chart(df_hist[["hard_violations", "soft_violations"]], height=240)

        with st.expander("Detail Representasi Kromosom"):
            st.code(
                f"Kromosom Solusi Terbaik : {jadwal_terbaik.genes}\n"
                f"Jumlah Gen             : {len(jadwal_terbaik.genes)}\n"
                f"Ruang Tersedia         : {len(jadwal_terbaik.rooms)}\n"
                f"Slot Waktu Tersedia    : {jadwal_terbaik.num_timeslots}\n"
                f"Evaluasi Fitness       : {nilai_fitness:.6f}",
                language="text",
            )

st.markdown("---")
st.markdown(
    "<div style='font-size: 12px; color: #98989D; text-align: center;'>Sistem Penjadwalan Perkuliahan | KKA Kelompok 05</div>",
    unsafe_allow_html=True,
)
