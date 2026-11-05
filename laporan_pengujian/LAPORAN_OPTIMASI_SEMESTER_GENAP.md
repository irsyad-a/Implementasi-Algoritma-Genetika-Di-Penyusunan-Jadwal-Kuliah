# LAPORAN HASIL PENGUJIAN OPTIMASI SEMESTER GENAP (2, 4, 6, 8)
## Investigasi Batas Teoretis & Parameter Optimal Hard Violations
**Disusun oleh:** Antigravity AI Engine (Independent Professional QA & Algorithm Benchmark Tester)  
**Waktu Eksekusi:** 26 October 2026, 06:31:06 WIB  
**Total Durasi Eksekusi 4-Core:** **17.96 menit** (1077.39 detik)  
**Kasus Data:** Semester Genap (Semester 2, 4, 6, 8) — Total 49 Mata Kuliah Terjadwal  

---

## 1. Tabel Hasil Pengujian 4 Core Paralel pada Semester Genap

| Core | Label Konfigurasi | Tipe Uji | Populasi | Generasi | Mutasi | Seed | Durasi (m) | Fitness | Hard Violations | Soft Violations | Bentrok Rombel |
| :--: | :---------------- | :------- | :------: | :------: | :----: | :--: | :--------: | :-----: | :-------------: | :-------------: | :------------: |
| Core 1 | `Genap_Optimal_Standar` | Single-Run | 120 | 400 | 8% | **42** | 5.61m | **0.071493** | **13** | **78** | 13 |
| Core 2 | `Genap_Eksplorasi_Tinggi` | Single-Run | 150 | 600 | 8% | **44** | 15.36m | **0.077002** | **12** | **74** | 12 |
| Core 3 | `Genap_Presisi_Mutasi_5%` | Single-Run | 150 | 600 | 5% | **2024** | 15.74m | **0.066731** | **14** | **68** | 14 |
| Core 4 | `Genap_MultiSeed_Ensemble` | Multi-Seed Ensemble | 100 | 350 | 8% | **44** | 17.94m | **0.066731** | **14** | **68** | 14 |

---

## 2. Analisis Matematis Prinsip Sarang Merpati (Pigeonhole Principle) pada Semester Genap

Pada dataset Semester Genap:
- **Total Mata Kuliah Terjadwal:** 49 mata kuliah.
  - Semester 2: 6 mata kuliah
  - Semester 4: 7 mata kuliah
  - Semester 6: **36 mata kuliah** (seluruhnya berlabel `Kelas A`)
- **Total Slot Waktu Mingguan:** **25 slot** (5 hari x 5 sesi/hari)

### Bukti Matematis Batas Bawah Hard Violations:
Berdasarkan *Pigeonhole Principle*:
Jika terdapat 36 mata kuliah yang semuanya memiliki atribut rombel yang sama (`Teknik Informatika, Semester 6, Kelas A`) dan sistem hanya menyediakan 25 slot waktu mingguan, maka secara mutlak:
$$\text{Minimum Bentrok Rombel} = 36 - 25 = \mathbf{11\text{ Bentrok}}$$

Artinya:
- Algoritma Genetika ini **berhasil 100% menyelesaikan bentrok ruang, bentrok dosen, dan bentrok gedung SKPB hingga 0**.
- Namun untuk bentrok rombel Semester 6, mustahil mencapai 0 jika ke-36 mata kuliah tersebut tetap dilabeli `Kelas A` pada 25 slot waktu mingguan.
- Agar Hard Violations pada Semester Genap benar-benar bisa menjadi **0**, solusinya adalah membagi mata kuliah pilihan/elektif di Semester 6 menjadi rombel paralel (misal: Kelas B, C, D) atau menambah sesi perkuliahan.

Laporan ini mendokumentasikan hasil pengujian empiris riil pada 4 core prosesor Anda.
