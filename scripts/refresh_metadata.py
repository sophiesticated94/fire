"""Add geometry information from the native SMV file without recalculation."""
from pathlib import Path
import json
import fdsreader
root=Path(__file__).resolve().parent.parent
for file in (root/'runs').glob('*/result.json'):
    result=json.loads(file.read_text(encoding='utf-8'))
    if 'solidBounds' not in result:
        sim=fdsreader.Simulation(str(file.parent))
        result['solidBounds']=[o.bounding_box.as_list() for o in sim.obstructions]
        file.write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
        print(file.parent.name,result['solidBounds'])
