# Aplikasi Penjadwalan Kuliah: Streamlit & Algoritma Genetika
Evaluasi Tengah Semester (ETS) Komputasi Kognitif dan Aplikasinya (Kelompok KKA-05)

Aplikasi berbasis web untuk optimasi penyusunan jadwal perkuliahan menggunakan Algoritma Genetika dengan operator Uni-One-Point Crossover (3 Parents), seleksi tournament, telemetri transparansi eksekusi real-time, dan penanganan kendala alokasi gedung SKPB vs Departemen Teknik Informatika ITS.

## Struktur Berkas

| Berkas | Deskripsi |
|---|---|
| `algoritma_ga.py` | Modul inti algoritma genetika dengan fungsi utama `buat_jadwal(...)`, telemetri callback, dan kendala alokasi ruang. |
| `optimasi_multi_seed.py` | Orkestrasi eksternal multi-start yang menjalankan GA inti beberapa kali dengan seed berbeda dan memilih hasil terbaik. |
| `kurikulum_data.py` | Dataset Kurikulum 2023 Teknik Informatika, 25 ruang kuliah riil (Departemen IF & SKPB), dan 25 sesi waktu (Senin s/d Jumat). |
| `app.py` | Dashboard Streamlit dengan antarmuka gelap profesional (`DESIGN.md`), monitor transparansi, dan tabel jadwal. |
| `run_app.bat` | Skrip eksekusi otomatis untuk lingkungan Windows. |
| `requirements.txt` | Dependensi pustaka (`streamlit`, `pandas`). |
| `DESIGN.md` | Panduan token desain antarmuka (Dark mode `#121212`, kartu `#1E1E1E`, font JetBrains Mono). |

## Ruang Perkuliahan & Sesi Waktu

- **Ruang Perkuliahan (28 Ruangan pada dataset):**
  - **SKPB ITS (Perkuliahan Bersama Umum):** `SKPB`, `SKPB IUP`
    serta `SKPB-101`, `SKPB-102`, dan `SKPB-103` (masing-masing 60 kursi).
  - **Departemen Teknik Informatika ITS:** `Aula Prof. Handayani (IF-219)`, `IF-101`, `IF-102`, `IF-103`, `IF-104`, `IF-105`, `IF-106`, `IF-107a&b`, `IF-108`, `Ruang TIF-109A`, `Ruang TIF-109B`, `Ruang TIF-109C / Ruang Residensi S3`, `IF-110 (LAB PASCASARJANA)`, `IF-111`, `IF-112`, `IF-113 / Ruang PIKTI`, `LP-1 (IF 305)`, `RBTC (IF-114)`, `Lab. KBJ`, `LP-2 (IF-309)`, `Ruang TIF-306`, `Ruang TIF-309A`, `Lab. NETICS`.
- **Sesi Pertemuan (25 Slot Waktu: Senin s/d Jumat):**
  - Sesi 1: 07:00 - 09:30
  - Sesi 2: 09:40 - 12:10
  - Sesi 3: 12:30 - 15:00
  - Sesi 4: 15:30 - 18:00
  - Sesi 5: 18:30 - 21:00

## 8 Rumpun Mata Kuliah (RMK) Departemen Teknik Informatika ITS

Sistem menggunakan data dosen dan mata kuliah resmi yang terbagi ke dalam 8 RMK:
1. **Algoritma Pemrograman (AP):** Diketuai Dr. Ir. Dwi Sunaryono, S.Kom., M.Kom. (Dasar Pemrograman, Struktur Data, PBO, Pemrograman Web, PAA, PBKK, Mobile, dll.)
2. **Grafika, Interaksi, Gim dan Analitika (GIGa):** Diketuai Wijayanti Nurul Khotimah, S.Kom., M.Sc., Ph.D. (Grafika Komputer, Gim, IMK, Animasi 3D, UX, dll.)
3. **Teknologi Jaringan dan Keamanan Siber Cerdas (NETICS):** Diketuai Royyana Muslim Ijtihadie, S.Kom., M.Kom., Ph.D. (Sistem Digital, Jarkom, Keamanan Jaringan, IoT, dll.)
4. **Komputasi Cerdas Visi (KCV):** Diketuai Prof. Dr. Eng. Nanik Suciati, S.Kom., M.Kom. (Kecerdasan Artifisial, Machine Learning, Computer Vision, Deep Learning, Robotika, dll.)
5. **Komputasi Berbasis Jaringan (KBJ / NCC):** Diketuai Prof. Ir. Tohari Ahmad, S.Kom., M.IT., Ph.D. (Sistem Operasi, Sistem Terdistribusi, Cloud Computing, Forensik Digital, dll.)
6. **Rekayasa Perangkat Lunak (RPL):** Diketuai Dr. Sarwosri, S.Kom., MT. (RPL, MPPL, Rekayasa Kebutuhan, Konstruksi PL, Arsitektur PL, dll.)
7. **Pemodelan dan Komputasi Terapan (PKT):** Diketuai Dr. Ir. Bilqis Amaliah, S.Kom., M.Kom. (Aljabar Linier, Komputasi Numerik, Matdis, Teori Graf, Riset Operasi, Simulasi, dll.)
8. **Manajemen Cerdas Informasi (MCI):** Diketuai Ir. Ratih Nur Esti Anggraini, S.Kom., M.Sc., Ph.D. (Sistem Basis Data, Big Data, Knowledge Based System, Enterprise Systems, dll.)

## Cara Menjalankan Aplikasi

### Metode 1: Menggunakan Berkas Batch
Jalankan berkas berikut melalui klik ganda:
```
run_app.bat
```

### Metode 2: Menggunakan Terminal
1. Buka terminal pada direktori proyek:
   ```powershell
   cd c:\Users\LEGION\Downloads\ETS-KKA
   ```
2. Jalankan aplikasi Streamlit:
   ```powershell
   & "C:\Users\LEGION\AppData\Local\Programs\Python\Python313\python.exe" -m streamlit run app.py
   ```
3. Buka peramban pada alamat lokal yang ditampilkan (`http://localhost:8501`).

## Antarmuka Fungsi Utama `buat_jadwal`

```python
def buat_jadwal(
    data_mata_kuliah, 
    data_dosen, 
    data_ruang, 
    slot_waktu, 
    populasi_size=50, 
    generasi=100, 
    mutation_rate=0.1,
    callback=None,
    random_seed=None
):
    return jadwal_terbaik, nilai_fitness, history
```

`random_seed` dapat diisi dengan angka tetap, misalnya `42`, agar hasil demo dapat direproduksi pada mesin yang sama. Kosongkan nilainya untuk eksperimen acak.

## Spesifikasi Evaluasi

- **Hard Constraints (Pelanggaran Keras):**
  - **Alokasi Ruang SKPB vs Departemen:** Kalkulus 1 & 2, Agama, Bahasa, Kewirausahaan, Kewarganegaraan, Etika Profesi, dan Pancasila wajib bertempat di ruang `SKPB` atau `SKPB IUP`. Sebaliknya, mata kuliah spesifik Informatika bertempat di ruang/lab Departemen Teknik Informatika.
  - **Bebas Bentrok Ruang & Waktu:** Satu ruang hanya dapat digunakan oleh satu kelas pada slot waktu yang sama.
  - **Bebas Bentrok Dosen:** Seorang dosen hanya dapat mengajar satu kelas pada slot waktu yang sama.
  - **Kapasitas Kursi:** Jumlah mahasiswa tidak boleh melebihi kapasitas ruang.
  - **Bebas Bentrok Rombel Mahasiswa:** Mahasiswa pada Program Studi, Semester, dan Kelas yang sama tidak boleh memiliki jadwal bersamaan.

- **Mata Kuliah Tanpa Ruang Kelas:**
  - Tugas Akhir, Proposal Tugas Akhir, Magang, Topik Khusus, dan Kerja Praktik tidak dimasukkan ke optimasi ruang dan slot kelas.
  - Mata kuliah tersebut tetap ditampilkan sebagai data kurikulum dengan status `Tidak memerlukan ruang kelas`.

- **Operator Evolusi:**
  - **Tournament Selection:** Tiga parent dipilih melalui turnamen acak berukuran tiga, dengan individu ber-fitness tertinggi dari setiap turnamen menjadi parent.
  - **Uni-One-Point Crossover:** Parent 1 dan Parent 2 terlebih dahulu menghasilkan kromosom perantara melalui uniform crossover. Kromosom perantara tersebut lalu dipotong pada satu titik acak dan digabungkan dengan bagian akhir Parent 3.
  - **Mutasi Feasible:** Saat mutasi, ruang dipilih dari zona yang benar dan diutamakan yang kapasitasnya mencukupi jumlah mahasiswa.

- **Soft Constraints (Pelanggaran Lunak):**
  - Kesesuaian preferensi slot waktu mengajar dosen.
  - Kesesuaian preferensi lokasi ruang kuliah dosen.

## Orkestrasi Multi-Seed

`optimasi_multi_seed.py` tidak mengubah populasi, seleksi, crossover, mutasi, atau fitness pada GA inti. Modul ini hanya menjalankan `buat_jadwal(...)` beberapa kali dengan seed berbeda, lalu memilih hasil dengan prioritas:

1. jumlah hard violation paling rendah;
2. jumlah soft violation paling rendah;
3. fitness paling tinggi.

Fitur ini meningkatkan peluang menemukan jadwal feasible tanpa mengubah database atau mekanisme inti algoritma. Hasil tetap harus dilaporkan sebagai “solusi terbaik yang ditemukan”, bukan bukti optimal global.

Pada dashboard, hasil multi-seed selalu diprioritaskan dengan urutan `hard violations` terendah, kemudian `soft violations` terendah, dan terakhir fitness tertinggi. Jumlah generasi dapat dinaikkan hingga 2.000 untuk memperpanjang pencarian, tetapi generasi tambahan tidak menjamin `hard = 0`.
