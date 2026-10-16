"""Summarize measured native GPU artifacts; never substitute guessed device data."""
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]


def percentile(values, fraction):
    values = sorted(v for v in values if v is not None)
    return values[min(len(values) - 1, int(len(values) * fraction))] if values else None


def describe(trial, timestamps=False):
    samples = trial.get('samples', trial.get('metrics', []))
    wall = trial['wallSeconds']
    gpu_times = [m['gpuMs'] for m in samples if m['gpuMs'] is not None]
    return {
        'wall_s': wall,
        'physical_s': trial['physicalSeconds'],
        'steps': trial['steps'],
        'steps_per_wall_s': trial['steps'] / wall,
        'physical_per_wall_s': trial['physicalSeconds'] / wall,
        'render_fps': trial['frames'] / wall if 'frames' in trial else None,
        'step_wall_ms_median': median(m['wallMs'] for m in samples),
        'step_wall_ms_p95': percentile([m['wallMs'] for m in samples], .95),
        'step_gpu_ms_median': median(gpu_times) if timestamps and gpu_times else None,
        'step_gpu_ms_p95': percentile([m['gpuMs'] for m in samples], .95) if timestamps else None,
        'pressure_iterations_median': median(m['iterations'] for m in samples),
        'pressure_iterations_max': max(m['iterations'] for m in samples),
        'readback_bytes': trial['readbackBytes'],
    }


def main():
    native = json.loads((ROOT / 'artifacts/gpu/benchmark-native.json').read_text(encoding='utf-8'))
    render = json.loads((ROOT / 'artifacts/gpu/render-benchmark-native.json').read_text(encoding='utf-8'))
    if render.get('timingScheme') != 'per-pass-step-sum':
        raise ValueError('Render benchmark predates the per-step timestamp correction; rerun it alone.')
    end, energy = native['at60'], native['at5']
    samples = native['samples'] + [end]
    summary = {
        'model': native['model'], 'adapter': native['adapter'],
        'render_adapter': render['adapter'], 'grid': native['cells'],
        'browser': render['userAgent'], 'timestamp_scheme': render['timingScheme'],
        'fields_bytes': render['fieldsBytes'], 'viewport_css': render['viewport'],
        'pixel_ratio': render['pixelRatio'], 'full_volume_readbacks': native['fullReadbacks'] + render['fullReadbacks'],
        'stability': {
            'physical_s': end['time'], 'steps': end['steps'],
            'mass_residual_final': end['cumulativeMassError'],
            'normalized_divergence_final': end['normalizedDivergence'],
            'sampled_normalized_divergence_max': max(m['normalizedDivergence'] for m in samples),
            'temperature_final_C': end['temperature'], 'speed_final_m_s': end['speed'],
            'energy_test_physical_s': energy['time'], 'energy_residual_J': energy['energyError'],
            'energy_residual_fraction_of_input': abs(energy['energyError']) / energy['time'],
        },
        # The first long stability run used last-frame timestamps, which are not
        # comparable to whole-step timestamps. Its GPU durations are discarded.
        'compute_only_trials': [describe(t) for t in native['trials']],
        'render_compute_trials': [describe(t, True) for t in render['trials']],
        'limitations': [
            'Native stability ran alongside short regression tests; its wall times are not isolated performance measurements.',
            'Compute-only legacy GPU timestamps are deliberately omitted.',
            'Render/compute measurements must be run alone, after all other GPU tests finish.',
            'Adapter selection is controlled by the browser; no RTX 4050 result is claimed.',
            'Field allocation excludes driver, renderer, staging and timestamp storage.',
        ],
    }
    assert end['time'] >= 60 and end['cumulativeMassError'] <= 1e-4
    assert abs(energy['energyError']) / energy['time'] <= .05
    out = ROOT / 'docs/benchmark-gpu-1.3.json'
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(out)
    for t in summary['render_compute_trials']:
        print(f"{t['render_fps']:.1f} FPS; {t['steps_per_wall_s']:.2f} steps/s; "
              f"{t['physical_per_wall_s']:.4f} physical/wall; GPU median {t['step_gpu_ms_median']:.3f} ms")


if __name__ == '__main__':
    main()
