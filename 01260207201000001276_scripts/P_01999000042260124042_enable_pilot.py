"""Enable planning-time reservations for pilot phase.

FILE_ID: 01999000042260124042
DOC_ID: P_01999000042260124042
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "govreg_core"))

from P_01999000042260124030_shared_utils import atomic_json_write, utc_timestamp


def enable_pilot():
    """Enable planning-time reservations for pilot phase."""
    config_path = Path(".state/feature_flags.json")
    
    # Read current flags
    if config_path.exists():
        import json
        with open(config_path) as f:
            flags = json.load(f)
    else:
        flags = {}
    
    # Enable reservation flag
    flags["enable_planning_reservations"] = True
    flags["pilot_enabled_at"] = utc_timestamp()
    flags["pilot_status"] = "ACTIVE"
    
    # Write back
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(flags, f, indent=2)
    
    print(f"✓ Pilot enabled at {flags['pilot_enabled_at']}")
    print(f"✓ Config: {config_path}")
    print(json.dumps(flags, indent=2))


if __name__ == "__main__":
    import json
    enable_pilot()
