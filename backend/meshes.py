"""Integer, conforming partitions of the original global Cartesian grid."""
from itertools import product

LAYOUTS = {
    'single': ((1,), (1,), (1,)),
    **{f'{axis}{n}': tuple((1,)*n if a==axis else (1,) for a in 'xyz') for axis in 'xyz' for n in (2,4)},
    'xy22': ((1,1),(1,1),(1,)),
    'z13': ((1,),(1,),(1,3)), 'z31': ((1,),(1,),(3,1)),
    'z1124': ((1,),(1,),(1,1,2,4)), 'z4211': ((1,),(1,),(4,2,1,1)),
}

def partition(cells, layout='single'):
    if layout not in LAYOUTS:raise ValueError(f'Nieznany podział: {layout}')
    axes=[]
    for count,weights in zip(cells,LAYOUTS[layout]):
        total=sum(weights)
        if count%total:raise ValueError('Podział nie zachowuje całkowitych komórek.')
        cuts=[0]
        for weight in weights:cuts.append(cuts[-1]+count*weight//total)
        axes.append(list(zip(cuts[:-1],cuts[1:])))
    return [dict(process=i,start=[a[0] for a in region],end=[a[1] for a in region])
            for i,region in enumerate(product(*axes))]

def mesh_records(bounds,cells,layout):
    records=partition(cells,layout)
    for record in records:
        record['cells']=[b-a for a,b in zip(record['start'],record['end'])]
        record['bounds']=[bounds[2*a]+(bounds[2*a+1]-bounds[2*a])*v/cells[a]
                          for a in range(3) for v in (record['start'][a],record['end'][a])]
    return records

def interface_mask(cells,layout):
    """Union of both cell layers adjacent to actual internal mesh faces."""
    import numpy as np
    mask=np.zeros(tuple(cells[::-1]),dtype=bool)
    records=partition(cells,layout)
    for i,left in enumerate(records):
        for right in records[i+1:]:
            for axis in range(3):
                touching=left['end'][axis]==right['start'][axis] or right['end'][axis]==left['start'][axis]
                if not touching:continue
                overlap=[(max(left['start'][a],right['start'][a]),min(left['end'][a],right['end'][a])) for a in range(3)]
                if any(b<=a for j,(a,b) in enumerate(overlap) if j!=axis):continue
                k=left['end'][axis] if left['end'][axis]==right['start'][axis] else right['end'][axis]
                overlap[axis]=(k-1,k+1)
                mask[tuple(slice(a,b) for a,b in overlap[::-1])]=True
    return mask
