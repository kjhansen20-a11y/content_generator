"""HTTP client for the FastAPI backend."""

from __future__ import annotations

from typing import Any

import requests

DEFAULT_API_BASE = "http://127.0.0.1:8001"


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    def __init__(self, base_url: str = DEFAULT_API_BASE) -> None:
        self.base_url = base_url.rstrip("/")

    def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> Any:
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = requests.request(
            method,
            f"{self.base_url}{path}",
            json=json,
            params=params,
            headers=headers,
            timeout=timeout,
        )

        if response.status_code >= 400:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except Exception:
                pass
            raise ApiError(str(detail), response.status_code)

        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def health(self) -> dict[str, str]:
        return self._request("GET", "/health")

    def register(self, email: str, password: str, company_name: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v1/auth/register",
            json={"email": email, "password": password, "company_name": company_name},
        )

    def login(self, email: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )

    def me(self, token: str) -> dict[str, Any]:
        return self._request("GET", "/api/v1/auth/me", token=token)

    def get_company_profile(self, token: str, company_id: int) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/companies/{company_id}/profile", token=token)

    def update_company_profile(
        self, token: str, company_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            "PUT",
            f"/api/v1/companies/{company_id}/profile",
            token=token,
            json=payload,
        )

    def get_brand_profile(self, token: str, company_id: int) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/companies/{company_id}/brand", token=token)

    def update_brand_profile(
        self, token: str, company_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            "PUT",
            f"/api/v1/companies/{company_id}/brand",
            token=token,
            json=payload,
        )

    def generate_post(self, token: str, company_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/companies/{company_id}/generate",
            token=token,
            json=payload,
            timeout=180,
        )

    def get_week_slots(
        self, token: str, company_id: int, week: str | None = None
    ) -> dict[str, Any]:
        params = {"week": week} if week else None
        return self._request(
            "GET",
            f"/api/v1/companies/{company_id}/marketing-plans/week-slots",
            token=token,
            params=params,
        )

    def list_calendar(self, token: str, company_id: int) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/companies/{company_id}/calendar", token=token)

    def update_calendar_item(
        self, token: str, company_id: int, item_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            "PUT",
            f"/api/v1/companies/{company_id}/calendar/{item_id}",
            token=token,
            json=payload,
        )

    def approve_calendar_item(self, token: str, company_id: int, item_id: int) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/companies/{company_id}/calendar/{item_id}/approve",
            token=token,
        )

    def queue_calendar_item(self, token: str, company_id: int, item_id: int) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/companies/{company_id}/calendar/{item_id}/queue",
            token=token,
        )

    def list_publishing_queue(self, token: str, company_id: int) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/companies/{company_id}/publishing/queue", token=token)

    def list_connected_accounts(self, token: str, company_id: int) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/companies/{company_id}/connected-accounts", token=token)

    def oauth_status(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/oauth/status")

    def oauth_start(
        self, token: str, company_id: int, platform: str, connection_kind: str = "profile"
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/companies/{company_id}/oauth/{platform}/start",
            token=token,
            json={"connection_kind": connection_kind},
        )

    def list_facebook_pending_pages(
        self, token: str, company_id: int, pending_id: str
    ) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            f"/api/v1/companies/{company_id}/oauth/facebook/pending-pages",
            token=token,
            params={"pending_id": pending_id},
        )

    def complete_facebook_page(
        self, token: str, company_id: int, pending_id: str, page_id: str
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/companies/{company_id}/oauth/facebook/complete",
            token=token,
            json={"pending_id": pending_id, "page_id": page_id},
        )

    def disconnect_account(self, token: str, company_id: int, account_id: int) -> None:
        self._request(
            "DELETE",
            f"/api/v1/companies/{company_id}/connected-accounts/{account_id}",
            token=token,
        )

    def list_publishing_jobs(self, token: str, company_id: int) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/companies/{company_id}/publishing/jobs", token=token)

    def publish_item(self, token: str, company_id: int, item_id: int) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/companies/{company_id}/calendar/{item_id}/publish",
            token=token,
        )

    def publish_all(self, token: str, company_id: int) -> list[dict[str, Any]]:
        return self._request(
            "POST",
            f"/api/v1/companies/{company_id}/publishing/publish-all",
            token=token,
        )

    def admin_companies(self, token: str) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/admin/companies", token=token)

    def admin_usage(self, token: str) -> dict[str, Any]:
        return self._request("GET", "/api/v1/admin/usage", token=token)

    def admin_users(self, token: str) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/admin/users", token=token)

    def admin_prompts(self, token: str) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/admin/prompts", token=token)

    def admin_jobs(self, token: str) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/admin/jobs", token=token)

    def list_knowledge(self, token: str, company_id: int) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/companies/{company_id}/knowledge", token=token)

    def add_knowledge(self, token: str, company_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/companies/{company_id}/knowledge",
            token=token,
            json=payload,
        )

    def delete_knowledge(self, token: str, company_id: int, entry_id: int) -> None:
        self._request(
            "DELETE",
            f"/api/v1/companies/{company_id}/knowledge/{entry_id}",
            token=token,
        )

    def upload_file(
        self,
        token: str,
        company_id: int,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        kind: str = "knowledge",
        knowledge_source: str = "upload",
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{self.base_url}/api/v1/companies/{company_id}/files",
            params={"kind": kind, "knowledge_source": knowledge_source},
            files={"file": (filename, file_bytes, mime_type)},
            headers=headers,
            timeout=60,
        )
        if response.status_code >= 400:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except Exception:
                pass
            raise ApiError(str(detail), response.status_code)
        return response.json()

    def download_file(self, token: str, company_id: int, file_id: int) -> tuple[bytes, str]:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{self.base_url}/api/v1/companies/{company_id}/files/{file_id}",
            headers=headers,
            timeout=30,
        )
        if response.status_code >= 400:
            raise ApiError(response.text, response.status_code)
        mime = response.headers.get("content-type", "application/octet-stream")
        return response.content, mime

    def list_marketing_plans(self, token: str, company_id: int) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/companies/{company_id}/marketing-plans", token=token)

    def get_active_marketing_plan(self, token: str, company_id: int) -> dict[str, Any] | None:
        try:
            return self._request(
                "GET", f"/api/v1/companies/{company_id}/marketing-plans/active", token=token
            )
        except ApiError as exc:
            if exc.status_code == 404:
                return None
            raise

    def create_marketing_plan(
        self, token: str, company_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/companies/{company_id}/marketing-plans",
            token=token,
            json=payload,
        )

    def generate_marketing_plan(
        self, token: str, company_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/companies/{company_id}/marketing-plans/generate",
            token=token,
            json=payload,
        )

    def import_marketing_plan(
        self,
        token: str,
        company_id: int,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        plan_name: str | None = None,
        replace_existing: bool = True,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"}
        data: dict[str, str] = {"replace_existing": "true" if replace_existing else "false"}
        if plan_name:
            data["plan_name"] = plan_name
        response = requests.post(
            f"{self.base_url}/api/v1/companies/{company_id}/marketing-plans/import",
            headers=headers,
            files={"file": (filename, file_bytes, mime_type)},
            data=data,
            timeout=120,
        )
        if response.status_code >= 400:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except Exception:
                pass
            raise ApiError(str(detail), response.status_code)
        return response.json()

    def update_marketing_plan(
        self, token: str, company_id: int, plan_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            "PUT",
            f"/api/v1/companies/{company_id}/marketing-plans/{plan_id}",
            token=token,
            json=payload,
        )

    def delete_marketing_plan(self, token: str, company_id: int, plan_id: int) -> None:
        self._request(
            "DELETE",
            f"/api/v1/companies/{company_id}/marketing-plans/{plan_id}",
            token=token,
        )

    def list_content_pillars(self, token: str, company_id: int) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/companies/{company_id}/content-pillars", token=token)

    def create_content_pillar(
        self, token: str, company_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/companies/{company_id}/content-pillars",
            token=token,
            json=payload,
        )

    def delete_content_pillar(self, token: str, company_id: int, pillar_id: int) -> None:
        self._request(
            "DELETE",
            f"/api/v1/companies/{company_id}/content-pillars/{pillar_id}",
            token=token,
        )

    def list_posting_rules(self, token: str, company_id: int) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/companies/{company_id}/posting-rules", token=token)

    def create_posting_rule(
        self, token: str, company_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/companies/{company_id}/posting-rules",
            token=token,
            json=payload,
        )

    def update_posting_rule(
        self, token: str, company_id: int, rule_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            "PUT",
            f"/api/v1/companies/{company_id}/posting-rules/{rule_id}",
            token=token,
            json=payload,
        )

    def delete_posting_rule(self, token: str, company_id: int, rule_id: int) -> None:
        self._request(
            "DELETE",
            f"/api/v1/companies/{company_id}/posting-rules/{rule_id}",
            token=token,
        )
