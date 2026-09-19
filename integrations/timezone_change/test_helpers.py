from datetime import datetime, timezone
import importlib.util
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).parent / "custom_components" / "timezone_change"

pkg = types.ModuleType("custom_components.timezone_change")
pkg.__path__ = [str(ROOT)]
sys.modules["custom_components.timezone_change"] = pkg

for mod in ("models", "helpers"):
    spec = importlib.util.spec_from_file_location(
        f"custom_components.timezone_change.{mod}", ROOT / f"{mod}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

helpers = sys.modules["custom_components.timezone_change.helpers"]

now = datetime(2026, 9, 19, 14, 0, tzinfo=timezone.utc)
data = helpers.build_timezone_data("Europe/Lisbon", "Europe/Lisbon", now)
assert data.timezone == "Europe/Lisbon"
assert data.next_transition is not None
assert data.next_transition.year == 2026
assert data.next_transition.month == 10
assert data.transition_delta_seconds == -3600
assert helpers.format_offset(3600) == "UTC+01:00"
assert helpers.format_offset(-18000) == "UTC-05:00"
print("Helper tests passed")
print("Next Lisbon transition UTC:", data.next_transition.isoformat())
