import random
import unittest

from algoritma_ga import (
    Schedule,
    buat_jadwal,
    crossover_3_parents,
    encode_gene,
    is_skpb_course,
    tournament_select,
)
from kurikulum_data import (
    KURIKULUM_2023,
    DEFAULT_DOSEN_DATA,
    DEFAULT_RUANG_DATA,
)
from optimasi_multi_seed import buat_jadwal_multi_seed


COURSES = [
    {
        "id": "EF001",
        "nama": "Kelas 1",
        "dosen": "Dosen A",
        "mhs": 20,
        "prodi": "IF",
        "semester": 1,
        "kelas": "A",
        "lokasi": "Departemen",
    },
    {
        "id": "EF002",
        "nama": "Kelas 2",
        "dosen": "Dosen B",
        "mhs": 20,
        "prodi": "IF",
        "semester": 1,
        "kelas": "A",
        "lokasi": "Departemen",
    },
    {
        "id": "SM001",
        "nama": "Kelas SKPB",
        "dosen": "Dosen C",
        "mhs": 20,
        "prodi": "IF",
        "semester": 2,
        "kelas": "A",
        "lokasi": "SKPB",
    },
]
ROOMS = [
    {"id": "R1", "cap": 30, "tipe": "Departemen"},
    {"id": "SKPB", "cap": 30, "tipe": "SKPB"},
]
SLOTS = [
    {"hari": "Senin", "sesi": "Sesi 1"},
    {"hari": "Senin", "sesi": "Sesi 2"},
]
LECTURER_PREFS = {}


def schedule_with_genes(genes):
    schedule = Schedule(
        COURSES, ROOMS, len(SLOTS), LECTURER_PREFS, randomize=False
    )
    schedule.genes = genes
    schedule.calculate_fitness()
    return schedule


class GeneticAlgorithmTests(unittest.TestCase):
    def test_uni_one_point_uses_all_three_parents(self):
        parent_1 = schedule_with_genes([0, 0, 0])
        parent_2 = schedule_with_genes([1, 1, 1])
        parent_3 = schedule_with_genes([2, 2, 2])

        random.seed(4)
        child = crossover_3_parents(parent_1, parent_2, parent_3)

        self.assertEqual(len(child.genes), 3)
        self.assertTrue(all(
            gene in parent_1.genes + parent_2.genes + parent_3.genes
            for gene in child.genes
        ))
        self.assertIn(child.genes[-1], parent_3.genes)

    def test_tournament_select_returns_contestant_with_highest_fitness(self):
        candidates = [
            schedule_with_genes([encode_gene(0, 0, len(SLOTS))] * 3),
            schedule_with_genes([encode_gene(0, 1, len(SLOTS))] * 3),
            schedule_with_genes([encode_gene(1, 0, len(SLOTS))] * 3),
        ]
        candidates[0].fitness = 0.1
        candidates[1].fitness = 0.5
        candidates[2].fitness = 0.9

        random.seed(2)
        selected = tournament_select(candidates, tournament_size=3)

        self.assertIs(selected, candidates[2])

    def test_buat_jadwal_rejects_invalid_population(self):
        with self.assertRaises(ValueError):
            buat_jadwal(COURSES, [], ROOMS, SLOTS, populasi_size=2)

    def test_final_schedule_respects_room_zone_and_capacity(self):
        random.seed(8)
        schedule, _, _ = buat_jadwal(
            COURSES,
            [
                {"nama": "Dosen A"},
                {"nama": "Dosen B"},
                {"nama": "Dosen C"},
            ],
            ROOMS,
            SLOTS,
            populasi_size=10,
            generasi=10,
        )

        for row in schedule.get_schedule_table():
            if row["Kode MK"] == "SM001":
                self.assertEqual(row["Ruang"], "SKPB")
            else:
                self.assertEqual(row["Ruang"], "R1")
            self.assertLessEqual(row["Jumlah Mahasiswa"], row["Kapasitas Ruang"])

    def test_multi_seed_selects_lowest_hard_then_soft(self):
        result = buat_jadwal_multi_seed(
            COURSES,
            [{"nama": "Dosen A"}, {"nama": "Dosen B"}, {"nama": "Dosen C"}],
            ROOMS,
            SLOTS,
            seeds=[3, 4],
            populasi_size=8,
            generasi=5,
        )

        schedule, fitness, history, winner_seed, summaries = result
        self.assertIn(winner_seed, (3, 4))
        self.assertEqual(len(summaries), 2)
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(schedule.hard_violations, min(
            item["hard_violations"] for item in summaries
        ))

    def test_skpb_courses_are_classified_by_name_or_location(self):
        kalkulus = next(course for course in KURIKULUM_2023 if course["nama"] == "Kalkulus 1")
        etika = next(course for course in KURIKULUM_2023 if course["nama"] == "Etika Profesi")
        self.assertTrue(is_skpb_course(kalkulus))
        self.assertTrue(is_skpb_course(etika))
        self.assertIn(
            "Tim Dosen Etika Profesi (SKPB)",
            [lecturer["nama"] for lecturer in DEFAULT_DOSEN_DATA],
        )

    def test_default_skpb_rooms_total_five(self):
        skpb_rooms = [room for room in DEFAULT_RUANG_DATA if room["tipe"] == "SKPB"]
        self.assertEqual(len(skpb_rooms), 5)
        self.assertEqual(
            [room["id"] for room in skpb_rooms],
            ["SKPB", "SKPB IUP", "SKPB-101", "SKPB-102", "SKPB-103"],
        )
        self.assertEqual(
            [room["cap"] for room in skpb_rooms[-3:]],
            [60, 60, 60],
        )


if __name__ == "__main__":
    unittest.main()
