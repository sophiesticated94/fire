"""Rigorous, isolated performance benchmark for IGNIS FDS solver configurations.

Implements Etap 1 of docs/plan.md:
- Isolated test directories (artifacts/benchmark_tmp/<id>)
- Controlled process execution and returncode checking
- Verification of 'STOP: FDS completed successfully'
- Warm-up iteration + N measured iterations
- Subsystem CPU profiling from ignis_cpu.csv (DIVG, MASS, VELO, PRES, RADI, etc.)
- Statistical analysis: median, mean, min, max, stdev
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.models import Experiment, make_deck, geometry


def get_paths():
    fds_dir = ROOT / 'tools/fds/firemodels/FDS6/bin'
    exe_omp = fds_dir / 'fds_openmp.exe'
    exe_ser = fds_dir / 'fds.exe'
    mpiexec = fds_dir / 'mpi/mpiexec.exe'
    mpi_dir = fds_dir / 'mpi'
    return {
        'dir': fds_dir,
        'omp': exe_omp if exe_omp.exists() else None,
        'serial': exe_ser if exe_ser.exists() else None,
        'mpiexec': mpiexec if mpiexec.exists() else None,
        'mpi_dir': mpi_dir,
    }


def split_mesh_z(deck: str, num_splits: int) -> str:
    """Split a single MESH into num_splits equal sub-meshes along the Z axis."""
    lines = deck.splitlines()
    out = []
    mesh_found = False
    for line in lines:
        if line.strip().startswith('&MESH') and not mesh_found:
            mesh_found = True
            # Parse IJK and XB
            import re
            m_ijk = re.search(r'IJK=([0-9]+),([0-9]+),([0-9]+)', line)
            m_xb = re.search(r'XB=([0-9.\-]+),([0-9.\-]+),([0-9.\-]+),([0-9.\-]+),([0-9.\-]+),([0-9.\-]+)', line)
            if not m_ijk or not m_xb:
                raise ValueError(f"Cannot parse MESH line: {line}")
            nx, ny, nz = int(m_ijk.group(1)), int(m_ijk.group(2)), int(m_ijk.group(3))
            x0, x1 = float(m_xb.group(1)), float(m_xb.group(2))
            y0, y1 = float(m_xb.group(3)), float(m_xb.group(4))
            z0, z1 = float(m_xb.group(5)), float(m_xb.group(6))

            if nz % num_splits != 0:
                raise ValueError(f"Z cells ({nz}) not divisible by {num_splits}")
            sub_nz = nz // num_splits
            dz = (z1 - z0) / num_splits

            for i in range(num_splits):
                sub_z0 = z0 + i * dz
                sub_z1 = z0 + (i + 1) * dz
                out.append(
                    f"&MESH ID='M{i+1}', IJK={nx},{ny},{sub_nz}, "
                    f"XB={x0:.8f},{x1:.8f},{y0:.8f},{y1:.8f},{sub_z0:.8f},{sub_z1:.8f} /"
                )
        else:
            out.append(line)
    return '\n'.join(out) + '\n'


@dataclass
class RunMetrics:
    mode: str
    wall_time: float
    returncode: int
    success: bool
    num_steps: int = 0
    sim_time: float = 0.0
    cpu_total: float = 0.0
    cpu_divg: float = 0.0
    cpu_mass: float = 0.0
    cpu_velo: float = 0.0
    cpu_pres: float = 0.0
    cpu_radi: float = 0.0
    cpu_dump: float = 0.0
    cpu_comm: float = 0.0
    error: Optional[str] = None


def parse_cpu_csv(csv_path: Path) -> Dict[str, float]:
    if not csv_path.exists():
        return {}
    try:
        with csv_path.open('r', encoding='utf-8', errors='replace') as f:
            reader = list(csv.reader(f))
        if len(reader) < 2:
            return {}
        header = [h.strip() for h in reader[0]]
        # Sum metrics across all MPI ranks
        totals: Dict[str, float] = {}
        for row in reader[1:]:
            if not row or len(row) < len(header):
                continue
            for k, val in zip(header, row):
                try:
                    totals[k] = totals.get(k, 0.0) + float(val)
                except ValueError:
                    pass
        return totals
    except Exception:
        return {}


def parse_steps_csv(csv_path: Path) -> tuple[int, float]:
    if not csv_path.exists():
        return 0, 0.0
    try:
        with csv_path.open('r', encoding='utf-8', errors='replace') as f:
            reader = list(csv.reader(f))
        if len(reader) < 3:
            return 0, 0.0
        last = reader[-1]
        steps = int(last[0].strip())
        sim_t = float(last[3].strip())
        return steps, sim_t
    except Exception:
        return 0, 0.0


def execute_run(mode_name: str, deck_content: str, run_dir: Path, paths: dict) -> RunMetrics:
    run_dir.mkdir(parents=True, exist_ok=True)
    for item in run_dir.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item, ignore_errors=True)

    fds_file = run_dir / 'ignis.fds'
    fds_file.write_text(deck_content, encoding='ascii')

    env = os.environ.copy()
    env['PATH'] = str(paths['dir']) + os.pathsep + str(paths['mpi_dir']) + os.pathsep + env.get('PATH', '')

    cmd: List[str] = []

    if mode_name == 'serial':
        cmd = [str(paths['serial']), 'ignis.fds']
    elif mode_name.startswith('openmp_'):
        parts = mode_name.split('_')
        threads = parts[1]
        env['OMP_NUM_THREADS'] = threads
        if 'affinity' in mode_name:
            env['OMP_PLACES'] = 'cores'
            env['OMP_PROC_BIND'] = 'close'
        cmd = [str(paths['omp']), 'ignis.fds']
    elif mode_name.startswith('mpi_'):
        parts = mode_name.split('_')
        ranks = parts[1]
        env.update(
            I_MPI_ROOT=str(paths['mpi_dir']),
            I_MPI_FABRICS='shm',
            I_MPI_PIN_DOMAIN='core',
        )
        cmd = [str(paths['mpiexec']), '-n', ranks, str(paths['serial']), 'ignis.fds']
    else:
        raise ValueError(f"Unknown mode: {mode_name}")

    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            cwd=run_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=300,
        )
        t_wall = time.monotonic() - t0
        log_text = proc.stdout or ''
        (run_dir / 'solver.log').write_text(log_text, encoding='utf-8', errors='replace')
        out_file = run_dir / 'ignis.out'
        out_text = out_file.read_text(encoding='utf-8', errors='replace') if out_file.exists() else ''
        all_text = log_text + '\n' + out_text

        success = proc.returncode == 0 and 'STOP: FDS completed successfully' in all_text
        err_msg = None if success else all_text[-2000:]

        steps, sim_t = parse_steps_csv(run_dir / 'ignis_steps.csv')
        cpu_stats = parse_cpu_csv(run_dir / 'ignis_cpu.csv')

        return RunMetrics(
            mode=mode_name,
            wall_time=t_wall,
            returncode=proc.returncode,
            success=success,
            num_steps=steps,
            sim_time=sim_t,
            cpu_total=cpu_stats.get('Total T_USED (s)', 0.0),
            cpu_divg=cpu_stats.get('DIVG', 0.0),
            cpu_mass=cpu_stats.get('MASS', 0.0),
            cpu_velo=cpu_stats.get('VELO', 0.0),
            cpu_pres=cpu_stats.get('PRES', 0.0),
            cpu_radi=cpu_stats.get('RADI', 0.0),
            cpu_dump=cpu_stats.get('DUMP', 0.0),
            cpu_comm=cpu_stats.get('COMM', 0.0),
            error=err_msg,
        )
    except subprocess.TimeoutExpired:
        return RunMetrics(
            mode=mode_name,
            wall_time=time.monotonic() - t0,
            returncode=-1,
            success=False,
            error="Timeout (> 300s)",
        )
    except Exception as exc:
        return RunMetrics(
            mode=mode_name,
            wall_time=time.monotonic() - t0,
            returncode=-1,
            success=False,
            error=str(exc),
        )


def compute_summary(metrics_list: List[RunMetrics]) -> Dict:
    valid = [m for m in metrics_list if m.success]
    if not valid:
        return {
            'mode': metrics_list[0].mode if metrics_list else 'unknown',
            'success_count': 0,
            'total_count': len(metrics_list),
            'median_wall': None,
            'mean_wall': None,
            'min_wall': None,
            'max_wall': None,
            'stdev_wall': None,
            'error': metrics_list[-1].error if metrics_list else None,
        }

    wall_times = sorted([m.wall_time for m in valid])
    n = len(wall_times)
    median = wall_times[n // 2] if n % 2 != 0 else (wall_times[n // 2 - 1] + wall_times[n // 2]) / 2.0
    mean = sum(wall_times) / n
    variance = sum((x - mean) ** 2 for x in wall_times) / max(1, n - 1)
    stdev = math.sqrt(variance)

    # Average CPU subsystem breakdown
    avg_divg = sum(m.cpu_divg for m in valid) / n
    avg_mass = sum(m.cpu_mass for m in valid) / n
    avg_velo = sum(m.cpu_velo for m in valid) / n
    avg_pres = sum(m.cpu_pres for m in valid) / n
    avg_radi = sum(m.cpu_radi for m in valid) / n
    avg_dump = sum(m.cpu_dump for m in valid) / n
    avg_comm = sum(m.cpu_comm for m in valid) / n
    avg_steps = sum(m.num_steps for m in valid) / n

    return {
        'mode': valid[0].mode,
        'success_count': len(valid),
        'total_count': len(metrics_list),
        'median_wall': round(median, 2),
        'mean_wall': round(mean, 2),
        'min_wall': round(min(wall_times), 2),
        'max_wall': round(max(wall_times), 2),
        'stdev_wall': round(stdev, 2),
        'avg_steps': round(avg_steps, 0),
        'avg_divg': round(avg_divg, 2),
        'avg_mass': round(avg_mass, 2),
        'avg_velo': round(avg_velo, 2),
        'avg_pres': round(avg_pres, 2),
        'avg_radi': round(avg_radi, 2),
        'avg_dump': round(avg_dump, 2),
        'avg_comm': round(avg_comm, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="IGNIS Solver Performance Benchmark")
    parser.add_argument('--scene', choices=['burner', 'candle', 'wood'], default='burner')
    parser.add_argument('--duration', type=float, default=0.4, help='Physical simulation duration in seconds')
    parser.add_argument('--iterations', type=int, default=3, help='Number of measured repetitions (after warm-up)')
    parser.add_argument('--no-warmup', action='store_true', help='Skip unmeasured warm-up run')
    parser.add_argument(
        '--modes',
        type=str,
        default='serial,openmp_2,openmp_4,openmp_6,openmp_8,openmp_4_affinity,mpi_2,mpi_4',
        help='Comma-separated list of execution modes to benchmark',
    )
    parser.add_argument('--output-json', type=str, default='artifacts/benchmark_results.json')
    args = parser.parse_args()

    paths = get_paths()
    if not paths['serial'] or not paths['omp']:
        print("BŁĄD: Brak plików wykonywalnych FDS w tools/fds/... Uruchom setup.ps1.", file=sys.stderr)
        sys.exit(1)

    modes = [m.strip() for m in args.modes.split(',') if m.strip()]
    bench_root = ROOT / 'artifacts/benchmark_tmp'
    bench_root.mkdir(parents=True, exist_ok=True)

    print(f"\n========================================================")
    print(f" IGNIS FDS Solver Benchmark")
    print(f" Scena: {args.scene} | Czas fizyczny: {args.duration} s | Powtórzenia: {args.iterations}")
    print(f" Warianty: {', '.join(modes)}")
    print(f"========================================================\n")

    # Generate base input deck (Experiment requires duration >= 1)
    exp_dur = max(1.0, args.duration)
    c = Experiment(scene=args.scene, duration=exp_dur, quality='preview')
    base_deck = make_deck(c)
    if args.duration < 1.0:
        import re
        base_deck = re.sub(r'T_END=[0-9.]+', f'T_END={args.duration}', base_deck)

    all_summaries = []
    raw_results = {}

    for mode in modes:
        print(f"--- Tryb: {mode} ---")
        mode_deck = base_deck
        if mode.startswith('mpi_'):
            num_splits = int(mode.split('_')[1])
            mode_deck = split_mesh_z(base_deck, num_splits)

        mode_dir = bench_root / mode
        mode_runs: List[RunMetrics] = []

        # 1. Warm-up
        if not args.no_warmup:
            print("  [0/warm-up] ...", end=' ', flush=True)
            warmup = execute_run(mode, mode_deck, mode_dir / 'warmup', paths)
            status_str = f"OK ({warmup.wall_time:.2f} s)" if warmup.success else f"FAIL ({warmup.error[:50]}...)"
            print(status_str)

        # 2. Measured iterations
        for i in range(1, args.iterations + 1):
            print(f"  [{i}/{args.iterations}] ...", end=' ', flush=True)
            run = execute_run(mode, mode_deck, mode_dir / f'run_{i}', paths)
            status_str = f"OK ({run.wall_time:.2f} s)" if run.success else f"FAIL"
            print(status_str)
            mode_runs.append(run)

        summary = compute_summary(mode_runs)
        all_summaries.append(summary)
        raw_results[mode] = [asdict(m) for m in mode_runs]
        if summary['median_wall'] is not None:
            print(f"  => Mediana: {summary['median_wall']:.2f} s (min: {summary['min_wall']:.2f} s, max: {summary['max_wall']:.2f} s, stdev: {summary['stdev_wall']:.2f} s)\n")
        else:
            print(f"  => Wszystkie próby zakończyły się błędem!\n")

    # Output table
    print("\n" + "=" * 90)
    print(" PODSUMOWANIE WYNIKÓW BENCHMARKU")
    print("=" * 90)
    print(f"{'Tryb':<20} | {'Mediana [s]':<12} | {'Min [s]':<8} | {'Max [s]':<8} | {'Stdev':<8} | {'Kroki':<6} | {'DIVG':<6} | {'MASS':<6} | {'RADI':<6}")
    print("-" * 90)

    serial_median = next((s['median_wall'] for s in all_summaries if s['mode'] == 'serial'), None)

    for s in all_summaries:
        med_str = f"{s['median_wall']:.2f}" if s['median_wall'] else "ERR"
        speedup = f" ({(serial_median / s['median_wall']):.2f}x)" if serial_median and s['median_wall'] else ""
        med_fmt = f"{med_str}{speedup}"
        min_str = f"{s['min_wall']:.2f}" if s['min_wall'] else "-"
        max_str = f"{s['max_wall']:.2f}" if s['max_wall'] else "-"
        std_str = f"{s['stdev_wall']:.2f}" if s['stdev_wall'] else "-"
        steps_str = str(int(s.get('avg_steps', 0)))
        divg_str = f"{s.get('avg_divg', 0):.1f}"
        mass_str = f"{s.get('avg_mass', 0):.1f}"
        radi_str = f"{s.get('avg_radi', 0):.1f}"

        print(f"{s['mode']:<20} | {med_fmt:<12} | {min_str:<8} | {max_str:<8} | {std_str:<8} | {steps_str:<6} | {divg_str:<6} | {mass_str:<6} | {radi_str:<6}")

    print("=" * 90 + "\n")

    # Save JSON report
    out_path = ROOT / args.output_json
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_data = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'scene': args.scene,
        'duration': args.duration,
        'iterations': args.iterations,
        'summaries': all_summaries,
        'raw': raw_results,
    }
    out_path.write_text(json.dumps(report_data, indent=2), encoding='utf-8')
    print(f"Szczegółowy raport JSON zapisany w: {out_path}")


if __name__ == '__main__':
    main()
