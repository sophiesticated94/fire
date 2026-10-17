"""Read-only Windows DXGI inventory and per-process GPU engine evidence."""
import argparse
import ctypes as c
from ctypes import wintypes as w
import json
import os
import subprocess
import time
import uuid


class Guid(c.Structure):
    _fields_ = [('bytes', c.c_ubyte * 16)]


class Luid(c.Structure):
    _fields_ = [('low', w.DWORD), ('high', w.LONG)]


class Desc(c.Structure):
    _fields_ = [('description', w.WCHAR * 128), ('vendor', w.UINT), ('device', w.UINT),
                ('subsystem', w.UINT), ('revision', w.UINT), ('dedicatedVideo', c.c_size_t),
                ('dedicatedSystem', c.c_size_t), ('sharedSystem', c.c_size_t), ('luid', Luid), ('flags', w.UINT)]


def inventory():
    if os.name != 'nt':
        raise RuntimeError('DXGI verification requires Windows')
    dxgi = c.WinDLL('dxgi')
    create = dxgi.CreateDXGIFactory1
    create.argtypes = [c.POINTER(Guid), c.POINTER(c.c_void_p)]
    create.restype = c.c_long
    iid = Guid((c.c_ubyte * 16).from_buffer_copy(uuid.UUID('770aae78-f26f-4dba-a829-253c83d1b387').bytes_le))
    factory = c.c_void_p()
    hr = create(c.byref(iid), c.byref(factory))
    if hr < 0:
        raise OSError(f'CreateDXGIFactory1 HRESULT {hr:#x}')

    def method(obj, index, result, *types):
        table = c.cast(obj, c.POINTER(c.POINTER(c.c_void_p))).contents
        return c.WINFUNCTYPE(result, c.c_void_p, *types)(table[index])

    adapters = []
    try:
        enum = method(factory, 12, c.c_long, w.UINT, c.POINTER(c.c_void_p))
        for i in range(32):
            adapter = c.c_void_p()
            hr = enum(factory, i, c.byref(adapter))
            if hr & 0xffffffff == 0x887a0002:
                break
            if hr < 0:
                raise OSError(f'EnumAdapters1 HRESULT {hr:#x}')
            try:
                desc = Desc()
                hr = method(adapter, 10, c.c_long, c.POINTER(Desc))(adapter, c.byref(desc))
                if hr < 0:
                    raise OSError(f'GetDesc1 HRESULT {hr:#x}')
                adapters.append(dict(name=desc.description, vendor=f'0x{desc.vendor:04x}',
                                     device=f'0x{desc.device:04x}', dedicatedBytes=desc.dedicatedVideo,
                                     luid=f'0x{desc.luid.high & 0xffffffff:08x}_0x{desc.luid.low:08x}', flags=desc.flags))
            finally:
                method(adapter, 2, w.ULONG)(adapter)
    finally:
        method(factory, 2, w.ULONG)(factory)
    return adapters


def sample_process(pid, seconds):
    # PID is parsed as int, never supplied as shell text from an untrusted source.
    command = f"Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine | Where-Object {{$_.Name -like 'pid_{int(pid)}_*'}} | Select-Object Name,UtilizationPercentage | ConvertTo-Json -Compress"
    samples = []
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        proc = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', command],
                              capture_output=True, text=True, timeout=15, check=True)
        data = json.loads(proc.stdout or '[]')
        samples.extend(data if isinstance(data, list) else [data])
        time.sleep(.2)
    return samples


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', type=int)
    parser.add_argument('--seconds', type=float, default=3)
    args = parser.parse_args()
    print(json.dumps(dict(adapters=inventory(), samples=sample_process(args.pid, args.seconds) if args.pid else []), ensure_ascii=True))
