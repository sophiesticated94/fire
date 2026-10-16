"""Owned process trees; a Windows child cannot run before job assignment."""
import ctypes
from ctypes import wintypes as w
import os
import signal
import subprocess
import threading
import time

class WindowsAPI:
    def __init__(self):
        self.dll=ctypes.WinDLL('kernel32',use_last_error=True)
        signatures={
            'CreateJobObjectW':([ctypes.c_void_p,w.LPCWSTR],w.HANDLE),
            'SetInformationJobObject':([w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD],w.BOOL),
            'AssignProcessToJobObject':([w.HANDLE,w.HANDLE],w.BOOL),
            'TerminateJobObject':([w.HANDLE,w.UINT],w.BOOL),
            'CloseHandle':([w.HANDLE],w.BOOL),'ResumeThread':([w.HANDLE],w.DWORD),
            'WaitForSingleObject':([w.HANDLE,w.DWORD],w.DWORD),
            'GetExitCodeProcess':([w.HANDLE,ctypes.POINTER(w.DWORD)],w.BOOL),
            'TerminateProcess':([w.HANDLE,w.UINT],w.BOOL),
            'OpenProcess':([w.DWORD,w.BOOL,w.DWORD],w.HANDLE),
            'GetProcessAffinityMask':([w.HANDLE,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)],w.BOOL),
            'QueryInformationJobObject':([w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD,ctypes.c_void_p],w.BOOL),
        }
        for name,(args,result) in signatures.items():
            f=getattr(self.dll,name); f.argtypes=args; f.restype=result
    @staticmethod
    def check(ok):
        if not ok: raise ctypes.WinError(ctypes.get_last_error())
        return ok

class BasicLimits(ctypes.Structure):
    _fields_=[('process_time',ctypes.c_int64),('job_time',ctypes.c_int64),('flags',w.DWORD),('min_ws',ctypes.c_size_t),('max_ws',ctypes.c_size_t),('active',w.DWORD),('affinity',ctypes.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
class IOCounters(ctypes.Structure):
    _fields_=[(n,ctypes.c_uint64) for n in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]
class ExtendedLimits(ctypes.Structure):
    _fields_=[('basic',BasicLimits),('io',IOCounters),('process_memory',ctypes.c_size_t),('job_memory',ctypes.c_size_t),('peak_process_memory',ctypes.c_size_t),('peak_job_memory',ctypes.c_size_t)]
class StartupInfo(ctypes.Structure):
    _fields_=[('cb',w.DWORD),('reserved',w.LPWSTR),('desktop',w.LPWSTR),('title',w.LPWSTR)]+[(n,w.DWORD) for n in ('x','y','xsize','ysize','xchars','ychars','fill','flags')]+[('show',w.WORD),('reserved_size',w.WORD),('reserved_ptr',ctypes.c_void_p),('stdin',w.HANDLE),('stdout',w.HANDLE),('stderr',w.HANDLE)]
class ProcessInfo(ctypes.Structure):
    _fields_=[('process',w.HANDLE),('thread',w.HANDLE),('pid',w.DWORD),('tid',w.DWORD)]

_launch_lock=threading.Lock()

class ProcessTree:
    def __init__(self):
        self.api=WindowsAPI() if os.name=='nt' else None
        self.job=self.handle=self.thread=self.process=self.pid=None
        self.assigned=False
        self.stopped=False
        self._lock=threading.RLock()

    def start(self,command,cwd,env,log):
        with self._lock:
            try:
                if self.api:
                    self.job=self.api.check(self.api.dll.CreateJobObjectW(None,None))
                    limits=ExtendedLimits(); limits.basic.flags=0x2000
                    self.api.check(self.api.dll.SetInformationJobObject(self.job,9,ctypes.byref(limits),ctypes.sizeof(limits)))
                    create=self.api.dll.CreateProcessW
                    create.argtypes=[w.LPCWSTR,w.LPWSTR,ctypes.c_void_p,ctypes.c_void_p,w.BOOL,w.DWORD,ctypes.c_void_p,w.LPCWSTR,ctypes.POINTER(StartupInfo),ctypes.POINTER(ProcessInfo)]
                    create.restype=w.BOOL
                    import msvcrt
                    log_handle=msvcrt.get_osfhandle(log.fileno())
                    si=StartupInfo(cb=ctypes.sizeof(StartupInfo),flags=0x100,stdout=log_handle,stderr=log_handle)
                    pi=ProcessInfo()
                    environment=ctypes.create_unicode_buffer('\0'.join(f'{k}={v}' for k,v in sorted(env.items()))+'\0\0')
                    with _launch_lock:
                        os.set_handle_inheritable(log_handle,True)
                        try:
                            self.api.check(create(str(command[0]),ctypes.create_unicode_buffer(subprocess.list2cmdline(command)),None,None,True,0x4|0x400|0x08000000,environment,str(cwd),ctypes.byref(si),ctypes.byref(pi)))
                            self.handle,self.thread,self.pid=pi.process,pi.thread,pi.pid
                        finally: os.set_handle_inheritable(log_handle,False)
                    self.api.check(self.api.dll.AssignProcessToJobObject(self.job,self.handle))
                    self.assigned=True
                    if self.api.dll.ResumeThread(self.thread)==0xffffffff: self.api.check(False)
                    self.api.check(self.api.dll.CloseHandle(self.thread)); self.thread=None
                else:
                    self.process=subprocess.Popen(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True); self.pid=self.process.pid
            except BaseException:
                try:
                    self.terminate()
                    if self.pid:self.wait()
                finally:self.close()
                raise
        return self

    def poll(self):
        with self._lock:
            if self.api:
                if not self.handle: return None
                state=self.api.dll.WaitForSingleObject(self.handle,0)
                if state==0x102: return None
                if state!=0: self.api.check(False)
                code=w.DWORD(); self.api.check(self.api.dll.GetExitCodeProcess(self.handle,ctypes.byref(code)))
                return code.value
            return self.process.poll() if self.process else None

    def terminate(self):
        with self._lock:
            if self.api:
                if self.job: self.api.check(self.api.dll.TerminateJobObject(self.job,1))
                if self.handle and not self.assigned and self.poll() is None: self.api.check(self.api.dll.TerminateProcess(self.handle,1))
            elif self.process:
                try: os.killpg(self.process.pid,signal.SIGKILL)
                except ProcessLookupError: pass

    def wait(self,timeout=10):
        deadline=time.monotonic()+timeout
        while self.poll() is None:
            if time.monotonic()>=deadline: raise TimeoutError('Nie udało się zatrzymać solvera.')
            time.sleep(.02)
        if self.api and self.job:
            accounting=ctypes.create_string_buffer(48)
            while True:
                self.api.check(self.api.dll.QueryInformationJobObject(self.job,1,accounting,len(accounting),None))
                if ctypes.c_uint32.from_buffer(accounting,40).value==0: break
                if time.monotonic()>=deadline: raise TimeoutError('Procesy potomne solvera nie zakończyły się.')
                time.sleep(.02)
        code=self.poll();self.stopped=True
        return code

    def telemetry(self):
        if not self.api or not self.handle: return {}
        affinity,system=ctypes.c_size_t(),ctypes.c_size_t()
        self.api.check(self.api.dll.GetProcessAffinityMask(self.handle,ctypes.byref(affinity),ctypes.byref(system)))
        limits=ExtendedLimits(); self.api.check(self.api.dll.QueryInformationJobObject(self.job,9,ctypes.byref(limits),ctypes.sizeof(limits),None))
        accounting=ctypes.create_string_buffer(96)
        self.api.check(self.api.dll.QueryInformationJobObject(self.job,8,accounting,len(accounting),None))
        io=IOCounters.from_buffer(accounting,48)
        pids=ctypes.create_string_buffer(8+4096*ctypes.sizeof(ctypes.c_size_t))
        self.api.check(self.api.dll.QueryInformationJobObject(self.job,3,pids,len(pids),None))
        count=ctypes.c_uint32.from_buffer(pids,4).value
        process_affinity={}
        for i in range(count):
            pid=ctypes.c_size_t.from_buffer(pids,8+i*ctypes.sizeof(ctypes.c_size_t)).value
            handle=self.api.dll.OpenProcess(0x1000,False,pid)
            if not handle: continue  # A rank may have exited since enumeration.
            try:
                mask,system_mask=ctypes.c_size_t(),ctypes.c_size_t()
                if self.api.dll.GetProcessAffinityMask(handle,ctypes.byref(mask),ctypes.byref(system_mask)):process_affinity[str(pid)]=hex(mask.value)
            finally:self.api.check(self.api.dll.CloseHandle(handle))
        cpu=(ctypes.c_int64.from_buffer(accounting,0).value+ctypes.c_int64.from_buffer(accounting,8).value)/1e7
        return dict(affinityMask=hex(affinity.value),processAffinity=process_affinity,peakMemoryBytes=limits.peak_job_memory,
                    readBytes=io.read_bytes,writeBytes=io.write_bytes,cpuSeconds=cpu)

    def close(self):
        with self._lock:
            if self.api:
                errors=[]
                for name in ('thread','job','handle'):
                    handle=getattr(self,name)
                    if handle:
                        try:self.api.check(self.api.dll.CloseHandle(handle));setattr(self,name,None)
                        except OSError as exc:errors.append(exc)
                if errors:raise errors[0]
