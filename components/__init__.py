"""Compatibility package for Streamlit imports.

Streamlit Cloud executes `dashboard/app.py` but may resolve imports from repo root.
We keep a thin `components` package at repo root to avoid import-path surprises.
"""

