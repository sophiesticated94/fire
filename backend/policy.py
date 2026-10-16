"""Approval is a scientific checkpoint, never inferred from a benchmark PASS."""
import hashlib
import json
from pathlib import Path

VALIDATION_VERSION='validation-3'
POLICY_PATH=Path(__file__).resolve().parent.parent/'config/validation-v3.json'

def validation_policy():
    try:
        data=json.loads(POLICY_PATH.read_text(encoding='utf-8'))
        digest=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        approved=(data.get('version')==VALIDATION_VERSION and data.get('status')=='approved'
                  and bool(data.get('reviewedBy')) and bool(data.get('temporalLimits')) and bool(data.get('diagnosticLimits')))
        return dict(data=data,hash=digest,approved=approved)
    except (OSError,ValueError):return dict(data={},hash=None,approved=False)
