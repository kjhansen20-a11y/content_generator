import base64

from api_client import ApiClient, ApiError


def load_post_image(
    client: ApiClient, token: str, company_id: int, file_id: int | None
) -> tuple[str | None, str | None]:
    if not file_id:
        return None, None
    try:
        data, mime = client.download_file(token, company_id, file_id)
        return base64.b64encode(data).decode("ascii"), mime.split(";")[0]
    except ApiError:
        return None, None
