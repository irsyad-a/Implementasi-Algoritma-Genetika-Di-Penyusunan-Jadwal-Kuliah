import random
import copy

# ==========================================
# 1. SETUP DATA RANDOM DUMMY (9 Mata Kuliah)
# ==========================================
NUM_ROOMS = 3
NUM_TIMESLOTS = 6

# Generate 9 Mata Kuliah acak agar pembagian 3 Parent simetris (3-3-3 gen)
COURSES = [
    {"id": f"MK_{i+1}", "dosen": f"Dosen_{i%3+1}", "mhs": random.choice([25, 30, 35, 50])}
    for i in range(9)
]

LECTURER_PREFS = {
    "Dosen_1": {"pref_time_idx": [0, 1, 2], "pref_room_id": ["Ruang_1"]},
    "Dosen_2": {"pref_time_idx": [2, 3, 4], "pref_room_id": ["Ruang_2"]},
    "Dosen_3": {"pref_time_idx": [1, 3, 5], "pref_room_id": ["Ruang_3"]}
}

ROOMS = [{"id": f"Ruang_{i+1}", "cap": 40} for i in range(NUM_ROOMS)]

# ==========================================
# 2. ENCODING & CLASS SCHEDULE
# ==========================================
def encode_gene(room_idx, time_idx):
    return (room_idx * NUM_TIMESLOTS) + time_idx

def decode_gene(merge_index):
    return merge_index // NUM_TIMESLOTS, merge_index % NUM_TIMESLOTS

class Schedule:
    def __init__(self, randomize=True):
        self.genes = []
        self.fitness = 0.0
        self.m = 0
        self.c = 0
        
        if randomize:
            for _ in COURSES:
                r = random.randint(0, NUM_ROOMS - 1)
                t = random.randint(0, NUM_TIMESLOTS - 1)
                self.genes.append(encode_gene(r, t))

    def calculate_fitness(self):
        m, c = 0, 0
        decoded = []
        for i, gene in enumerate(self.genes):
            r_idx, t_idx = decode_gene(gene)
            decoded.append({"course": COURSES[i], "r": r_idx, "t": t_idx})
            
        for i in range(len(decoded)):
            if decoded[i]["course"]["mhs"] > ROOMS[decoded[i]["r"]]["cap"]:
                m += 1
            for j in range(i + 1, len(decoded)):
                if decoded[i]["r"] == decoded[j]["r"] and decoded[i]["t"] == decoded[j]["t"]:
                    m += 1
                if decoded[i]["course"]["dosen"] == decoded[j]["course"]["dosen"] and decoded[i]["t"] == decoded[j]["t"]:
                    m += 1

        for item in decoded:
            dosen = item["course"]["dosen"]
            if dosen in LECTURER_PREFS:
                if item["t"] not in LECTURER_PREFS[dosen]["pref_time_idx"]:
                    c += 1
                if ROOMS[item["r"]]["id"] not in LECTURER_PREFS[dosen]["pref_room_id"]:
                    c += 1
                    
        self.m, self.c = m, c
        denom = m + (c / (c + 1.0))
        self.fitness = 2.0 if denom == 0 else 1.0 / denom

# ==========================================
# 3. UNI-ONE-POINT CROSSOVER (3 PARENTS)
# ==========================================
def crossover_3_parents_demo(p1, p2, p3):
    n = len(p1.genes)
    mask = [random.randint(0, 1) for _ in range(n)]
    intermediate = [
        p1.genes[i] if mask[i] == 0 else p2.genes[i]
        for i in range(n)
    ]
    cut = random.randint(1, n - 1) if n > 1 else n

    child = Schedule(randomize=False)
    child.genes = intermediate[:cut] + p3.genes[cut:]
    child.calculate_fitness()
    return child, mask, intermediate, cut

# ==========================================
# 4. EKSEKUSI DEMO
# ==========================================
if __name__ == "__main__":
    # Generasi populasi acak sebanyak 20 individu
    population = [Schedule(randomize=True) for _ in range(20)]
    for ind in population:
        ind.calculate_fitness()
        
    # Urutkan populasi berdasarkan Fitness tertinggi untuk mengambil Top 3 Solusi
    population.sort(key=lambda x: x.fitness, reverse=True)
    
    p1 = population[0]
    p2 = population[1]
    p3 = population[2]
    
    child, mask, intermediate, cut = crossover_3_parents_demo(p1, p2, p3)
    
    print("==========================================================================")
    print("DEMO PENGUJIAN UNI-ONE-POINT CROSSOVER (3 PARENTS)")
    print("==========================================================================")
    print(f"Parent 1 (Rank 1) | Fitness: {p1.fitness:.4f} | Genes: {p1.genes}")
    print(f"Parent 2 (Rank 2) | Fitness: {p2.fitness:.4f} | Genes: {p2.genes}")
    print(f"Parent 3 (Rank 3) | Fitness: {p3.fitness:.4f} | Genes: {p3.genes}")
    print("--------------------------------------------------------------------------")
    print(f"Mask Uniform P1/P2 : {mask}")
    print(f"Kromosom Perantara  : {intermediate}")
    print(f"Titik Potong One-Point: indeks {cut}")
    print(f"  - Prefix perantara [0:{cut}] : {intermediate[:cut]}")
    print(f"  - Suffix P3 [{cut}:9]        : {p3.genes[cut:]}")
    print("--------------------------------------------------------------------------")
    print(f"HASIL CHILD (Anak) | Fitness: {child.fitness:.4f}")
    print(f"Kromosom Child    : {child.genes}")
    print("==========================================================================")