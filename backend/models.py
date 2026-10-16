"""Typed, SI-normalized experiment inputs and reproducible FDS input decks."""
from __future__ import annotations

import hashlib
import json
from typing import Literal
from pydantic import BaseModel, Field

MODEL_VERSION = 'ignis-1.0.2'
SOLVER_VERSION = '6.11.1'


class Experiment(BaseModel):
    scene: Literal['candle', 'burner', 'wood'] = 'burner'
    quality: Literal['preview', 'fine'] = 'preview'
    duration: float = Field(default=6, ge=1, le=30)
    fuel: float = Field(default=12, ge=0, le=30, description='mg/s, candle and burner')
    oxygen: float = Field(default=20.9, ge=12, le=23, description='volume percent')
    wind: float = Field(default=0, ge=0, le=0.6, description='m/s, positive X')
    primary_air: float = Field(default=0.3, ge=0, le=1.2, description='fraction of stoichiometric air')
    ambient: float = Field(default=20, ge=0, le=50, description='degrees Celsius')
    moisture: float = Field(default=12, ge=0, le=30, description='wet-basis mass percent')
    ignition: float = Field(default=35, ge=0, le=70, description='incident kW/m2 for wood')

    def canonical(self):
        data = self.model_dump()
        data = {k:float(v) if isinstance(v,(int,float)) else v for k,v in data.items()}
        # Irrelevant hidden controls must not alter a case or cache key.
        if self.scene == 'wood':
            data['fuel'] = 0
            data['primary_air'] = 0
        elif self.scene == 'candle':
            data['primary_air'] = 0
            data['moisture'] = 0
            data['ignition'] = 0
        else:
            data['moisture'] = 0
            data['ignition'] = 0
        return data

    def key(self, profile=None):
        payload = {'config': self.canonical(), 'model': MODEL_VERSION, 'solver': SOLVER_VERSION}
        if profile is not None:
            from .profiles import TRANSPORT_VERSION
            payload.update(profile=profile.identity(),transport=TRANSPORT_VERSION)
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]


def geometry(c: Experiment):
    sizes = {'candle': (0.08, 0.08, 0.16), 'burner': (0.16, 0.16, 0.32), 'wood': (0.24, 0.24, 0.40)}
    grids = {'candle': (32, 32, 64), 'burner': (32, 32, 64), 'wood': (32, 32, 56)}
    size = sizes[c.scene]
    cells = grids[c.scene]
    if c.quality == 'fine':
        cells = tuple(int(n * 1.5) for n in cells)
    return [-size[0]/2, size[0]/2, -size[1]/2, size[1]/2, 0, size[2]], cells


def make_deck(c: Experiment, ranks: int = 1) -> str:
    bounds, cells = geometry(c)
    xb = ','.join(f'{n:.8f}' for n in bounds)
    # FDS background O2 mass fraction; replace O2 by N2 at fixed pressure.
    xo = c.oxygen / 100
    yo = xo*31.998/(xo*31.998 + (1-xo)*28.014)
    out = [
        "&HEAD CHID='ignis', TITLE='IGNIS quantitative educational experiment' /",
        *mesh_lines(bounds,cells,ranks),
        f"&TIME T_END={c.duration}, WALL_INCREMENT=20 /",
        f"&MISC TMPA={c.ambient}, Y_O2_INFTY={yo:.9f} /",
        "&DUMP DT_DEVC=0.1, DT_HRR=0.1, DT_SLCF=0.1, DT_SL3D=0.1 /",
        "&RADI RADIATION=.TRUE., NUMBER_RADIATION_ANGLES=50 /",
        "&SPEC ID='OXYGEN' /",
        "&SPEC ID='NITROGEN' /",
        "&SPEC ID='SOOT' /",
    ]
    if c.scene == 'wood':
        # Material constants and kinetics from the FDS verification case
        # surf_mass_part_char_cart_fuel.fds (FDS-6.11.1), not measured pine data.
        out += [
            "&REAC FUEL='WOOD', C=3.4, H=6.2, O=2.5, HEAT_OF_COMBUSTION=12000., SOOT_YIELD=0.015 /",
            "&SPEC ID='WATER VAPOR' /",
            "&MATL ID='CHAR', DENSITY=180., CONDUCTIVITY=1.0, SPECIFIC_HEAT=1.6, EMISSIVITY=1.0 /",
            "&MATL ID='PINE', DENSITY=360., CONDUCTIVITY=0.05, SPECIFIC_HEAT=1.0, EMISSIVITY=1.0, A=1.E20, E=1.6E5, NU_MATL=0.5, MATL_ID='CHAR', NU_SPEC=0.5, SPEC_ID='WOOD', HEAT_OF_REACTION=1000. /",
            "&MATL ID='MOISTURE', DENSITY=1000., CONDUCTIVITY=0.6, SPECIFIC_HEAT=4.18, A=1.E10, E=8.E4, NU_SPEC=1., SPEC_ID='WATER VAPOR', HEAT_OF_REACTION=2257. /",
        ]
        wet = c.moisture/100
        if wet:
            out += [f"&SURF ID='SAMPLE', MATL_ID(1,1:2)='PINE','MOISTURE', MATL_MASS_FRACTION(1,1:2)={1-wet},{wet}, THICKNESS=0.015, EXTERNAL_FLUX={c.ignition}, RAMP_EF='IGNITION', BACKING='INSULATED', COLOR='BROWN' /"]
        else:
            out += [f"&SURF ID='SAMPLE', MATL_ID='PINE', THICKNESS=0.015, EXTERNAL_FLUX={c.ignition}, RAMP_EF='IGNITION', BACKING='INSULATED', COLOR='BROWN' /"]
        out += [
            "&RAMP ID='IGNITION', T=0., F=1. /",
            f"&RAMP ID='IGNITION', T={min(10,c.duration*0.65)}, F=1. /",
            f"&RAMP ID='IGNITION', T={min(10,c.duration*0.65)+0.1}, F=0. /",
            "&OBST XB=-0.045,0.045,-0.045,0.045,0.,0.03, SURF_IDS='SAMPLE','INERT','INERT' /",
            "&DEVC ID='surface', XYZ=0.,0.,0.03, IOR=3, QUANTITY='WALL TEMPERATURE' /",
        ]
    else:
        is_candle = c.scene == 'candle'
        fuel = 'N-HEPTANE' if is_candle else 'METHANE'
        out += [f"&REAC FUEL='{fuel}', SOOT_YIELD={0.04 if is_candle else 0.008}, CO_YIELD=0.005 /"]
        # Heptane is a documented gas-phase surrogate, not wax thermochemistry.
        # A 10 mm candle source aligns on both the 2.5 mm and 1.667 mm grids.
        # It is an idealized porous vapour inlet, not a resolved candle wick.
        width = 0.01 if is_candle else 0.02
        h = 0.02 if is_candle else 0.04
        # Widths align with preview AND fine grids for burner; FDS snaps candle.
        dx = (bounds[1]-bounds[0])/cells[0]
        width = max(dx, round(width/dx)*dx)
        dz = bounds[5]/cells[2]
        h = round(h/dz)*dz
        # Symmetric extents are snapped explicitly to cell boundaries.
        half = max(dx, round(width/(2*dx))*dx)
        area = (2*half)**2
        mf = c.fuel*1e-6/area
        if is_candle or c.primary_air == 0:
            out += [f"&SURF ID='SOURCE', SPEC_ID='{fuel}', MASS_FLUX={mf}, TAU_MF=0.2, COLOR='GRAY 30' /"]
        else:
            # Methane needs 4 kg O2/kg fuel; remaining air is N2.
            air = mf*4.0/yo*c.primary_air
            out += [f"&SURF ID='SOURCE', SPEC_ID(1:3)='{fuel}','OXYGEN','NITROGEN', MASS_FLUX(1:3)={mf},{air*yo},{air*(1-yo)}, TAU_MF=0.2, COLOR='GRAY 30' /"]
        out += [f"&OBST XB={-half},{half},{-half},{half},0.,{h}, SURF_IDS='SOURCE','INERT','INERT' /"]
    # Open domain. Crosswind is a prescribed boundary flow, not a visual effect.
    if c.wind:
        out += [f"&SURF ID='WIND', VEL={-c.wind}, TMP_FRONT={c.ambient} /", "&VENT MB='XMIN', SURF_ID='WIND' /"]
    else:
        out += ["&VENT MB='XMIN', SURF_ID='OPEN' /"]
    out += [f"&VENT MB='{side}', SURF_ID='OPEN' /" for side in ('XMAX','YMIN','YMAX','ZMAX')]
    fields = [('TEMPERATURE', None), ('HRRPUV', None), ('DENSITY','SOOT'), ('VOLUME FRACTION','OXYGEN'), ('U-VELOCITY',None), ('V-VELOCITY',None), ('W-VELOCITY',None)]
    for quantity, species in fields:
        extra = f", SPEC_ID='{species}'" if species else ''
        out.append(f"&SLCF XB={xb}, QUANTITY='{quantity}'{extra}, CELL_CENTERED=.TRUE. /")
    out += [
        f"&DEVC ID='probe_T', XYZ=0.,0.,{bounds[5]*0.45}, QUANTITY='TEMPERATURE' /",
        f"&DEVC ID='probe_O2', XYZ=0.,0.,{bounds[5]*0.45}, QUANTITY='VOLUME FRACTION', SPEC_ID='OXYGEN' /",
        '&TAIL /',
    ]
    return '\n'.join(out)+'\n'


def mesh_lines(bounds,cells,ranks=1):
    if ranks not in (1,2,4) or cells[2]%ranks:
        raise ValueError('Nieprawidłowy podział siatki MPI.')
    if ranks==1:
        return [f"&MESH IJK={','.join(map(str,cells))}, XB={','.join(f'{n:.8f}' for n in bounds)} /"]
    lines=[]
    for i in range(ranks):
        b=list(bounds)
        b[4]=bounds[4]+(bounds[5]-bounds[4])*i/ranks
        b[5]=bounds[4]+(bounds[5]-bounds[4])*(i+1)/ranks
        lines.append(f"&MESH ID='M{i+1}', IJK={cells[0]},{cells[1]},{cells[2]//ranks}, XB={','.join(f'{n:.8f}' for n in b)}, MPI_PROCESS={i} /")
    return lines
