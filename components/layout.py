from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_dashboard_layout():
    dashboard_layout_path = (
        Path(__file__).resolve().parent.parent / "dashboard" / "components" / "layout.py"
    )
    if not dashboard_layout_path.is_file():
        raise ImportError(f"dashboard layout not found at {dashboard_layout_path}")

    module_name = "_pg_dashboard_components_layout"
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, dashboard_layout_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load dashboard layout from {dashboard_layout_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_layout = _load_dashboard_layout()

auth_footer = getattr(_layout, "auth_footer")
auth_hero = getattr(_layout, "auth_hero")
inject_global_styles = getattr(_layout, "inject_global_styles")
render_authenticated_sidebar = getattr(_layout, "render_authenticated_sidebar")

__all__ = [
    "auth_footer",
    "auth_hero",
    "inject_global_styles",
    "render_authenticated_sidebar",
]

