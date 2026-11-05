"""
run_suite_pengujian.py
Skrip pengujian otomatis komprehensif untuk Algoritma Genetika Penjadwalan Kuliah (ETS-KKA).
Kasus Uji: Preset Semester Ganjil (1, 3, 5, 7).
Pengujian mencakup:
1. Ukuran Populasi (Population Size)
2. Jumlah Generasi (Generations)
3. Laju Mutasi (Mutation Rate)
4. Seed Reproduksi (Random Seed Sensitivity)
5. Jumlah Run Multi-Seed (Multi-Start Runs)
6. Preset Penggunaan (Fast, Balanced, High-Quality)

Seluruh eksekusi tidak memodifikasi modul inti algoritma_ga.py maupun optimasi_multi_seed.py.
"""

import csv
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List

# Tambahkan direktori root ke path agar dapat mengimpor modul tanpa mengubah kode asli
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import kurikulum_data as kd
from algoritma_ga import buat_jadwal
from optimasi_multi_seed import buat_jadwal_multi_seed


def get_preset_ganjil_data():
    """Mengambil data preset semester ganjil (1, 3, 5, 7) persis seperti di app.py."""
    courses = [mk for mk in kd.KURIKULUM_2023 if mk["semester"] in [1, 3, 5, 7]]
    no_room = [
        c for c in courses
        if any(k in c["nama"].lower() for k in kd.NO_CLASSROOM_NAME_KEYWORDS)
    ]
    req_room = [c for c in courses if c not in no_room]

    dosen_parsed = []
    for d in kd.DEFAULT_DOSEN_DATA:
        raw_s = d.get("pref_slot", "")
        slots = [int(s.strip()) for s in str(raw_s).split(",") if s.strip().isdigit()]
        raw_r = d.get("pref_ruang", "")
        ruangs = [r.strip() for r in str(raw_r).split(",") if r.strip()]
        dosen_parsed.append({
            "nama": d["nama"],
            "email": d.get("email", ""),
            "rmk": d.get("rmk", ""),
            "role": d.get("role", ""),
            "pref_slot": slots,
            "pref_ruang": ruangs,
        })

    ruang_parsed = [
        {
            "id": r["id"],
            "cap": r["cap"],
            "gedung": r.get("gedung", ""),
            "tipe": r.get("tipe", "SKPB" if r["id"] in ["SKPB", "SKPB IUP"] else "Departemen"),
        }
        for r in kd.DEFAULT_RUANG_DATA
    ]

    slot_parsed = [
        {
            "hari": s["hari"],
            "sesi": s["sesi"],
            "jam_mulai": s["jam_mulai"],
            "jam_selesai": s["jam_selesai"],
        }
        for s in kd.DEFAULT_SLOT_DATA
    ]

    return req_room, dosen_parsed, ruang_parsed, slot_parsed


def _run_single_experiment(params: Dict[str, Any]) -> Dict[str, Any]:
    """Helper worker untuk eksekusi satu konfigurasi GA."""
    req_room, dosen_parsed, ruang_parsed, slot_parsed = get_preset_ganjil_data()

    pop_size = params["populasi_size"]
    generasi = params["generasi"]
    mut_rate = params["mutation_rate"]
    seed = params["seed"]
    kategori_eks = params.get("kategori", "Umum")
    label_uji = params.get("label", f"pop{pop_size}_gen{generasi}_mut{mut_rate}_seed{seed}")

    t0 = time.time()
    schedule, fitness, history = buat_jadwal(
        data_mata_kuliah=req_room,
        data_dosen=dosen_parsed,
        data_ruang=ruang_parsed,
        slot_waktu=slot_parsed,
        populasi_size=pop_size,
        generasi=generasi,
        mutation_rate=mut_rate,
        random_seed=seed,
    )
    t1 = time.time()
    elapsed = t1 - t0

    summary = schedule.get_conflict_summary()
    counts = summary["counts"]

    # Ekstraksi konvergensi fitness
    fit_initial = history[0]["fitness_terbaik"] if history else fitness
    fit_final = fitness
    gen_actual = len(history)
    speed = gen_actual / elapsed if elapsed > 0 else 0.0

    return {
        "kategori": kategori_eks,
        "label": label_uji,
        "populasi_size": pop_size,
        "generasi_target": generasi,
        "generasi_aktual": gen_actual,
        "mutation_rate": mut_rate,
        "seed": seed,
        "fitness_awal": round(fit_initial, 6),
        "fitness_akhir": round(fit_final, 6),
        "hard_violations": schedule.hard_violations,
        "soft_violations": schedule.soft_violations,
        "kapasitas_terlampaui": counts.get("Kapasitas Terlampaui", 0),
        "bentrok_ruang_waktu": counts.get("Bentrok Ruang & Waktu", 0),
        "bentrok_dosen": counts.get("Bentrok Dosen Mengajar", 0),
        "bentrok_rombel": counts.get("Bentrok Rombel Mahasiswa", 0),
        "alokasi_gedung_salah": counts.get("Alokasi Gedung Tidak Sesuai", 0),
        "pelanggaran_pref_dosen": counts.get("Preferensi Dosen", 0),
        "waktu_detik": round(elapsed, 3),
        "kecepatan_gen_per_detik": round(speed, 2),
        "is_feasible": schedule.hard_violations == 0,
        "history_fit": [h["fitness_terbaik"] for h in history[:: max(1, len(history) // 10)]],
    }


def _run_multiseed_experiment(params: Dict[str, Any]) -> Dict[str, Any]:
    """Helper worker untuk eksekusi multi-seed."""
    req_room, dosen_parsed, ruang_parsed, slot_parsed = get_preset_ganjil_data()

    pop_size = params["populasi_size"]
    generasi = params["generasi"]
    mut_rate = params["mutation_rate"]
    base_seed = params["base_seed"]
    jumlah_run = params["jumlah_run"]
    kategori_eks = "Multi-Seed Runs"
    label_uji = f"multiseed_runs_{jumlah_run}"

    seeds = [int(base_seed) + offset for offset in range(jumlah_run)]

    t0 = time.time()
    best_schedule, best_fitness, best_history, winning_seed, run_summaries = buat_jadwal_multi_seed(
        data_mata_kuliah=req_room,
        data_dosen=dosen_parsed,
        data_ruang=ruang_parsed,
        slot_waktu=slot_parsed,
        populasi_size=pop_size,
        generasi=generasi,
        mutation_rate=mut_rate,
        seeds=seeds,
    )
    t1 = time.time()
    elapsed = t1 - t0

    summary = best_schedule.get_conflict_summary()
    counts = summary["counts"]

    return {
        "kategori": kategori_eks,
        "label": label_uji,
        "populasi_size": pop_size,
        "generasi_target": generasi,
        "generasi_aktual": len(best_history),
        "mutation_rate": mut_rate,
        "base_seed": base_seed,
        "jumlah_run": jumlah_run,
        "winning_seed": winning_seed,
        "fitness_akhir": round(best_fitness, 6),
        "hard_violations": best_schedule.hard_violations,
        "soft_violations": best_schedule.soft_violations,
        "kapasitas_terlampaui": counts.get("Kapasitas Terlampaui", 0),
        "bentrok_ruang_waktu": counts.get("Bentrok Ruang & Waktu", 0),
        "bentrok_dosen": counts.get("Bentrok Dosen Mengajar", 0),
        "bentrok_rombel": counts.get("Bentrok Rombel Mahasiswa", 0),
        "alokasi_gedung_salah": counts.get("Alokasi Gedung Tidak Sesuai", 0),
        "pelanggaran_pref_dosen": counts.get("Preferensi Dosen", 0),
        "waktu_detik": round(elapsed, 3),
        "is_feasible": best_schedule.hard_violations == 0,
        "run_summaries": run_summaries,
    }


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(out_dir, "hasil_pengujian_parameter.csv")
    json_file = os.path.join(out_dir, "data_pengujian_lengkap.json")

    print("=================================================================")
    print("  MEMULAI SUITE PENGUJIAN KOMPREHENSIF ALGORITMA GENETIKA (GA)  ")
    print("  KASUS: PRESET SEMESTER GANJIL (1, 3, 5, 7) - 50 MATA KULIAH    ")
    print("=================================================================\n")

    single_tasks = []

    # 1. KATEGORI: Ukuran Populasi (Population Size)
    # Baseline: gen=250, mut=0.10, seed=42
    pop_sizes = [15, 30, 50, 80, 100, 150, 200, 300]
    for p in pop_sizes:
        single_tasks.append({
            "kategori": "1. Ukuran Populasi",
            "label": f"Populasi_{p}",
            "populasi_size": p,
            "generasi": 250,
            "mutation_rate": 0.10,
            "seed": 42,
        })

    # 2. KATEGORI: Jumlah Generasi (Generations)
    # Baseline: pop=100, mut=0.10, seed=42
    gens = [50, 100, 200, 350, 500, 750, 1000]
    for g in gens:
        single_tasks.append({
            "kategori": "2. Jumlah Generasi",
            "label": f"Generasi_{g}",
            "populasi_size": 100,
            "generasi": g,
            "mutation_rate": 0.10,
            "seed": 42,
        })

    # 3. KATEGORI: Laju Mutasi (Mutation Rate)
    # Baseline: pop=100, gen=250, seed=42
    mut_rates = [0.01, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30, 0.50]
    for m in mut_rates:
        single_tasks.append({
            "kategori": "3. Laju Mutasi",
            "label": f"Mutasi_{int(m*100)}persen",
            "populasi_size": 100,
            "generasi": 250,
            "mutation_rate": m,
            "seed": 42,
        })

    # 4. KATEGORI: Seed Reproduksi (Random Seed Sensitivity)
    # Baseline: pop=100, gen=250, mut=0.10
    seeds = [1, 7, 13, 21, 42, 77, 100, 313, 777, 1024, 2024, 9999]
    for s in seeds:
        single_tasks.append({
            "kategori": "4. Seed Reproduksi",
            "label": f"Seed_{s}",
            "populasi_size": 100,
            "generasi": 250,
            "mutation_rate": 0.10,
            "seed": s,
        })

    # 5. KATEGORI: Profil Penggunaan Nyata (Presets)
    presets = [
        {"kategori": "6. Profil Preset", "label": "Preset_Ultra_Fast", "populasi_size": 30, "generasi": 50, "mutation_rate": 0.10, "seed": 42},
        {"kategori": "6. Profil Preset", "label": "Preset_Interactive", "populasi_size": 50, "generasi": 150, "mutation_rate": 0.10, "seed": 42},
        {"kategori": "6. Profil Preset", "label": "Preset_Balanced", "populasi_size": 100, "generasi": 300, "mutation_rate": 0.08, "seed": 42},
        {"kategori": "6. Profil Preset", "label": "Preset_Deep_Search", "populasi_size": 150, "generasi": 600, "mutation_rate": 0.08, "seed": 42},
    ]
    single_tasks.extend(presets)

    print(f"Total pengujian single-run yang disiapkan: {len(single_tasks)} konfigurasi.")
    print("Mengeksekusi secara paralel menggunakan ProcessPoolExecutor (10 worker)...")

    single_results = []
    t_start_all = time.time()

    with ProcessPoolExecutor(max_workers=10) as executor:
        future_to_task = {executor.submit(_run_single_experiment, t): t for t in single_tasks}
        completed_count = 0
        for future in as_completed(future_to_task):
            completed_count += 1
            res = future.result()
            single_results.append(res)
            print(f"[{completed_count:02d}/{len(single_tasks)}] Selesai: {res['kategori']} -> {res['label']} "
                  f"(Fit: {res['fitness_akhir']:.4f}, Hard: {res['hard_violations']}, Soft: {res['soft_violations']}, Waktu: {res['waktu_detik']}s)")

    # 6. KATEGORI: Multi-Seed Runs
    print("\n--- Mengeksekusi Pengujian Kategori 5: Multi-Seed Runs ---")
    multiseed_tasks = [
        {"populasi_size": 80, "generasi": 200, "mutation_rate": 0.08, "base_seed": 42, "jumlah_run": 1},
        {"populasi_size": 80, "generasi": 200, "mutation_rate": 0.08, "base_seed": 42, "jumlah_run": 2},
        {"populasi_size": 80, "generasi": 200, "mutation_rate": 0.08, "base_seed": 42, "jumlah_run": 3},
        {"populasi_size": 80, "generasi": 200, "mutation_rate": 0.08, "base_seed": 42, "jumlah_run": 5},
        {"populasi_size": 80, "generasi": 200, "mutation_rate": 0.08, "base_seed": 42, "jumlah_run": 7},
        {"populasi_size": 80, "generasi": 200, "mutation_rate": 0.08, "base_seed": 42, "jumlah_run": 10},
    ]

    multiseed_results = []
    with ProcessPoolExecutor(max_workers=6) as executor:
        future_to_ms = {executor.submit(_run_multiseed_experiment, ms): ms for ms in multiseed_tasks}
        completed_ms = 0
        for future in as_completed(future_to_ms):
            completed_ms += 1
            res = future.result()
            multiseed_results.append(res)
            print(f"[MS {completed_ms:02d}/{len(multiseed_tasks)}] Selesai: Runs={res['jumlah_run']} -> Best Seed={res['winning_seed']} "
                  f"(Fit: {res['fitness_akhir']:.4f}, Hard: {res['hard_violations']}, Soft: {res['soft_violations']}, Total Waktu: {res['waktu_detik']}s)")

    t_total = time.time() - t_start_all
    print(f"\nSeluruh pengujian selesai dalam {t_total:.2f} detik ({t_total/60:.2f} menit).")

    # Simpan hasil ke file CSV
    single_results.sort(key=lambda x: (x["kategori"], x["label"]))
    fieldnames = [
        "kategori", "label", "populasi_size", "generasi_target", "generasi_aktual",
        "mutation_rate", "seed", "fitness_awal", "fitness_akhir",
        "hard_violations", "soft_violations", "kapasitas_terlampaui",
        "bentrok_ruang_waktu", "bentrok_dosen", "bentrok_rombel",
        "alokasi_gedung_salah", "pelanggaran_pref_dosen", "waktu_detik",
        "kecepatan_gen_per_detik", "is_feasible"
    ]

    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in single_results:
            row_dict = {k: r[k] for k in fieldnames}
            writer.writerow(row_dict)

    print(f"Data pengujian berhasil diekspor ke: {csv_file}")

    # Simpan data lengkap ke file JSON
    full_data = {
        "metadata": {
            "judul": "Hasil Pengujian Parameter Algoritma Genetika Penjadwalan Kuliah",
            "kasus": "Preset Data Semester Ganjil (1, 3, 5, 7)",
            "jumlah_mata_kuliah": 50,
            "jumlah_ruang": 28,
            "jumlah_slot_waktu": 25,
            "tanggal_pengujian": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_durasi_pengujian_detik": round(t_total, 2),
            "total_uji_single": len(single_results),
            "total_uji_multiseed": len(multiseed_results),
        },
        "single_experiments": single_results,
        "multiseed_experiments": multiseed_results,
    }

    with open(json_file, mode="w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=2)

    print(f"Data lengkap dan telemetri JSON berhasil disimpan ke: {json_file}")


if __name__ == "__main__":
    main()
