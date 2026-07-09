import os
import sys
import time
from pathlib import Path

# Ensure dashboard/ is on sys.path (Streamlit Cloud hot-reloads can drop it).
_DASHBOARD_DIR = Path(__file__).resolve().parent
if str(_DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD_DIR))

import extra_streamlit_components as stx
import streamlit as st

from api_client import ApiClient, ApiError
from components.layout import auth_hero, inject_global_styles
from views.admin import render_admin_dashboard
from views.brand_profile import render_brand_profile
from views.company_profile import render_company_profile
from views.generate import render_generate_post
from views.home import render_home_dashboard
from views.marketing_plan import render_marketing_plan
from views.connections import render_connections
from views.publishing import render_previous_posts, render_publishing_queue

st.set_page_config(page_title="Post Generator", page_icon="📅", layout="wide", initial_sidebar_state="expanded")
inject_global_styles()

TOKEN_COOKIE = "pg_token"
EDIT_ROLES = {"owner", "admin", "editor"}

def _default_api_base() -> str:
    env_url = os.environ.get("POST_GENERATOR_API_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")
    try:
        return str(st.secrets["POST_GENERATOR_API_URL"]).rstrip("/")
    except (KeyError, FileNotFoundError, AttributeError):
        return "http://127.0.0.1:8001"


# Prefer env/secrets on each run so local POST_GENERATOR_API_URL overrides stale session state.
st.session_state.api_base = _default_api_base()

client = ApiClient(st.session_state.api_base)
cookie_manager = stx.CookieManager(key="cookie_manager")

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "companies" not in st.session_state:
    st.session_state.companies = []
if "selected_company_id" not in st.session_state:
    st.session_state.selected_company_id = None
if "page" not in st.session_state:
    st.session_state.page = "Home"
if st.session_state.page == "Knowledge Base":
    st.session_state.page = "Company Profile"
if "block_cookie_login" not in st.session_state:
    st.session_state.block_cookie_login = False
if "logged_out" not in st.session_state:
    st.session_state.logged_out = False


def load_profile(token: str) -> None:
    profile = client.me(token)
    previous_user_id = (st.session_state.user or {}).get("id")
    st.session_state.user = profile["user"]
    st.session_state.companies = profile.get("companies", [])
    if previous_user_id != st.session_state.user.get("id"):
        st.session_state.selected_company_id = None
    if st.session_state.companies and st.session_state.selected_company_id is None:
        st.session_state.selected_company_id = st.session_state.companies[0]["id"]


def set_session(token: str) -> None:
    st.session_state.logged_out = False
    st.session_state.block_cookie_login = False
    st.session_state.cookie_retries = 0
    st.session_state.cookies_ready = False
    st.session_state.pop("cookie_sync_phase", None)
    st.session_state.token = token
    st.session_state.user = None
    st.session_state.companies = []
    st.session_state.selected_company_id = None
    st.session_state.pop("company_select", None)


def _perform_logout() -> None:
    """Run at script start before nav widgets so session keys can be reset safely."""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.companies = []
    st.session_state.selected_company_id = None
    st.session_state.logged_out = True
    st.session_state.block_cookie_login = True
    st.session_state.page = "Home"
    st.session_state.pop("company_select", None)
    st.session_state.pop("nav_pending", None)
    st.session_state.pop("cookie_sync_phase", None)
    cookie_manager.delete(TOKEN_COOKIE, key="delete_token")


def _wait_for_cookies(cookies: dict) -> None:
    """CookieManager returns {} until the browser component hydrates."""
    if cookies:
        st.session_state.cookies_ready = True
        return
    if st.session_state.get("cookies_ready"):
        return
    retries = st.session_state.get("cookie_retries", 0)
    if retries < 3:
        st.session_state.cookie_retries = retries + 1
        time.sleep(0.3)
        st.rerun()
    st.session_state.cookies_ready = True


def _clear_auth_cookie() -> None:
    if cookies.get(TOKEN_COOKIE):
        cookie_manager.delete(TOKEN_COOKIE, key="delete_token")
        st.rerun()


def _ensure_auth_cookie() -> None:
    """Keep browser cookie aligned with session token (delete requires a rerun before set)."""
    token = st.session_state.token
    if not token:
        st.session_state.pop("cookie_sync_phase", None)
        return

    cookie_token = cookies.get(TOKEN_COOKIE)
    if cookie_token == token:
        st.session_state.pop("cookie_sync_phase", None)
        return

    phase = st.session_state.get("cookie_sync_phase")
    if phase == "await_set":
        cookie_manager.set(TOKEN_COOKIE, token, key="set_token")
        st.session_state.pop("cookie_sync_phase", None)
        return

    if cookie_token and cookie_token != token:
        cookie_manager.delete(TOKEN_COOKIE, key="clear_token_before_set")
        st.session_state["cookie_sync_phase"] = "await_set"
        st.rerun()

    cookie_manager.set(TOKEN_COOKIE, token, key="set_token")


if st.session_state.pop("logout_requested", False):
    _perform_logout()
    st.rerun()

cookies = cookie_manager.get_all(key="cookies_get_all")
_wait_for_cookies(cookies)

if st.session_state.logged_out or st.session_state.block_cookie_login:
    _clear_auth_cookie()
    if st.session_state.block_cookie_login:
        st.session_state.block_cookie_login = False


def request_logout() -> None:
    st.session_state.logout_requested = True


def selected_company() -> dict | None:
    company_id = st.session_state.selected_company_id
    if company_id is None:
        return None
    for company in st.session_state.companies:
        if company["id"] == company_id:
            return company
    return None


def can_edit_company(company: dict | None) -> bool:
    return company is not None and company.get("role") in EDIT_ROLES


def _handle_oauth_callback() -> None:
    oauth_result = st.query_params.get("oauth")
    if not oauth_result:
        return
    platform = st.query_params.get("platform", "account")
    if oauth_result == "success":
        account = st.query_params.get("account", platform)
        st.success(f"Connected **{account}** on {platform.title()}.")
        st.session_state["nav_pending"] = "Connections"
    elif oauth_result == "pick_page":
        st.session_state["facebook_pending_id"] = st.query_params.get("pending_id")
        st.session_state["nav_pending"] = "Connections"
        st.info("Choose which Facebook Page to connect below.")
    elif oauth_result == "error":
        message = st.query_params.get("message", "Authorization failed.")
        st.error(f"{platform.title()} connection failed: {message}")
    st.query_params.clear()


if not st.session_state.token and not st.session_state.logged_out and not st.session_state.block_cookie_login:
    saved_token = cookies.get(TOKEN_COOKIE)
    if saved_token:
        try:
            load_profile(saved_token)
            st.session_state.token = saved_token
        except ApiError:
            cookie_manager.delete(TOKEN_COOKIE, key="delete_stale_token")

if st.session_state.token:
    _ensure_auth_cookie()
    if st.session_state.user is None:
        load_profile(st.session_state.token)

try:
    health = client.health()
    api_ok = health.get("status", "unknown")
except ApiError:
    api_ok = "offline"

if st.session_state.token:
    if api_ok != "ok":
        st.error(f"Cannot reach API at {st.session_state.api_base}. Start the backend first.")
        st.stop()

    with st.sidebar.expander("Account", expanded=False):
        st.caption(st.session_state.user["email"])
        if st.session_state.companies:
            st.caption(st.session_state.companies[0]["name"])
        if st.session_state.user.get("is_platform_admin"):
            st.caption("Platform admin")

    if st.session_state.companies:
        st.session_state.selected_company_id = st.session_state.companies[0]["id"]

        st.sidebar.divider()
        nav_options = [
            "Home",
            "Company Profile",
            "Brand Profile",
            "Marketing Plan",
            "Generate Post",
            "Connections",
            "Publishing Queue",
            "Previous Posts",
        ]
        if st.session_state.user.get("is_platform_admin"):
            nav_options.append("Admin Dashboard")
        if st.session_state.get("page") not in nav_options:
            st.session_state.pop("page", None)
        pending_nav = st.session_state.pop("nav_pending", None)
        if pending_nav and pending_nav in nav_options:
            st.session_state.page = pending_nav
        elif "page" not in st.session_state:
            st.session_state.page = nav_options[0]
        st.sidebar.radio("Navigation", nav_options, key="page")

    st.sidebar.divider()
    st.sidebar.button("Log out", key="logout_button", use_container_width=True, on_click=request_logout)

    company = selected_company()

    _handle_oauth_callback()

    if st.session_state.page == "Home":
        if company:
            render_home_dashboard(client, st.session_state.token, company, can_edit_company(company))
        else:
            st.warning("No companies linked to this account yet.")

    elif st.session_state.page == "Company Profile":
        if company:
            render_company_profile(client, st.session_state.token, company["id"], can_edit_company(company))
        else:
            st.warning("Select a company first.")

    elif st.session_state.page == "Brand Profile":
        if company:
            render_brand_profile(client, st.session_state.token, company["id"], can_edit_company(company))
        else:
            st.warning("Select a company first.")

    elif st.session_state.page == "Marketing Plan":
        if company:
            render_marketing_plan(
                client,
                st.session_state.token,
                company["id"],
                can_edit_company(company),
            )
        else:
            st.warning("Select a company first.")

    elif st.session_state.page == "Generate Post":
        if company:
            render_generate_post(client, st.session_state.token, company["id"], can_edit_company(company))
        else:
            st.warning("Select a company first.")

    elif st.session_state.page == "Connections":
        if company:
            render_connections(
                client,
                st.session_state.token,
                company["id"],
                can_edit_company(company),
                user_email=st.session_state.user["email"],
            )
        else:
            st.warning("Select a company first.")

    elif st.session_state.page == "Publishing Queue":
        if company:
            render_publishing_queue(
                client,
                st.session_state.token,
                company["id"],
                can_edit_company(company),
                company_name=company["name"],
            )
        else:
            st.warning("Select a company first.")

    elif st.session_state.page == "Previous Posts":
        if company:
            render_previous_posts(
                client,
                st.session_state.token,
                company["id"],
                company_name=company["name"],
            )
        else:
            st.warning("Select a company first.")

    elif st.session_state.page == "Admin Dashboard":
        render_admin_dashboard(client, st.session_state.token)

else:
    if api_ok != "ok":
        st.error(f"Cannot reach API at {st.session_state.api_base}. Start the backend first.")
        st.stop()

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        auth_hero()
        tab_login, tab_register = st.tabs(["Log in", "Register"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)

            if submitted:
                try:
                    result = client.login(email.strip(), password)
                    set_session(result["access_token"])
                    load_profile(result["access_token"])
                    st.rerun()
                except ApiError as exc:
                    st.error(str(exc))

        with tab_register:
            with st.form("register_form"):
                reg_email = st.text_input("Email", key="reg_email")
                reg_password = st.text_input("Password", type="password", key="reg_password")
                company_name = st.text_input("Company name")
                reg_submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)

            if reg_submitted:
                try:
                    result = client.register(reg_email.strip(), reg_password, company_name.strip())
                    set_session(result["access_token"])
                    load_profile(result["access_token"])
                    st.rerun()
                except ApiError as exc:
                    st.error(str(exc))
