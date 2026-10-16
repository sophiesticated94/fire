"""Compatibility facade. Execution lives in profiles and runner."""
from .profiles import get_optimal_threads, build_profile

def get_solver_env(exe):
    return build_profile(exe).environment()

def get_solver_command(exe,mpi_ranks=None):
    return build_profile(exe,f'mpi{mpi_ranks}' if mpi_ranks and mpi_ranks>1 else 'openmp').command()
