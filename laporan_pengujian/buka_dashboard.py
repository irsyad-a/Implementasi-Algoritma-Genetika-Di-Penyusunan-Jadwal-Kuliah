"""
buka_dashboard.py
Skrip praktis untuk membuka Web Dashboard Laporan Benchmark GA langsung di browser default Anda.
"""

import os
import webbrowser

WEB_INDEX = os.path.abspath(os.path.join(os.path.dirname(__file__), "web", "index.html"))

if os.path.exists(WEB_INDEX):
    print(f"Membuka Web Dashboard di browser...")
    print(f"Lokasi File: {WEB_INDEX}")
    webbrowser.open(f"file:///{WEB_INDEX.replace(os.sep, '/')}")
    print("Dashboard berhasil dibuka!")
else:
    print(f"File index.html tidak ditemukan di: {WEB_INDEX}")
