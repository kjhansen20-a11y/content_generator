import streamlit as st

from api_client import ApiClient, ApiError
from components.layout import page_header


POST_TYPE_LABELS = {
    "professional": "Professional / Educational → Company Page",
    "personal": "Personal / Founder → Your profile",
}


def _account_kind_label(account: dict) -> str:
    kind = account.get("account_type") or "account"
    if kind == "profile":
        return "Personal profile"
    if kind == "organization":
        return "Company Page"
    if kind == "page":
        return "Facebook Page"
    return kind.replace("_", " ").title()


def _render_facebook_page_picker(client: ApiClient, token: str, company_id: int) -> None:
    pending_id = st.session_state.get("facebook_pending_id")
    if not pending_id:
        return

    with st.container(border=True):
        st.subheader("Choose your Facebook Page")
        st.caption(
            "Select the Page you manage — only Pages on the account you signed in with are listed."
        )
        try:
            pages = client.list_facebook_pending_pages(token, company_id, pending_id)
        except ApiError as exc:
            st.error(str(exc))
            st.session_state.pop("facebook_pending_id", None)
            return

        if not pages:
            st.warning("No pages available. Try connecting Facebook again.")
            return

        labels = {p["name"]: p["id"] for p in pages}
        choice = st.selectbox("Facebook Page", options=list(labels.keys()), key="fb_page_choice")
        if st.button("Connect this Page", type="primary", key="confirm_fb_page"):
            try:
                account = client.complete_facebook_page(
                    token, company_id, pending_id, labels[choice]
                )
                st.session_state.pop("facebook_pending_id", None)
                st.session_state.pop("oauth_authorize_url", None)
                st.success(f"Connected Facebook Page **{account['account_name']}**.")
                st.rerun()
            except ApiError as exc:
                st.error(str(exc))


def render_connections(
    client: ApiClient,
    token: str,
    company_id: int,
    can_edit: bool,
    user_email: str,
) -> None:
    page_header(
        "Connections",
        "Link your LinkedIn profile and Facebook Page so Post Generator can publish on your behalf.",
    )

    _render_facebook_page_picker(client, token, company_id)

    try:
        accounts = client.list_connected_accounts(token, company_id)
        oauth_status = client.oauth_status()
    except ApiError as exc:
        st.error(str(exc))
        return

    real_accounts = [a for a in accounts if not a.get("is_mock") and a.get("status") == "active"]
    my_accounts = [a for a in real_accounts if a.get("connected_by_email") == user_email]
    team_accounts = [a for a in real_accounts if a.get("connected_by_email") != user_email]

    st.subheader("Your connections")
    if my_accounts:
        for account in my_accounts:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f"**{account['platform'].title()}** — {account['account_name']} "
                    f"({_account_kind_label(account)})"
                )
            with col2:
                if can_edit and st.button("Disconnect", key=f"disconnect_{account['id']}"):
                    try:
                        client.disconnect_account(token, company_id, account["id"])
                        st.success("Disconnected.")
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))
    else:
        st.info("You have not connected any accounts yet. Use the cards below to get started.")

    if team_accounts:
        st.subheader("Team connections")
        st.caption("Other members of your company have connected these accounts.")
        for account in team_accounts:
            owner = account.get("connected_by_email") or "teammate"
            kind = _account_kind_label(account)
            st.markdown(
                f"- **{account['platform'].title()}** — {account['account_name']} ({kind}) · {owner}"
            )

    if not can_edit:
        st.caption("You have read-only access. An editor can connect accounts.")
        return

    if not oauth_status.get("linkedin_configured"):
        with st.expander("Platform setup: enable LinkedIn (one-time, for admins)", expanded=True):
            st.markdown(
                """
1. Open [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps) → **Create app**
2. Link it to a **LinkedIn Company Page** you admin (required by LinkedIn)
3. **Products** tab — add:
   - **Sign In with LinkedIn using OpenID Connect**
   - **Share on LinkedIn**
   - **Community Management API** (required for Company Page posts)
4. **Auth** tab — add this redirect URL (must match exactly):
                """
            )
            st.code(oauth_status.get("linkedin_redirect_uri", ""), language=None)
            privacy_url = oauth_status.get("privacy_policy_url", "")
            if privacy_url:
                st.markdown("5. **Privacy policy URL** (required by LinkedIn):")
                st.code(privacy_url, language=None)
                st.caption("Hosted automatically at `/privacy` on your API domain once deployed.")
            st.markdown(
                """
6. Copy **Client ID** and **Client Secret** into `backend/.env`:
   ```
   LINKEDIN_CLIENT_ID=...
   LINKEDIN_CLIENT_SECRET=...
   ```
7. Restart the API, then refresh this page.

**Scopes:** """ + oauth_status.get("linkedin_scopes", "")
            )
            st.caption(
                "After connecting, professional posts publish to your LinkedIn Company Page "
                "(e.g. KJSolution). Personal posts publish from your personal profile."
            )

    if not oauth_status.get("linkedin_configured") and not oauth_status.get("facebook_configured"):
        st.divider()

    st.divider()
    st.subheader("Connect an account")
    st.caption(
        "You will sign in on LinkedIn or Facebook with **your own** account. "
        "Each team member connects their own profile or Page."
    )

    col_li, col_fb = st.columns(2)

    with col_li:
        with st.container(border=True):
            st.markdown("#### LinkedIn")
            st.caption(
                "Connect once — we detect your personal profile and any Company Pages you admin."
            )
            linkedin_profile = any(
                a["platform"] == "linkedin"
                and a.get("connected_by_email") == user_email
                and a.get("account_type") == "profile"
                for a in my_accounts
            )
            linkedin_pages = [
                a for a in my_accounts
                if a["platform"] == "linkedin"
                and a.get("connected_by_email") == user_email
                and a.get("account_type") == "organization"
            ]
            if linkedin_profile:
                st.success("LinkedIn personal profile connected.")
            if linkedin_pages:
                names = ", ".join(a["account_name"] for a in linkedin_pages)
                st.success(f"LinkedIn Company Page(s): **{names}**")
            if linkedin_profile or linkedin_pages:
                pass
            elif oauth_status.get("linkedin_configured"):
                if st.button("Connect LinkedIn", key="connect_linkedin", use_container_width=True):
                    try:
                        result = client.oauth_start(token, company_id, "linkedin", "profile")
                        st.session_state["oauth_authorize_url"] = result["authorization_url"]
                        st.session_state.pop("facebook_pending_id", None)
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))
            else:
                st.button("Connect LinkedIn", disabled=True, use_container_width=True)
                st.caption("Not available — platform admin must enable LinkedIn OAuth.")

    with col_fb:
        with st.container(border=True):
            st.markdown("#### Facebook")
            st.caption("Connect a Facebook Page you manage.")
            facebook_connected = any(
                a["platform"] == "facebook" and a.get("connected_by_email") == user_email
                for a in my_accounts
            )
            if facebook_connected:
                st.success("Your Facebook Page is connected.")
            elif oauth_status.get("facebook_configured"):
                if st.button("Connect Facebook Page", key="connect_facebook", use_container_width=True):
                    try:
                        result = client.oauth_start(token, company_id, "facebook", "page")
                        st.session_state["oauth_authorize_url"] = result["authorization_url"]
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))
            else:
                st.button("Connect Facebook Page", disabled=True, use_container_width=True)
                st.caption("Not available — platform admin must enable Facebook OAuth.")

    auth_url = st.session_state.get("oauth_authorize_url")
    if auth_url:
        st.link_button(
            "Continue — sign in on LinkedIn or Facebook →",
            auth_url,
            type="primary",
            use_container_width=True,
        )
        st.caption("A new tab opens. Complete sign-in there, then return to this page.")
