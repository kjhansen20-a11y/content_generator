from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_dashboard_theme():
    dashboard_theme_path = Path(__file__).resolve().parent.parent / "dashboard" / "styles" / "theme.py"
    if not dashboard_theme_path.is_file():
        raise ImportError(f"dashboard theme not found at {dashboard_theme_path}")

    module_name = "_pg_dashboard_styles_theme"
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, dashboard_theme_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load dashboard theme from {dashboard_theme_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_theme = _load_dashboard_theme()

build_global_css = getattr(_theme, "build_global_css")

__all__ = ["build_global_css"]

