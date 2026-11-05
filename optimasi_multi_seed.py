"""Orkestrasi multi-start untuk menjalankan GA tanpa mengubah mesin GA inti."""

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from algoritma_ga import Schedule, buat_jadwal


def _quality_key(schedule: Schedule, fitness: float) -> Tuple[int, int, float]:
    return (
        -schedule.hard_violations,
        -schedule.soft_violations,
        fitness,
    )


def buat_jadwal_multi_seed(
    data_mata_kuliah: List[Dict],
    data_dosen: List[Dict],
    data_ruang: List[Dict],
    slot_waktu: List[Dict],
    seeds: Iterable[int],
    populasi_size: int = 50,
    generasi: int = 100,
    mutation_rate: float = 0.1,
    callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    parallel_workers: int = 1,
) -> Tuple[Schedule, float, List[Dict], int, List[Dict]]:
    """Run the GA and rank results by hard, soft, then fitness."""
    seed_list = list(dict.fromkeys(int(seed) for seed in seeds))
    if not seed_list:
        raise ValueError("Minimal satu seed harus diberikan.")

    best_result = None
    summaries: List[Dict] = []

    for run_index, seed in enumerate(seed_list, start=1):
        def run_callback(data: Dict[str, Any]) -> None:
            if callback is None:
                return
            forwarded = dict(data)
            forwarded["run"] = run_index
            forwarded["total_runs"] = len(seed_list)
            forwarded["seed"] = seed
            forwarded["progress"] = (
                (run_index - 1 + data.get("progress", 0.0)) / len(seed_list)
            )
            forwarded["phase"] = (
                f"Run {run_index}/{len(seed_list)} | Seed {seed} | "
                f"{data.get('phase', 'Proses')}"
            )
            callback(forwarded)

        schedule, fitness, history = buat_jadwal(
            data_mata_kuliah=data_mata_kuliah,
            data_dosen=data_dosen,
            data_ruang=data_ruang,
            slot_waktu=slot_waktu,
            populasi_size=populasi_size,
            generasi=generasi,
            mutation_rate=mutation_rate,
            callback=run_callback,
            random_seed=seed,
            parallel_workers=parallel_workers,
        )
        summary = {
            "run": run_index,
            "seed": seed,
            "fitness": fitness,
            "hard_violations": schedule.hard_violations,
            "soft_violations": schedule.soft_violations,
            "generations": len(history),
        }
        summaries.append(summary)

        candidate = (schedule, fitness, history, seed)
        if best_result is None or _quality_key(schedule, fitness) > _quality_key(
            best_result[0], best_result[1]
        ):
            best_result = candidate

    return (*best_result, summaries)
