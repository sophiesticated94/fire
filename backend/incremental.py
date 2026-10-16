"""Bounded file tails, complete CSV rows and monotonic sampling deadlines."""
import csv
import math
from pathlib import Path
import re

class Tail:
    def __init__(self,path):self.path=Path(path);self.offset=0;self.pending=b'';self.identity=None;self.generation=0;self.bytes_read=0
    def lines(self):
        if not self.path.exists():return []
        stat=self.path.stat();identity=(stat.st_dev,stat.st_ino)
        if self.identity is not None and (self.identity!=identity or stat.st_size<self.offset):
            self.offset=0;self.pending=b'';self.generation+=1
        self.identity=identity
        with self.path.open('rb') as f:
            f.seek(self.offset);data=f.read();self.offset=f.tell()
        self.bytes_read+=len(data);chunks=(self.pending+data).split(b'\n');self.pending=chunks.pop()
        return [line.decode('utf-8',errors='replace').rstrip('\r') for line in chunks]

class CSVSeries:
    def __init__(self,path):self.tail=Tail(path);self.generation=0;self.header_rows=0;self.names=None;self.data={};self.units={};self.unit_row=[]
    def read(self):
        lines=self.tail.lines()
        if self.generation!=self.tail.generation:
            self.generation=self.tail.generation;self.header_rows=0;self.names=None;self.data={};self.units={};self.unit_row=[]
        for line in lines:
            if not line.strip():continue
            row=next(csv.reader([line]))
            if self.header_rows<2:
                self.header_rows+=1
                if self.header_rows==1:self.unit_row=[s.strip().strip('"') for s in row]
                if self.header_rows==2:
                    self.names=[s.strip().strip('"') for s in row]
                    if len(set(self.names))!=len(self.names):raise ValueError('Duplicate CSV columns')
                    self.data={name:[] for name in self.names}
                    if len(self.unit_row)!=len(self.names):raise ValueError('CSV units/header length differs')
                    self.units=dict(zip(self.names,self.unit_row))
                continue
            if len(row)!=len(self.names):raise ValueError('Malformed complete CSV row')
            values=[float(value) for value in row]
            if not all(math.isfinite(value) for value in values):raise ValueError('Non-finite CSV row')
            for name,value in zip(self.names,values):self.data[name].append(value)
        return self.data if self.data and len(next(iter(self.data.values()))) else {}

class OutputProgress:
    def __init__(self,path):self.tail=Tail(path);self.generation=0;self.time=0
    def read(self):
        lines=self.tail.lines()
        if self.generation!=self.tail.generation:self.generation=self.tail.generation;self.time=0
        for line in lines:
            match=re.search(r'Total Time:\s*([\d.E+\-]+)',line)
            if match:self.time=max(self.time,float(match[1]))
        return self.time

class Deadline:
    def __init__(self,interval):self.interval=interval;self.next=0
    def due(self,now):
        if now<self.next:return False
        self.next=now+self.interval;return True
