"""Global Streamlit CSS — aligned with site/styles.css (Kredesolutions marketing)."""

from components.design import (
    BG,
    BORDER,
    PRIMARY,
    PRIMARY_DARK,
    PRIMARY_SOFT,
    RADIUS,
    RADIUS_LG,
    RADIUS_XL,
    SHADOW,
    SHADOW_MD,
    SHADOW_SM,
    SURFACE,
    TEXT,
    TEXT_MUTED,
    TEXT_SUBTLE,
)


def build_global_css() -> str:
    return f"""
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {{
      --pg-primary: {PRIMARY};
      --pg-primary-dark: {PRIMARY_DARK};
      --pg-primary-soft: {PRIMARY_SOFT};
      --pg-bg: {BG};
      --pg-surface: {SURFACE};
      --pg-border: {BORDER};
      --pg-text: {TEXT};
      --pg-text-muted: {TEXT_MUTED};
      --pg-radius: {RADIUS};
      --pg-radius-lg: {RADIUS_LG};
      --pg-shadow-sm: {SHADOW_SM};
      --pg-shadow-md: {SHADOW_MD};
    }}

    html, body, [class*="css"] {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      -webkit-font-smoothing: antialiased;
    }}

    .stApp {{
      background-color: {BG};
      color: {TEXT};
    }}

    #MainMenu, footer {{
      visibility: hidden;
      height: 0;
      min-height: 0;
      overflow: hidden;
    }}

    header[data-testid="stHeader"] {{
      visibility: hidden;
      height: 0;
      min-height: 0;
      overflow: hidden;
    }}

    [data-testid="stSidebarCollapseButton"],
    [data-testid="stExpandSidebarButton"] {{
      display: none !important;
    }}

    .block-container {{
      padding-top: 1.75rem;
      padding-bottom: 2.5rem;
      max-width: 1100px;
    }}

    /* Typography */
    h1, h2, h3, h4, h5, h6 {{
      color: {TEXT};
      letter-spacing: -0.02em;
    }}

    h1 {{
      font-weight: 700 !important;
      font-size: 1.75rem !important;
    }}

    h2, h3 {{
      font-weight: 600 !important;
    }}

    [data-testid="stCaptionContainer"], .stCaption {{
      color: {TEXT_MUTED} !important;
    }}

    /* Sidebar — background, typography, nav styling only */
    [data-testid="stSidebar"] {{
      background: {SURFACE};
      border-right: 1px solid {BORDER};
      transform: none !important;
      max-width: none !important;
    }}

    [data-testid="stSidebar"] > div:first-child {{
      padding: 1.25rem 1rem 1.5rem;
      display: flex;
      flex-direction: column;
      min-height: 100%;
    }}

    [data-testid="stSidebarHeader"] {{
      padding: 0.5rem 0.75rem 0;
      background: transparent;
    }}

    [data-testid="stSidebarHeader"] img {{
      display: none;
    }}

    [data-testid="stSidebarUserContent"] {{
      padding-top: 0.25rem;
    }}

    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
      gap: 0.25rem;
    }}

    [data-testid="stSidebar"] hr,
    [data-testid="stSidebar"] [data-testid="stDivider"] {{
      margin: 0.85rem 0;
      border: none;
      border-top: 1px solid {BORDER};
    }}

    /* Brand header */
    .pg-sidebar-brand {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0 0.25rem 1rem;
      margin-bottom: 0.25rem;
      border-bottom: 1px solid {BORDER};
    }}

    .pg-sidebar-brand-mark img,
    .pg-sidebar-brand-mark svg {{
      display: block;
      height: 36px;
      width: auto;
      flex-shrink: 0;
    }}

    .pg-sidebar-brand-text {{
      display: flex;
      flex-direction: column;
      gap: 0.1rem;
      min-width: 0;
    }}

    .pg-sidebar-brand-name {{
      font-size: 0.95rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: {TEXT};
      line-height: 1.2;
    }}

    .pg-sidebar-brand-product {{
      font-size: 0.72rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: {TEXT_MUTED};
    }}

    /* Account card */
    .pg-sidebar-account {{
      margin: 0.75rem 0 1rem;
      padding: 0.75rem;
      background: {BG};
      border: 1px solid {BORDER};
      border-radius: {RADIUS};
    }}

    .pg-sidebar-account-row {{
      display: flex;
      align-items: center;
      gap: 0.65rem;
      min-width: 0;
    }}

    .pg-sidebar-avatar {{
      flex-shrink: 0;
      width: 2rem;
      height: 2rem;
      border-radius: 999px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.8rem;
      font-weight: 700;
      color: {PRIMARY_DARK};
      background: {PRIMARY_SOFT};
      border: 1px solid #BFDBFE;
    }}

    .pg-sidebar-account-meta {{
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
      min-width: 0;
    }}

    .pg-sidebar-account-email {{
      font-size: 0.8125rem;
      font-weight: 600;
      color: {TEXT};
      line-height: 1.3;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}

    .pg-sidebar-account-company {{
      font-size: 0.75rem;
      font-weight: 500;
      color: {TEXT_MUTED};
      line-height: 1.3;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}

    .pg-sidebar-admin-badge {{
      display: inline-block;
      margin-top: 0.55rem;
      padding: 0.15rem 0.5rem;
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: {PRIMARY_DARK};
      background: {PRIMARY_SOFT};
      border-radius: 999px;
      border: 1px solid #BFDBFE;
    }}

    /* Nav section */
    .pg-sidebar-label {{
      margin: 0.5rem 0 0.4rem;
      padding: 0 0.25rem 0 0.65rem;
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: {TEXT_SUBTLE};
    }}

    /* Collapsed st.radio labels still render a widget label node — hide it */
    [data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] .stRadio > label[data-testid="stWidgetLabel"] {{
      display: none !important;
      height: 0 !important;
      min-height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: hidden !important;
      border: none !important;
    }}

    [data-testid="stSidebar"] [data-testid="stElementContainer"]:has([data-testid="stRadio"]),
    [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.stRadio) {{
      margin-top: 0 !important;
      margin-bottom: 0 !important;
    }}

    [data-testid="stSidebar"] [data-testid="stRadio"],
    [data-testid="stSidebar"] .stRadio {{
      margin: 0;
      padding: 0;
    }}

    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"],
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] {{
      gap: 0.125rem;
      margin: 0;
      padding: 0;
    }}

    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label {{
      display: flex;
      align-items: center;
      padding: 0.5rem 0.65rem;
      margin: 0;
      border-radius: 8px;
      border-left: 3px solid transparent;
      font-size: 0.875rem;
      font-weight: 500;
      color: {TEXT_MUTED};
      cursor: pointer;
      transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
    }}

    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:hover,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover {{
      background: {BG};
      color: {TEXT};
    }}

    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label[data-checked="true"],
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked),
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) {{
      background: {PRIMARY_SOFT};
      color: {PRIMARY_DARK};
      font-weight: 600;
      border-left-color: {PRIMARY};
    }}

    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] input[type="radio"],
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] input[type="radio"] {{
      position: absolute;
      opacity: 0;
      width: 0;
      height: 0;
      pointer-events: none;
    }}

    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label > div:first-child,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label > div:first-child {{
      display: none !important;
    }}

    /* Push logout toward bottom */
    .pg-sidebar-spacer {{
      flex: 1 1 auto;
      min-height: 1.5rem;
    }}

    [data-testid="stSidebar"] .stButton > button {{
      border-radius: {RADIUS};
      font-weight: 600;
      font-size: 0.875rem;
      padding: 0.5rem 0.75rem;
      border: 1px solid {BORDER};
      background: {SURFACE};
      color: {TEXT_MUTED};
      transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
    }}

    [data-testid="stSidebar"] .stButton > button:hover {{
      background: #FEF2F2;
      border-color: #FECACA;
      color: #B91C1C;
    }}

    [data-testid="stSidebar"] [data-testid="stExpander"] {{
      margin-top: 0.125rem;
      border: 1px solid {BORDER};
      border-radius: {RADIUS};
      background: {BG};
      overflow: hidden;
    }}

    [data-testid="stSidebar"] [data-testid="stExpander"] summary {{
      font-size: 0.875rem;
      font-weight: 600;
      color: {TEXT_MUTED};
      padding: 0.5rem 0.65rem;
      border-left: 3px solid transparent;
      transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
    }}

    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {{
      background: {BG};
      color: {TEXT};
    }}

    [data-testid="stSidebar"] [data-testid="stExpander"]:has(
      [data-testid="stRadio"] label:has(input:checked)
    ) {{
      border-color: #BFDBFE;
      background: {PRIMARY_SOFT};
    }}

    [data-testid="stSidebar"] [data-testid="stExpander"]:has(
      [data-testid="stRadio"] label:has(input:checked)
    ) summary {{
      color: {PRIMARY_DARK};
      font-weight: 600;
      border-left-color: {PRIMARY};
      background: transparent;
    }}

    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
      padding-top: 0 !important;
    }}

    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stVerticalBlock"] {{
      gap: 0;
      padding: 0 0 0.2rem;
    }}

    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stElementContainer"]:has(
      [data-testid="stRadio"]
    ) {{
      margin-top: 0 !important;
      margin-bottom: 0 !important;
    }}

    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stRadio"] [role="radiogroup"] label,
    [data-testid="stSidebar"] [data-testid="stExpander"] .stRadio [role="radiogroup"] > label {{
      padding-left: 1.15rem;
      font-size: 0.8125rem;
    }}

    /* Buttons */
    .stButton > button {{
      border-radius: {RADIUS};
      font-weight: 600;
      font-size: 0.9rem;
      padding: 0.45rem 1rem;
      transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
    }}

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {{
      background: {PRIMARY};
      border: 1px solid {PRIMARY};
      color: #fff;
      box-shadow: {SHADOW_SM};
    }}

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {{
      background: {PRIMARY_DARK};
      border-color: {PRIMARY_DARK};
      color: #fff;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }}

    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="baseButton-secondary"] {{
      background: {SURFACE};
      border: 1px solid {BORDER};
      color: {TEXT};
    }}

    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="baseButton-secondary"]:hover {{
      background: {BG};
      border-color: #CBD5E1;
    }}

    .stLinkButton > a {{
      border-radius: {RADIUS} !important;
      font-weight: 600 !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
      gap: 0.35rem;
      background: transparent;
      border-bottom: 1px solid {BORDER};
    }}

    .stTabs [data-baseweb="tab"] {{
      border-radius: 8px 8px 0 0;
      padding: 0.5rem 1rem;
      font-weight: 600;
      font-size: 0.9rem;
      color: {TEXT_MUTED};
      background: transparent;
    }}

    .stTabs [aria-selected="true"] {{
      color: {PRIMARY} !important;
      background: {PRIMARY_SOFT} !important;
    }}

    .stTabs [data-baseweb="tab-panel"] {{
      padding-top: 1.25rem;
    }}

    /* Forms */
    [data-testid="stForm"] {{
      border: 1px solid {BORDER};
      border-radius: {RADIUS_LG};
      padding: 1.25rem 1.35rem;
      background: {SURFACE};
      box-shadow: {SHADOW_SM};
    }}

    /* Inputs */
    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    .stDateInput input,
    .stTimeInput input {{
      border-radius: 8px !important;
      border-color: {BORDER} !important;
      font-size: 0.95rem;
    }}

    .stTextInput input:focus,
    .stTextArea textarea:focus {{
      border-color: {PRIMARY} !important;
      box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15) !important;
    }}

    div[data-baseweb="select"] > div {{
      border-radius: 8px !important;
    }}

    /* Cards / bordered containers */
    [data-testid="stVerticalBlockBorderWrapper"] {{
      border-radius: {RADIUS_LG} !important;
      border-color: {BORDER} !important;
      background: {SURFACE};
      box-shadow: {SHADOW_SM};
      padding: 0.25rem 0.5rem;
    }}

    /* Metrics */
    [data-testid="stMetric"] {{
      background: {SURFACE};
      border: 1px solid {BORDER};
      border-radius: {RADIUS_LG};
      padding: 0.9rem 1rem;
      box-shadow: {SHADOW};
    }}

    [data-testid="stMetricLabel"] {{
      font-size: 0.72rem !important;
      font-weight: 600 !important;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: {TEXT_MUTED} !important;
    }}

    [data-testid="stMetricValue"] {{
      font-size: 1.65rem !important;
      font-weight: 700 !important;
      color: {TEXT} !important;
      letter-spacing: -0.02em;
    }}

    /* Expanders */
    [data-testid="stExpander"] {{
      border: 1px solid {BORDER};
      border-radius: {RADIUS_LG};
      background: {SURFACE};
      box-shadow: {SHADOW_SM};
    }}

    [data-testid="stExpander"] summary {{
      font-weight: 600;
      font-size: 0.95rem;
    }}

    /* Alerts */
    [data-testid="stAlert"] {{
      border-radius: {RADIUS};
      border: 1px solid {BORDER};
    }}

    /* Dividers */
    hr {{
      border-color: {BORDER};
      margin: 1.25rem 0;
    }}

    /* Code blocks */
    code {{
      background: {BG};
      color: {TEXT};
      border: 1px solid {BORDER};
      border-radius: 6px;
      padding: 0.1rem 0.35rem;
      font-size: 0.85em;
    }}

    /* Custom page components */
    .pg-page-header {{
      margin-bottom: 1.5rem;
    }}

    .pg-page-eyebrow {{
      margin: 0 0 0.35rem;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: {PRIMARY};
    }}

    .pg-page-title {{
      margin: 0 0 0.4rem;
      font-size: 1.75rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: {TEXT};
      line-height: 1.2;
    }}

    .pg-page-subtitle {{
      margin: 0;
      font-size: 1rem;
      color: {TEXT_MUTED};
      line-height: 1.5;
      max-width: 56ch;
    }}

    .pg-section-title {{
      margin: 1.5rem 0 0.5rem;
      font-size: 1.1rem;
      font-weight: 600;
      color: {TEXT};
      letter-spacing: -0.01em;
    }}

    .pg-status-badge {{
      display: inline-block;
      padding: 0.15rem 0.55rem;
      border-radius: 999px;
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}

    [data-testid="stVerticalBlockBorderWrapper"]:has(.pg-auth-hero) {{
      padding: 1.75rem 1.75rem 1.25rem !important;
      border-radius: {RADIUS_XL} !important;
      box-shadow: {SHADOW_MD} !important;
      background: {SURFACE};
    }}

    [data-testid="stVerticalBlockBorderWrapper"]:has(.pg-auth-hero) [data-testid="stForm"] {{
      border: none;
      box-shadow: none;
      padding: 0;
      background: transparent;
    }}

    .pg-auth-shell {{
      background: {SURFACE};
      border: 1px solid {BORDER};
      border-radius: {RADIUS_XL};
      padding: 2rem 2rem 1.5rem;
      box-shadow: {SHADOW_MD};
    }}

    .pg-auth-hero {{
      text-align: center;
      margin-bottom: 1.25rem;
    }}

    .pg-brand {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.625rem;
      margin-bottom: 1.25rem;
      font-weight: 700;
      font-size: 1.05rem;
      letter-spacing: -0.02em;
      color: {TEXT};
    }}

    .pg-brand img,
    .pg-brand svg {{
      display: block;
      height: 36px;
      width: auto;
      flex-shrink: 0;
    }}

    .pg-hero-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.35rem 0.85rem;
      margin-bottom: 1rem;
      background: {BG};
      border: 1px solid {BORDER};
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 600;
      color: {TEXT_MUTED};
      box-shadow: {SHADOW_SM};
    }}

    .pg-hero-badge-dot {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #22c55e;
      flex-shrink: 0;
    }}

    .pg-auth-title {{
      margin: 0 0 0.5rem;
      font-size: 1.5rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: {TEXT};
    }}

    .pg-auth-lead {{
      margin: 0;
      font-size: 0.95rem;
      color: {TEXT_MUTED};
      line-height: 1.55;
    }}

    .pg-auth-footer {{
      display: block;
      margin-top: 1.25rem;
      text-align: center;
      font-size: 0.85rem;
      color: {TEXT_SUBTLE};
    }}

    .pg-workflow-step--active {{
      border-color: #BFDBFE !important;
      box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.12);
    }}

    @media (max-width: 768px) {{
      .block-container {{
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
      }}

      .pg-auth-shell {{
        padding: 1.5rem 1.25rem 1.25rem;
      }}

      .pg-page-title {{
        font-size: 1.45rem;
      }}
    }}
    """
