"""Windows CPU topology and measured thread affinity, with typed x64 handles."""
import ctypes
from ctypes import wintypes as w
import os

def cpu_sets():
    if os.name!='nt':return []
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    query=api.GetSystemCpuSetInformation
    query.argtypes=[ctypes.c_void_p,w.DWORD,ctypes.POINTER(w.DWORD),w.HANDLE,w.DWORD];query.restype=w.BOOL
    needed=w.DWORD();query(None,0,ctypes.byref(needed),None,0)
    if needed.value==0:raise ctypes.WinError(ctypes.get_last_error())
    data=ctypes.create_string_buffer(needed.value)
    if not query(data,needed,ctypes.byref(needed),None,0):raise ctypes.WinError(ctypes.get_last_error())
    records=[];offset=0
    while offset<needed.value:
        size=ctypes.c_uint32.from_buffer(data,offset).value;kind=ctypes.c_uint32.from_buffer(data,offset+4).value
        if size<24 or offset+size>needed.value:raise ValueError('Invalid Windows CPU topology record')
        if kind==0:
            records.append(dict(id=ctypes.c_uint32.from_buffer(data,offset+8).value,group=ctypes.c_uint16.from_buffer(data,offset+12).value,
                                logical=data[offset+14][0],core=data[offset+15][0],efficiency=data[offset+18][0],flags=data[offset+19][0]))
        offset+=size
    return records

def performance_cores(records=None):
    records=cpu_sets() if records is None else records
    classes={r['efficiency'] for r in records}
    if len(classes)<2:raise ValueError('Windows nie rozróżnia klas wydajności rdzeni; nie zgadujemy numerów CPU.')
    best=max(classes);cores={}
    for r in records:
        # Parking is dynamic and must not change a reproducible profile's IDs.
        # A hard process affinity makes Windows schedule/unpark these CPUs.
        if r['efficiency']!=best or (r['flags']&2 and not r['flags']&4):continue
        if r['group']!=0:raise ValueError('This local affinity profile requires processor group 0')
        key=(r['group'],r['core']);cores[key]=min(cores.get(key,r['logical']),r['logical'])
    return sorted(cores.values())

class ThreadEntry(ctypes.Structure):
    _fields_=[('size',w.DWORD),('usage',w.DWORD),('tid',w.DWORD),('pid',w.DWORD),('priority',w.LONG),('delta',w.LONG),('flags',w.DWORD)]
class GroupAffinity(ctypes.Structure):
    _fields_=[('mask',ctypes.c_size_t),('group',w.WORD),('reserved',w.WORD*3)]

def thread_affinities(pids):
    if os.name!='nt':return {}
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    signatures={'CreateToolhelp32Snapshot':([w.DWORD,w.DWORD],w.HANDLE),'Thread32First':([w.HANDLE,ctypes.POINTER(ThreadEntry)],w.BOOL),
                'Thread32Next':([w.HANDLE,ctypes.POINTER(ThreadEntry)],w.BOOL),'OpenThread':([w.DWORD,w.BOOL,w.DWORD],w.HANDLE),
                'GetThreadGroupAffinity':([w.HANDLE,ctypes.POINTER(GroupAffinity)],w.BOOL),'CloseHandle':([w.HANDLE],w.BOOL)}
    for name,(args,result) in signatures.items():getattr(api,name).argtypes=args;getattr(api,name).restype=result
    snapshot=api.CreateToolhelp32Snapshot(4,0)
    if snapshot==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    result={};entry=ThreadEntry(size=ctypes.sizeof(ThreadEntry));pids=set(pids)
    try:
        available=api.Thread32First(snapshot,ctypes.byref(entry))
        while available:
            if entry.pid in pids:
                handle=api.OpenThread(0x40,False,entry.tid)
                if handle:
                    try:
                        affinity=GroupAffinity()
                        if api.GetThreadGroupAffinity(handle,ctypes.byref(affinity)):result[str(entry.tid)]=dict(pid=entry.pid,group=affinity.group,mask=hex(affinity.mask))
                    finally:api.CloseHandle(handle)
            available=api.Thread32Next(snapshot,ctypes.byref(entry))
    finally:api.CloseHandle(snapshot)
    return result
