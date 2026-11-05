"""
algoritma_ga.py
Modul algoritma genetika untuk optimasi penjadwalan kuliah.
Diadaptasi dari python_solusi_KKA_05.py dengan dukungan data dinamis,
penanganan kendala SKPB vs Departemen Teknik Informatika, dan telemetri transparansi.
"""

import copy
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from typing import Any, Callable, Dict, List, Optional, Tuple

SKPB_NAME_KEYWORDS = (
    "kalkulus", "agama", "bahasa", "kewirausahaan",
    "kewarganegaraan", "etika profesi", "pancasila",
)


def is_skpb_course(course: Dict) -> bool:
    course_id = str(course.get("id", "")).upper()
    name = str(course.get("nama", "")).lower()
    return (
        course_id.startswith(("SM", "UG"))
        or str(course.get("lokasi", "")).upper() == "SKPB"
        or any(keyword in name for keyword in SKPB_NAME_KEYWORDS)
    )

def encode_gene(room_idx: int, time_idx: int, num_timeslots: int) -> int:
    return (room_idx * num_timeslots) + time_idx

def decode_gene(merge_index: int, num_timeslots: int) -> Tuple[int, int]:
    return merge_index // num_timeslots, merge_index % num_timeslots

class Schedule:
    def __init__(
        self,
        courses: List[Dict],
        rooms: List[Dict],
        num_timeslots: int,
        lecturer_prefs: Dict,
        randomize: bool = True,
    ):
        self.courses = courses
        self.rooms = rooms
        self.num_timeslots = num_timeslots
        self.lecturer_prefs = lecturer_prefs
        self.genes: List[int] = []
        self.fitness: float = 0.0
        self.hard_violations: int = 0
        self.soft_violations: int = 0

        if randomize:
            skpb_indices = [
                idx for idx, r in enumerate(rooms)
                if r["id"] in ["SKPB", "SKPB IUP"] or r.get("tipe") == "SKPB"
            ]
            dept_indices = [idx for idx, r in enumerate(rooms) if idx not in skpb_indices]

            for c in courses:
                cid = c.get("id", "")
                is_skpb = is_skpb_course(c)
                allowed_rooms = skpb_indices if is_skpb else dept_indices
                capacity_rooms = [
                    idx for idx in allowed_rooms if rooms[idx]["cap"] >= c["mhs"]
                ]
                candidates = capacity_rooms or allowed_rooms
                if candidates:
                    r = random.choice(candidates)
                else:
                    r = random.randint(0, len(rooms) - 1)
                t = random.randint(0, num_timeslots - 1)
                self.genes.append(encode_gene(r, t, num_timeslots))

    def _decode_all(self) -> List[Dict]:
        decoded = []
        for i, gene in enumerate(self.genes):
            r_idx, t_idx = decode_gene(gene, self.num_timeslots)
            decoded.append({
                "course_idx": i,
                "course": self.courses[i],
                "r_idx": r_idx,
                "t_idx": t_idx,
                "room": self.rooms[r_idx],
            })
        return decoded

    def calculate_fitness(self) -> None:
        m, c = 0, 0
        decoded = self._decode_all()

        for i in range(len(decoded)):
            ci = decoded[i]["course"]
            ri = decoded[i]["room"]

            # Validasi kapasitas ruang
            if ci["mhs"] > ri["cap"]:
                m += 1

            # Validasi peruntukan ruang (SKPB vs Departemen)
            cid_i = ci.get("id", "")
            is_skpb_mk = is_skpb_course(ci)
            is_skpb_ruang = ri["id"] in ["SKPB", "SKPB IUP"] or ri.get("tipe") == "SKPB"
            if is_skpb_mk and not is_skpb_ruang:
                m += 1  # Hard constraint: MK Dasar Sains / MKU wajib di ruang SKPB
            elif not is_skpb_mk and is_skpb_ruang:
                m += 1  # Hard constraint: MK Departemen IF tidak boleh menggunakan ruang SKPB

            for j in range(i + 1, len(decoded)):
                cj = decoded[j]["course"]

                # Konflik ruang pada slot waktu yang sama
                if (decoded[i]["r_idx"] == decoded[j]["r_idx"]
                        and decoded[i]["t_idx"] == decoded[j]["t_idx"]):
                    m += 1

                # Konflik dosen mengajar lebih dari satu kelas pada slot waktu yang sama
                if (ci["dosen"] == cj["dosen"]
                        and decoded[i]["t_idx"] == decoded[j]["t_idx"]):
                    m += 1

                # Konflik mahasiswa (program studi, semester, dan kelas yang sama pada slot waktu yang sama)
                prodi_i = ci.get("prodi", ci.get("departemen"))
                prodi_j = cj.get("prodi", cj.get("departemen"))
                if (prodi_i and prodi_j
                        and prodi_i == prodi_j
                        and ci.get("semester") == cj.get("semester")
                        and ci.get("kelas") == cj.get("kelas")
                        and decoded[i]["t_idx"] == decoded[j]["t_idx"]):
                    m += 1

        # Evaluasi preferensi dosen (soft constraint)
        for item in decoded:
            dosen = item["course"]["dosen"]
            if dosen in self.lecturer_prefs:
                pref = self.lecturer_prefs[dosen]
                if item["t_idx"] not in pref.get("pref_time_idx", []):
                    c += 1
                if item["room"]["id"] not in pref.get("pref_room_id", []):
                    c += 1

        self.hard_violations = m
        self.soft_violations = c
        denom = m + (c / (c + 1.0))
        self.fitness = 2.0 if denom == 0 else 1.0 / denom

    def get_schedule_table(self) -> List[Dict]:
        decoded = self._decode_all()
        rows = []
        for item in decoded:
            course = item["course"]
            room = item["room"]
            t_idx = item["t_idx"]
            default_gedung = (
                "SKPB (Perkuliahan Bersama)"
                if room["id"] in ["SKPB", "SKPB IUP"] or room.get("tipe") == "SKPB"
                else "Departemen Teknik Informatika"
            )
            rows.append({
                "Kode MK": course.get("id", "-"),
                "Mata Kuliah": course.get("nama", course.get("id", "-")),
                "Program Studi": course.get("prodi", course.get("departemen", "Teknik Informatika")),
                "RMK": course.get("rmk", "-"),
                "Semester": course.get("semester", "-"),
                "SKS": course.get("sks", "-"),
                "Kelas": course.get("kelas", "-"),
                "Dosen": course.get("dosen", "-"),
                "Ruang": room["id"],
                "Lokasi Gedung": room.get("gedung", default_gedung),
                "Kapasitas Ruang": room["cap"],
                "Jumlah Mahasiswa": course.get("mhs", "-"),
                "Slot Waktu": t_idx,
                "Hari": course.get("_slot_hari", "-"),
                "Sesi": course.get("_slot_sesi", f"Sesi {(t_idx % 5) + 1}"),
                "Jam": course.get("_slot_jam", "-"),
            })
        return rows

    def get_detailed_conflicts(self) -> List[Dict[str, Any]]:
        detailed = []
        decoded = self._decode_all()

        for i in range(len(decoded)):
            ci = decoded[i]["course"]
            ri = decoded[i]["room"]
            cid_i = ci.get("id", "")
            nama_i = ci.get("nama", cid_i)
            t_idx_i = decoded[i]["t_idx"]

            # 1. Validasi Kapasitas Ruang
            if ci["mhs"] > ri["cap"]:
                detailed.append({
                    "kategori": "Kapasitas Terlampaui",
                    "jenis": "hard",
                    "kode_mk": cid_i,
                    "nama_mk": nama_i,
                    "ruang": ri["id"],
                    "kapasitas": ri["cap"],
                    "peserta": ci["mhs"],
                    "slot": t_idx_i,
                    "entitas": f"{ri['id']} ({ri['cap']} kursi)",
                    "pesan": (
                        f"Kapasitas terlampaui: {cid_i} - {nama_i} ({ci['mhs']} mhs) "
                        f"melebihi kapasitas {ri['id']} ({ri['cap']} kursi)."
                    ),
                })

            # 2. Validasi Peruntukan Gedung (SKPB vs Departemen)
            is_skpb_mk = is_skpb_course(ci)
            is_skpb_ruang = ri["id"] in ["SKPB", "SKPB IUP"] or ri.get("tipe") == "SKPB"
            if is_skpb_mk and not is_skpb_ruang:
                detailed.append({
                    "kategori": "Alokasi Gedung Tidak Sesuai",
                    "jenis": "hard",
                    "kode_mk": cid_i,
                    "nama_mk": nama_i,
                    "ruang": ri["id"],
                    "kapasitas": ri["cap"],
                    "peserta": ci["mhs"],
                    "slot": t_idx_i,
                    "entitas": f"{ri['id']} (Departemen IF)",
                    "pesan": (
                        f"Alokasi Ruang Tidak Sesuai: MK Umum/Sains {cid_i} ({nama_i}) "
                        f"ditempatkan di {ri['id']}. Wajib diselenggarakan di SKPB / SKPB IUP."
                    ),
                })
            elif not is_skpb_mk and is_skpb_ruang:
                detailed.append({
                    "kategori": "Alokasi Gedung Tidak Sesuai",
                    "jenis": "hard",
                    "kode_mk": cid_i,
                    "nama_mk": nama_i,
                    "ruang": ri["id"],
                    "kapasitas": ri["cap"],
                    "peserta": ci["mhs"],
                    "slot": t_idx_i,
                    "entitas": f"{ri['id']} (SKPB)",
                    "pesan": (
                        f"Alokasi Ruang Tidak Sesuai: MK Departemen {cid_i} ({nama_i}) "
                        f"ditempatkan di {ri['id']} (SKPB adalah ruang bersama di luar Departemen IF)."
                    ),
                })

            # 3. Validasi Antar-Mata Kuliah (Ruang, Dosen, Rombel Mahasiswa)
            for j in range(i + 1, len(decoded)):
                cj = decoded[j]["course"]
                cid_j = cj.get("id", "")
                nama_j = cj.get("nama", cid_j)
                t_idx_j = decoded[j]["t_idx"]

                # Konflik Ruang dan Waktu
                if (decoded[i]["r_idx"] == decoded[j]["r_idx"] and t_idx_i == t_idx_j):
                    detailed.append({
                        "kategori": "Bentrok Ruang & Waktu",
                        "jenis": "hard",
                        "kode_mk": f"{cid_i} & {cid_j}",
                        "nama_mk": f"{nama_i} & {nama_j}",
                        "ruang": ri["id"],
                        "kapasitas": ri["cap"],
                        "peserta": ci["mhs"] + cj["mhs"],
                        "slot": t_idx_i,
                        "entitas": ri["id"],
                        "pesan": (
                            f"Bentrok Ruang & Waktu: {cid_i} ({nama_i}) dan {cid_j} ({nama_j}) "
                            f"dijadwalkan di ruang {ri['id']} pada Slot {t_idx_i}."
                        ),
                    })

                # Konflik Dosen
                if (ci["dosen"] == cj["dosen"] and t_idx_i == t_idx_j):
                    detailed.append({
                        "kategori": "Bentrok Dosen Mengajar",
                        "jenis": "hard",
                        "kode_mk": f"{cid_i} & {cid_j}",
                        "nama_mk": f"{nama_i} & {nama_j}",
                        "ruang": f"{ri['id']}, {decoded[j]['room']['id']}",
                        "kapasitas": ri["cap"],
                        "peserta": ci["mhs"],
                        "slot": t_idx_i,
                        "entitas": ci["dosen"],
                        "pesan": (
                            f"Bentrok Dosen Mengajar: {ci['dosen']} mengajar {cid_i} ({nama_i}) "
                            f"dan {cid_j} ({nama_j}) pada slot waktu bersamaan (Slot {t_idx_i})."
                        ),
                    })

                # Konflik Rombel Mahasiswa
                prodi_i = ci.get("prodi", ci.get("departemen"))
                prodi_j = cj.get("prodi", cj.get("departemen"))
                if (prodi_i and prodi_j
                        and prodi_i == prodi_j
                        and ci.get("semester") == cj.get("semester")
                        and ci.get("kelas") == cj.get("kelas")
                        and t_idx_i == t_idx_j):
                    detailed.append({
                        "kategori": "Bentrok Rombel Mahasiswa",
                        "jenis": "hard",
                        "kode_mk": f"{cid_i} & {cid_j}",
                        "nama_mk": f"{nama_i} & {nama_j}",
                        "ruang": f"{ri['id']}, {decoded[j]['room']['id']}",
                        "kapasitas": ri["cap"],
                        "peserta": ci["mhs"],
                        "slot": t_idx_i,
                        "entitas": f"{prodi_i} Sem {ci.get('semester')} Kls {ci.get('kelas')}",
                        "pesan": (
                            f"Bentrok Rombel Mahasiswa: {cid_i} ({nama_i}) dan {cid_j} ({nama_j}) "
                            f"({prodi_i} Sem {ci.get('semester')} Kelas {ci.get('kelas')}) "
                            f"berada pada slot waktu yang sama (Slot {t_idx_i})."
                        ),
                    })

        # 4. Evaluasi Preferensi Dosen (Soft Violations)
        for item in decoded:
            dosen = item["course"]["dosen"]
            cid = item["course"].get("id", "")
            nama = item["course"].get("nama", cid)
            if dosen in self.lecturer_prefs:
                pref = self.lecturer_prefs[dosen]
                pref_slots = pref.get("pref_time_idx", [])
                if pref_slots and item["t_idx"] not in pref_slots:
                    detailed.append({
                        "kategori": "Preferensi Dosen",
                        "jenis": "soft",
                        "kode_mk": cid,
                        "nama_mk": nama,
                        "ruang": item["room"]["id"],
                        "kapasitas": item["room"]["cap"],
                        "peserta": item["course"]["mhs"],
                        "slot": item["t_idx"],
                        "entitas": dosen,
                        "pesan": (
                            f"Preferensi Waktu Dosen: {dosen} dialokasikan pada Slot {item['t_idx']} "
                            f"di luar daftar slot waktu preferensinya untuk MK {cid} ({nama})."
                        ),
                    })
                pref_rooms = pref.get("pref_room_id", [])
                if pref_rooms and item["room"]["id"] not in pref_rooms:
                    detailed.append({
                        "kategori": "Preferensi Dosen",
                        "jenis": "soft",
                        "kode_mk": cid,
                        "nama_mk": nama,
                        "ruang": item["room"]["id"],
                        "kapasitas": item["room"]["cap"],
                        "peserta": item["course"]["mhs"],
                        "slot": item["t_idx"],
                        "entitas": dosen,
                        "pesan": (
                            f"Preferensi Ruang Dosen: {dosen} dialokasikan di ruang {item['room']['id']} "
                            f"di luar daftar ruang preferensinya untuk MK {cid} ({nama})."
                        ),
                    })

        return detailed

    def get_conflict_summary(self) -> Dict[str, Any]:
        detailed = self.get_detailed_conflicts()
        categories = {
            "Kapasitas Terlampaui": 0,
            "Bentrok Ruang & Waktu": 0,
            "Bentrok Dosen Mengajar": 0,
            "Bentrok Rombel Mahasiswa": 0,
            "Alokasi Gedung Tidak Sesuai": 0,
            "Preferensi Dosen": 0,
        }
        for item in detailed:
            cat = item.get("kategori", "Lainnya")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "counts": categories,
            "total_hard": self.hard_violations,
            "total_soft": self.soft_violations,
            "total_all": len(detailed),
            "detailed": detailed,
        }

    def get_conflicts(self) -> List[str]:
        detailed = self.get_detailed_conflicts()
        return [item["pesan"] for item in detailed]

def crossover_3_parents(p1: Schedule, p2: Schedule, p3: Schedule) -> Schedule:
    """Apply Uniform(p1, p2), then One-Point(intermediate, p3)."""
    n = len(p1.genes)
    if not (len(p2.genes) == n and len(p3.genes) == n):
        raise ValueError("Semua parent harus memiliki panjang kromosom yang sama.")

    intermediate = [
        p1.genes[i] if random.random() < 0.5 else p2.genes[i]
        for i in range(n)
    ]
    cut = random.randint(1, n - 1) if n > 1 else n

    child = Schedule(
        courses=p1.courses,
        rooms=p1.rooms,
        num_timeslots=p1.num_timeslots,
        lecturer_prefs=p1.lecturer_prefs,
        randomize=False,
    )
    child.genes = intermediate[:cut] + p3.genes[cut:]
    child.calculate_fitness()
    return child


def tournament_select(
    population: List[Schedule], tournament_size: int = 3
) -> Schedule:
    """Select the fittest individual from a random tournament."""
    if not population:
        raise ValueError("Populasi tidak boleh kosong.")
    size = min(max(2, tournament_size), len(population))
    contestants = random.sample(population, size)
    return max(contestants, key=lambda individual: individual.fitness)

def mutate(schedule: Schedule, mutation_rate: float = 0.1) -> Schedule:
    mutant = copy.deepcopy(schedule)
    skpb_indices = [
        idx for idx, r in enumerate(mutant.rooms)
        if r["id"] in ["SKPB", "SKPB IUP"] or r.get("tipe") == "SKPB"
    ]
    dept_indices = [idx for idx, r in enumerate(mutant.rooms) if idx not in skpb_indices]

    for i in range(len(mutant.genes)):
        if random.random() < mutation_rate:
            c = mutant.courses[i]
            cid = c.get("id", "")
            is_skpb = is_skpb_course(c)
            allowed_rooms = skpb_indices if is_skpb else dept_indices
            capacity_rooms = [
                idx for idx in allowed_rooms if mutant.rooms[idx]["cap"] >= c["mhs"]
            ]
            candidates = capacity_rooms or allowed_rooms
            if candidates:
                r = random.choice(candidates)
            else:
                r = random.randint(0, len(mutant.rooms) - 1)
            t = random.randint(0, mutant.num_timeslots - 1)
            mutant.genes[i] = encode_gene(r, t, mutant.num_timeslots)

    mutant.calculate_fitness()
    return mutant


def _mutate_schedule_worker(task: Tuple[Schedule, float, int]) -> Schedule:
    """Worker CPU untuk mutasi dan evaluasi satu individu secara terisolasi."""
    schedule, mutation_rate, seed = task
    random.seed(seed)
    return mutate(schedule, mutation_rate)

def buat_jadwal(
    data_mata_kuliah: List[Dict],
    data_dosen: List[Dict],
    data_ruang: List[Dict],
    slot_waktu: List[Dict],
    populasi_size: int = 50,
    generasi: int = 100,
    mutation_rate: float = 0.1,
    callback: Optional[Callable[[Dict], None]] = None,
    random_seed: Optional[int] = None,
    parallel_workers: int = 1,
) -> Tuple[Schedule, float, List[Dict]]:
    if populasi_size < 3:
        raise ValueError("populasi_size minimal 3 agar tiga parent dapat dipilih.")
    if generasi < 1:
        raise ValueError("generasi harus lebih besar dari 0.")
    if not data_mata_kuliah:
        raise ValueError("Data mata kuliah tidak boleh kosong.")
    if not data_ruang:
        raise ValueError("Data ruang tidak boleh kosong.")
    if not slot_waktu:
        raise ValueError("Data slot waktu tidak boleh kosong.")
    if parallel_workers < 1:
        raise ValueError("parallel_workers harus minimal 1.")
    available_workers = getattr(os, "process_cpu_count", os.cpu_count)() or 1
    parallel_workers = min(int(parallel_workers), available_workers)
    if random_seed is not None:
        random.seed(random_seed)

    t_start = time.time()
    num_timeslots = len(slot_waktu)
    rooms = [
        {
            "id": r["id"],
            "cap": r["cap"],
            "gedung": r.get("gedung", ""),
            "tipe": r.get("tipe", "SKPB" if r["id"] in ["SKPB", "SKPB IUP"] else "Departemen"),
        }
        for r in data_ruang
    ]

    if callback:
        callback({
            "step": "init",
            "phase": "Tahap 1: Validasi Parameter & Pemetaan Kromosom",
            "progress": 0.04,
            "message": f"Menganalisis {len(data_mata_kuliah)} mata kuliah, {len(rooms)} ruang kuliah, dan {num_timeslots} slot waktu.",
            "elapsed": time.time() - t_start,
            "eta": None,
            "speed": 0.0,
            "gen": 0,
            "total_gen": generasi,
            "fitness": 0.0,
        })

    lecturer_prefs: Dict[str, Dict] = {}
    for d in data_dosen:
        nama = d.get("nama", d.get("id", ""))
        raw_slots = d.get("pref_slot", list(range(num_timeslots)))
        if isinstance(raw_slots, str):
            slots = []
            for s in raw_slots.split(","):
                s = s.strip()
                if s.isdigit():
                    slots.append(int(s))
        elif isinstance(raw_slots, (list, tuple, set)):
            slots = [int(s) for s in raw_slots if str(s).strip().isdigit()]
        else:
            slots = list(range(num_timeslots))

        raw_ruangs = d.get("pref_ruang", [r["id"] for r in rooms])
        if isinstance(raw_ruangs, str):
            ruangs = [r.strip() for r in raw_ruangs.split(",") if r.strip()]
        elif isinstance(raw_ruangs, (list, tuple, set)):
            ruangs = [str(r).strip() for r in raw_ruangs if str(r).strip()]
        else:
            ruangs = [r["id"] for r in rooms]

        lecturer_prefs[nama] = {
            "pref_time_idx": slots,
            "pref_room_id": ruangs,
        }

    courses = [dict(mk) for mk in data_mata_kuliah]

    def make_schedule():
        s = Schedule(
            courses=courses,
            rooms=rooms,
            num_timeslots=num_timeslots,
            lecturer_prefs=lecturer_prefs,
            randomize=True,
        )
        s.calculate_fitness()
        return s

    population = [make_schedule() for _ in range(populasi_size)]
    history = []
    jadwal_terbaik = max(population, key=lambda x: x.fitness)

    if callback:
        callback({
            "step": "eval",
            "phase": "Tahap 2: Pembentukan Populasi Awal",
            "progress": 0.08,
            "message": f"Populasi awal ({populasi_size} jadwal acak) berhasil dibangkitkan. Fitness awal: {jadwal_terbaik.fitness:.4f}.",
            "elapsed": time.time() - t_start,
            "eta": None,
            "speed": 0.0,
            "gen": 0,
            "total_gen": generasi,
            "fitness": jadwal_terbaik.fitness,
        })

    update_interval = 1 if generasi <= 40 else max(1, generasi // 35)

    executor = ProcessPoolExecutor(max_workers=parallel_workers) if parallel_workers > 1 else None
    fallback_reported = False
    try:
        for gen in range(generasi):
            population.sort(key=lambda x: x.fitness, reverse=True)
            best = population[0]

            history.append({
                "generasi": gen + 1,
                "fitness_terbaik": round(best.fitness, 6),
                "hard_violations": best.hard_violations,
                "soft_violations": best.soft_violations,
            })

            if best.fitness > jadwal_terbaik.fitness:
                jadwal_terbaik = copy.deepcopy(best)

            elapsed = time.time() - t_start
            completed = gen + 1
            speed = completed / elapsed if elapsed > 0 else 0.0
            remaining = generasi - completed
            eta = remaining / speed if speed > 0 else 0.0

            is_last = (completed == generasi) or (best.fitness >= 2.0)
            if callback and (completed % update_interval == 0 or is_last):
                progress_val = 0.08 + (0.88 * (completed / generasi))
                callback({
                    "step": "evolution",
                    "phase": f"Tahap 3: Siklus Evolusi (Generasi {completed} dari {generasi})",
                    "progress": min(0.96, progress_val),
                    "message": (
                        f"Gen {completed:03d}/{generasi}: P1({population[0].fitness:.3f}) + "
                        f"P2({population[1].fitness:.3f}) + P3({population[2].fitness:.3f}) "
                        f"-> Mutasi paralel ({parallel_workers if executor else 1} worker) -> Fitness: {best.fitness:.4f} "
                        f"(Hard: {best.hard_violations}, Soft: {best.soft_violations})"
                    ),
                    "elapsed": elapsed,
                    "eta": eta,
                    "speed": speed,
                    "gen": completed,
                    "total_gen": generasi,
                    "fitness": best.fitness,
                    "hard_violations": best.hard_violations,
                    "soft_violations": best.soft_violations,
                })

            # Terminasi dini jika solusi bebas konflik telah tercapai
            if best.fitness >= 2.0:
                if callback:
                    callback({
                        "step": "converged",
                        "phase": "Tahap 4: Konvergensi Sempurna Tercapai",
                        "progress": 0.98,
                        "message": f"Konvergensi dini pada generasi ke-{completed}! Jadwal optimal bebas konflik ditemukan (Fitness: 2.0000).",
                        "elapsed": elapsed,
                        "eta": 0.0,
                        "speed": speed,
                        "gen": completed,
                        "total_gen": generasi,
                        "fitness": 2.0,
                        "hard_violations": 0,
                        "soft_violations": 0,
                    })
                break

            if len(population) >= 3:
                parents = [
                    tournament_select(population),
                    tournament_select(population),
                    tournament_select(population),
                ]
                child = crossover_3_parents(*parents)
                population.append(child)

            individuals = population[1:]
            if executor is None:
                mutated = [mutate(ind, mutation_rate) for ind in individuals]
            else:
                tasks = [
                    (individual, mutation_rate, random.randrange(0, 2**32))
                    for individual in individuals
                ]
                try:
                    mutated = list(executor.map(_mutate_schedule_worker, tasks))
                except BrokenProcessPool:
                    executor.shutdown(wait=False, cancel_futures=True)
                    executor = None
                    mutated = [mutate(ind, mutation_rate) for ind in individuals]
                    if callback and not fallback_reported:
                        callback({
                            "step": "parallel_fallback",
                            "phase": "Mode aman: pool CPU dipulihkan",
                            "progress": min(0.96, 0.08 + (0.88 * (completed / generasi))),
                            "message": (
                                "Worker CPU berhenti mendadak. Proses dilanjutkan "
                                "secara serial agar hasil GA tetap tersimpan."
                            ),
                            "elapsed": time.time() - t_start,
                            "eta": None,
                            "speed": 0.0,
                            "gen": completed,
                            "total_gen": generasi,
                            "fitness": best.fitness,
                        })
                        fallback_reported = True
            population = [population[0]] + mutated

            population.sort(key=lambda x: x.fitness, reverse=True)
            population = population[:populasi_size]
    finally:
        if executor is not None:
            executor.shutdown(wait=True)

    decoded = jadwal_terbaik._decode_all()
    for item in decoded:
        t_idx = item["t_idx"]
        if t_idx < len(slot_waktu):
            slot = slot_waktu[t_idx]
            jadwal_terbaik.courses[item["course_idx"]]["_slot_hari"] = slot.get("hari", "-")
            jadwal_terbaik.courses[item["course_idx"]]["_slot_sesi"] = slot.get("sesi", f"Sesi {(t_idx % 5) + 1}")
            jadwal_terbaik.courses[item["course_idx"]]["_slot_jam"] = (
                f"{slot.get('jam_mulai', '')} - {slot.get('jam_selesai', '')}"
            )

    total_elapsed = time.time() - t_start
    if callback:
        callback({
            "step": "completed",
            "phase": "Tahap 5: Penyusunan Jadwal Final Selesai",
            "progress": 1.0,
            "message": f"Proses selesai dalam {total_elapsed:.2f} detik. Seluruh jadwal siap ditampilkan.",
            "elapsed": total_elapsed,
            "eta": 0.0,
            "speed": len(history) / total_elapsed if total_elapsed > 0 else 0.0,
            "gen": len(history),
            "total_gen": generasi,
            "fitness": jadwal_terbaik.fitness,
            "hard_violations": jadwal_terbaik.hard_violations,
            "soft_violations": jadwal_terbaik.soft_violations,
        })

    return jadwal_terbaik, jadwal_terbaik.fitness, history


def analisis_defisit_sumber_daya(
    data_mata_kuliah: List[Dict],
    data_ruang: List[Dict],
    data_dosen: List[Dict],
    slot_waktu: List[Dict],
) -> Dict[str, Any]:
    """
    Riset & Audit Diagnostik Defisit Sumber Daya (Resource Deficit & Capacity Bottlenecks).
    Menganalisis keseimbangan Supply vs Demand pada ruang, kapasitas kursi, beban dosen,
    serta kepadatan rombel mahasiswa sebelum atau sesudah penjadwalan.
    """
    num_courses = len(data_mata_kuliah)
    num_rooms = len(data_ruang)
    num_slots = len(slot_waktu)
    total_slot_capacity = num_rooms * num_slots
    global_utilization = (num_courses / total_slot_capacity * 100.0) if total_slot_capacity > 0 else 0.0

    # 1. Analisis Zonasi Ruang: SKPB vs Departemen Teknik Informatika
    skpb_courses = [
        c for c in data_mata_kuliah
        if is_skpb_course(c)
    ]
    skpb_rooms = [
        r for r in data_ruang
        if r.get("id") in ["SKPB", "SKPB IUP"] or r.get("tipe") == "SKPB"
    ]
    skpb_demand = len(skpb_courses)
    skpb_supply = len(skpb_rooms) * num_slots
    skpb_util = (skpb_demand / skpb_supply * 100.0) if skpb_supply > 0 else 0.0
    skpb_deficit = max(0, skpb_demand - skpb_supply)

    dept_courses = [c for c in data_mata_kuliah if c not in skpb_courses]
    dept_rooms = [r for r in data_ruang if r not in skpb_rooms]
    dept_demand = len(dept_courses)
    dept_supply = len(dept_rooms) * num_slots
    dept_util = (dept_demand / dept_supply * 100.0) if dept_supply > 0 else 0.0
    dept_deficit = max(0, dept_demand - dept_supply)

    # 2. Analisis Kapasitas Kursi & Ruangan Besar (Large Lecture Bottleneck)
    max_room_cap = max([r.get("cap", 0) for r in data_ruang]) if data_ruang else 0
    impossible_courses = [c for c in data_mata_kuliah if c.get("mhs", 0) > max_room_cap]

    large_threshold = 40
    large_courses = [c for c in data_mata_kuliah if c.get("mhs", 0) >= large_threshold]
    large_rooms = [r for r in data_ruang if r.get("cap", 0) >= large_threshold]
    large_supply = len(large_rooms) * num_slots
    large_demand = len(large_courses)
    large_deficit = max(0, large_demand - large_supply)
    large_util = (large_demand / large_supply * 100.0) if large_supply > 0 else 0.0

    small_rooms = [r for r in data_ruang if r.get("cap", 0) <= 25]

    # 3. Analisis Beban Mengajar Dosen & Keterbatasan Slot Preferensi
    dosen_load: Dict[str, int] = {}
    for c in data_mata_kuliah:
        d = c.get("dosen", "Tidak Diketahui")
        dosen_load[d] = dosen_load.get(d, 0) + 1

    dosen_map: Dict[str, Dict] = {}
    for d in data_dosen:
        nama = d.get("nama", d.get("id", ""))
        pref_s = d.get("pref_slot", [])
        if isinstance(pref_s, str):
            p_list = [int(s.strip()) for s in pref_s.split(",") if s.strip().isdigit()]
        elif isinstance(pref_s, (list, tuple, set)):
            p_list = [int(s) for s in pref_s if str(s).strip().isdigit()]
        else:
            p_list = list(range(num_slots))
        dosen_map[nama] = {
            "num_slots": len(p_list),
            "slots": p_list,
            "role": d.get("role", ""),
            "rmk": d.get("rmk", ""),
        }

    dosen_bottlenecks = []
    for d_nama, count in dosen_load.items():
        pref_info = dosen_map.get(d_nama)
        avail_slots = pref_info["num_slots"] if pref_info else num_slots
        if avail_slots < count:
            dosen_bottlenecks.append({
                "dosen": d_nama,
                "kelas": count,
                "slot_preferensi": avail_slots,
                "defisit": count - avail_slots,
            })

    top_dosen_load = sorted(dosen_load.items(), key=lambda x: x[1], reverse=True)[:5]

    # 4. Analisis Kepadatan Rombel Mahasiswa per Angkatan
    rombel_counts: Dict[str, int] = {}
    for c in data_mata_kuliah:
        prodi = c.get("prodi", c.get("departemen", "Teknik Informatika"))
        sem = c.get("semester", 1)
        kls = c.get("kelas", "A")
        key = f"{prodi} Sem {sem} Kls {kls}"
        rombel_counts[key] = rombel_counts.get(key, 0) + 1

    overcrowded_rombels = [
        {"rombel": k, "jumlah_mk": v}
        for k, v in rombel_counts.items()
        if v > num_slots
    ]

    # 5. Sintesis Isu Kritis & Rekomendasi Solusi Teknis
    issues = []

    # Defisit Ruang SKPB
    if skpb_deficit > 0:
        issues.append({
            "kategori": "Kekurangan Ruang Kelas",
            "tingkat": "KRITIS",
            "pesan": f"Defisit Ruang SKPB: Kebutuhan {skpb_demand} kelas SKPB melebihi kapasitas {skpb_supply} slot ({len(skpb_rooms)} ruang x {num_slots} sesi). Defisit: {skpb_deficit} slot kelas.",
            "solusi": "Tambah ruang perkuliahan bersama di tab Ruang dengan kategori 'SKPB' (misal: Gedung Menara Sains / Teater A), atau kurangi jumlah rombel kelas bersama.",
        })
    elif skpb_util > 75.0:
        issues.append({
            "kategori": "Kekurangan Ruang Kelas",
            "tingkat": "PERINGATAN",
            "pesan": f"Utilisasi Ruang SKPB sangat padat ({skpb_util:.1f}%): {skpb_demand} kelas di {skpb_supply} slot ruang SKPB.",
            "solusi": "Jadwalkan slot alternatif atau buka sesi perkuliahan tambahan.",
        })

    # Defisit Ruang Departemen
    if dept_deficit > 0:
        issues.append({
            "kategori": "Kekurangan Ruang Kelas",
            "tingkat": "KRITIS",
            "pesan": f"Defisit Ruang Departemen: Kebutuhan {dept_demand} kelas melebihi suplai {dept_supply} slot ruang Departemen Teknik Informatika. Defisit: {dept_deficit} slot.",
            "solusi": "Tambah alokasi ruang kelas/lab Departemen di tab Ruang atau gunakan ruang serbaguna.",
        })

    # Kelas Melebihi Ruang Terbesar
    if impossible_courses:
        c_names = ", ".join([f"{c.get('id')} ({c.get('mhs')} mhs)" for c in impossible_courses[:3]])
        issues.append({
            "kategori": "Kapasitas Kursi Tidak Cukup",
            "tingkat": "KRITIS",
            "pesan": f"Kapasitas Kursi Fisik Terlampaui Mutlak: Terdapat {len(impossible_courses)} mata kuliah ({c_names}) dengan peserta melebihi kapasitas ruang terbesar yang ada ({max_room_cap} kursi).",
            "solusi": f"Perbesar kapasitas kursi ruang di tab Ruang (misal Aula Prof. Handayani menjadi >= {max([c.get('mhs', 0) for c in impossible_courses])} kursi) atau pecah kelas menjadi 2 rombel paralel.",
        })

    # Defisit Ruang Berkapasitas Besar
    if large_deficit > 0:
        issues.append({
            "kategori": "Kapasitas Kursi Tidak Cukup",
            "tingkat": "KRITIS",
            "pesan": f"Defisit Ruang Kelas Besar: Ada {large_demand} kelas dengan >= {large_threshold} mahasiswa, tetapi hanya ada {large_supply} slot ruang besar ({len(large_rooms)} ruang). Defisit: {large_deficit} slot.",
            "solusi": "Tingkatkan kapasitas ruang sedang atau tambahkan ruang kelas berkapasitas >= 40 kursi.",
        })
    elif large_util > 80.0:
        issues.append({
            "kategori": "Kapasitas Kursi Tidak Cukup",
            "tingkat": "PERINGATAN",
            "pesan": f"Tekanan Ruang Besar Tinggi ({large_util:.1f}%): {large_demand} kelas besar merebut {large_supply} slot ruang besar.",
            "solusi": "Pantau potensi overcapacity pada sesi-sesi puncak.",
        })

    # Defisit Slot Preferensi Dosen
    if dosen_bottlenecks:
        d_details = "; ".join([f"{b['dosen']} ({b['kelas']} kelas vs {b['slot_preferensi']} slot)" for b in dosen_bottlenecks[:3]])
        issues.append({
            "kategori": "Kekurangan Ketersediaan Dosen",
            "tingkat": "KRITIS",
            "pesan": f"Kekurangan Ketersediaan Slot Dosen: {len(dosen_bottlenecks)} dosen mengampu kelas lebih banyak daripada slot preferensi yang dibuka ({d_details}). Secara matematis pasti memicu bentrok atau pelanggaran preferensi.",
            "solusi": "Perluas preferensi slot waktu dosen pada tab Dosen agar minimal sama dengan atau lebih banyak dari jumlah kelas yang diampu.",
        })

    # Beban Dosen Ekstrem
    heavy_lecturers = [d for d in top_dosen_load if d[1] >= 4]
    if heavy_lecturers:
        issues.append({
            "kategori": "Beban Mengajar Berlebih",
            "tingkat": "PERINGATAN",
            "pesan": f"Beban Dosen Sangat Tinggi: {len(heavy_lecturers)} dosen mengampu >= 4 kelas per semester (tertinggi: {heavy_lecturers[0][0]} mengampu {heavy_lecturers[0][1]} kelas).",
            "solusi": "Pertimbangkan distribusi tim teaching atau penugasan dosen paralel dari RMK yang sama.",
        })

    # Rombel Mahasiswa Terlalu Padat
    if overcrowded_rombels:
        issues.append({
            "kategori": "Kepadatan Rombel Mahasiswa",
            "tingkat": "KRITIS",
            "pesan": f"Kepadatan Rombel Mustahil: Rombel {overcrowded_rombels[0]['rombel']} memiliki {overcrowded_rombels[0]['jumlah_mk']} mata kuliah, melebihi total {num_slots} slot sesi mingguan yang tersedia.",
            "solusi": "Pindahkan mata kuliah elektif/pilihan ke paket semester lain.",
        })

    if not issues:
        issues.append({
            "kategori": "Keseimbangan Sumber Daya",
            "tingkat": "OPTIMAL",
            "pesan": "Keseimbangan sumber daya ideal: Rasio supply-demand ruang seimbang, kapasitas kursi mencukupi seluruh rombel, dan ketersediaan waktu dosen memadai.",
            "solusi": "Sistem siap mengeksekusi optimasi Algoritma Genetika dengan peluang konvergensi tinggi.",
        })

    return {
        "global": {
            "total_courses": num_courses,
            "total_rooms": num_rooms,
            "total_slots": num_slots,
            "total_slot_capacity": total_slot_capacity,
            "utilization_rate": round(global_utilization, 2),
            "max_room_cap": max_room_cap,
        },
        "zonasi": {
            "skpb_demand": skpb_demand,
            "skpb_supply": skpb_supply,
            "skpb_rooms_count": len(skpb_rooms),
            "skpb_util": round(skpb_util, 2),
            "skpb_deficit": skpb_deficit,
            "dept_demand": dept_demand,
            "dept_supply": dept_supply,
            "dept_rooms_count": len(dept_rooms),
            "dept_util": round(dept_util, 2),
            "dept_deficit": dept_deficit,
        },
        "kapasitas": {
            "large_threshold": large_threshold,
            "large_demand": large_demand,
            "large_supply": large_supply,
            "large_rooms_count": len(large_rooms),
            "large_deficit": large_deficit,
            "large_util": round(large_util, 2),
            "impossible_count": len(impossible_courses),
            "impossible_courses": impossible_courses,
            "small_rooms_count": len(small_rooms),
        },
        "dosen": {
            "bottlenecks": dosen_bottlenecks,
            "top_load": top_dosen_load,
            "total_dosen_active": len(dosen_load),
        },
        "rombel": {
            "overcrowded": overcrowded_rombels,
            "total_rombels": len(rombel_counts),
        },
        "issues": issues,
    }
