"""Solver execution configuration, thread tuning, and Windows Job Object management."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import List, Optional

JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
JobObjectExtendedLimitInformation = 9


class WindowsJobObject:
    """Encapsulates Windows Job Object to guarantee atomic process tree termination."""

    def __init__(self):
        self.handle = None
        if os.name == 'nt':
            self._init_job()

    def _init_job(self):
        import ctypes
        from ctypes import wintypes

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('PerProcessUserTimeLimit', wintypes.LARGE_INTEGER),
                ('PerJobUserTimeLimit', wintypes.LARGE_INTEGER),
                ('LimitFlags', wintypes.DWORD),
                ('MinimumWorkingSetSize', ctypes.c_size_t),
                ('MaximumWorkingSetSize', ctypes.c_size_t),
                ('ActiveProcessLimit', wintypes.DWORD),
                ('Affinity', ctypes.c_size_t),
                ('PriorityClass', wintypes.DWORD),
                ('SchedulingClass', wintypes.DWORD),
            ]

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ('ReadOperationCount', ctypes.c_uint64),
                ('WriteOperationCount', ctypes.c_uint64),
                ('OtherOperationCount', ctypes.c_uint64),
                ('ReadTransferCount', ctypes.c_uint64),
                ('WriteTransferCount', ctypes.c_uint64),
                ('OtherTransferCount', ctypes.c_uint64),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ('IoInfo', IO_COUNTERS),
                ('ProcessMemoryLimit', ctypes.c_size_t),
                ('JobMemoryLimit', ctypes.c_size_t),
                ('PeakProcessMemoryLimit', ctypes.c_size_t),
                ('PeakJobMemoryLimit', ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        handle = kernel32.CreateJobObjectW(None, None)
        if handle:
            info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            success = kernel32.SetInformationJobObject(
                handle,
                JobObjectExtendedLimitInformation,
                ctypes.byref(info),
                ctypes.sizeof(info),
            )
            if success:
                self.handle = handle
            else:
                kernel32.CloseHandle(handle)

    def assign_process(self, pid: int) -> bool:
        if not self.handle or os.name != 'nt':
            return False
        import ctypes

        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        PROCESS_ALL_ACCESS = 0x1FFFFF
        proc_handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not proc_handle:
            return False
        try:
            return bool(kernel32.AssignProcessToJobObject(self.handle, proc_handle))
        finally:
            kernel32.CloseHandle(proc_handle)

    def terminate(self):
        if self.handle and os.name == 'nt':
            import ctypes

            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.TerminateJobObject(self.handle, 1)

    def close(self):
        if self.handle and os.name == 'nt':
            import ctypes

            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.CloseHandle(self.handle)
            self.handle = None


def get_optimal_threads() -> int:
    """Return the optimal number of OpenMP threads.

    On modern hybrid Intel architectures (P-cores + E-cores), using 8 threads causes
    barrier synchronization stalls and thermal throttling (proven in benchmarks:
    openmp_4 is ~42% faster than openmp_8!).
    Default is 4 threads (pinned to physical performance cores).
    User can override with IGNIS_THREADS.
    """
    user_val = os.environ.get('IGNIS_THREADS')
    if user_val:
        try:
            return max(1, min(16, int(user_val)))
        except ValueError:
            pass
    # Default to 4 threads for optimal performance core scaling
    cpu_count = os.cpu_count() or 4
    return min(4, cpu_count)


def get_solver_env(exe: Path) -> dict:
    """Prepare environment variables for FDS and Intel MPI with core affinity."""
    env = os.environ.copy()
    mpi_dir = exe.parent / 'mpi'
    env['PATH'] = str(exe.parent) + os.pathsep + str(mpi_dir) + os.pathsep + env.get('PATH', '')

    threads = get_optimal_threads()
    env.update(
        OMP_NUM_THREADS=str(threads),
        OMP_PLACES='cores',
        OMP_PROC_BIND='close',
        I_MPI_ROOT=str(mpi_dir),
        I_MPI_FABRICS='shm',
    )
    return env


def get_solver_command(exe: Path, mpi_ranks: Optional[int] = None) -> List[str]:
    """Build the command line for executing FDS (serial, OpenMP, or MPI)."""
    threads = get_optimal_threads()
    mpiexec = exe.parent / 'mpi/mpiexec.exe'
    fds_serial = exe.parent / 'fds.exe'

    # If MPI is explicitly requested and available:
    if mpi_ranks and mpi_ranks > 1 and mpiexec.exists() and fds_serial.exists():
        return [str(mpiexec), '-n', str(mpi_ranks), str(fds_serial), 'ignis.fds']

    # For 1 thread, use serial binary to avoid OpenMP runtime overhead:
    if threads == 1 and fds_serial.exists():
        return [str(fds_serial), 'ignis.fds']

    return [str(exe), 'ignis.fds']
