from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_dashboard_design():
    dashboard_design_path = (
        Path(__file__).resolve().parent.parent / "dashboard" / "components" / "design.py"
    )
    if not dashboard_design_path.is_file():
        raise ImportError(f"dashboard design not found at {dashboard_design_path}")

    module_name = "_pg_dashboard_components_design"
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, dashboard_design_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load dashboard design from {dashboard_design_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_design = _load_dashboard_design()

_export_names: list[str] = []
for _name in dir(_design):
    if _name.isupper():
        globals()[_name] = getattr(_design, _name)
        _export_names.append(_name)

__all__ = sorted(_export_names)

