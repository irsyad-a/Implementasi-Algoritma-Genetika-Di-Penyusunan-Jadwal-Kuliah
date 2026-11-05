import sys
sys.path.insert(0, r"c:\Users\LEGION\Downloads\ETS-KKA")
from kurikulum_data import KURIKULUM_2023, NO_CLASSROOM_NAME_KEYWORDS

for sem in [1, 2, 3, 4, 5, 6, 7, 8]:
    mks = [m for m in KURIKULUM_2023 if m['semester'] == sem]
    print(f"\n{'='*70}")
    print(f"=== SEMESTER {sem}: Total {len(mks)} Mata Kuliah ===")
    print(f"{'='*70}")
    for m in mks:
        is_no_room = any(k in m['nama'].lower() for k in NO_CLASSROOM_NAME_KEYWORDS)
        no_room_str = " [NO CLASSROOM/PROPOSAL/TA]" if is_no_room else ""
        print(f"[{m.get('id')}] {m.get('nama'):<38} | {m.get('kelas')} | SKS:{m.get('sks')} | {m.get('dosen')[:30]:<30} | {m.get('lokasi')}{no_room_str}")
