from typing import Any

import httpx

from app.config import Settings
from app.rate_limit import AsyncRateLimiter
from app.schemas import EasyScholarResult, JournalRank


class EasyScholarClient:
    def __init__(self, settings: Settings, rate_limiter: AsyncRateLimiter):
        self._settings = settings
        self._rate_limiter = rate_limiter

    async def lookup(
        self,
        publication_name: str | None = None,
        issn: str | None = None,
    ) -> EasyScholarResult:
        if not self._settings.easyscholar_api_url:
            return EasyScholarResult(
                status="configuration_error",
                publication_name=publication_name,
                issn=issn,
                detail="EASYSCHOLAR_API_URL is not configured.",
            )
        if not self._settings.easyscholar_secret_key:
            return EasyScholarResult(
                status="configuration_error",
                publication_name=publication_name,
                issn=issn,
                detail="EASYSCHOLAR_SECRET_KEY is not configured.",
            )

        params = {
            "secretKey": self._settings.easyscholar_secret_key,
        }
        if publication_name:
            params["publicationName"] = publication_name
        if issn:
            params["issn"] = issn

        await self._rate_limiter.wait()
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(self._settings.easyscholar_api_url, params=params)
            payload = response.json()
        except httpx.HTTPError as exc:
            return EasyScholarResult(
                status="upstream_error",
                publication_name=publication_name,
                issn=issn,
                detail=str(exc),
            )
        except ValueError as exc:
            return EasyScholarResult(
                status="upstream_error",
                publication_name=publication_name,
                issn=issn,
                upstream_status_code=response.status_code if "response" in locals() else None,
                detail=f"EasyScholar returned non-JSON response: {exc}",
            )

        if response.status_code >= 500:
            return EasyScholarResult(
                status="upstream_error",
                publication_name=publication_name,
                issn=issn,
                raw_response=payload,
                upstream_status_code=response.status_code,
                detail="EasyScholar returned a server error.",
            )
        if response.status_code >= 400:
            return EasyScholarResult(
                status="not_found",
                publication_name=publication_name,
                issn=issn,
                raw_response=payload,
                upstream_status_code=response.status_code,
                detail="EasyScholar did not return a successful lookup.",
            )

        rank = parse_easyscholar_rank(payload)
        status = "ok" if rank else "not_found"
        publication_value = _first(
            payload,
            "publication_name",
            "publicationName",
            "journal",
            "name",
        )
        return EasyScholarResult(
            status=status,
            publication_name=publication_value or publication_name,
            issn=_first(payload, "issn", "ISSN") or issn,
            journal_rank=rank,
            raw_response=payload,
            upstream_status_code=response.status_code,
        )


def parse_easyscholar_rank(payload: dict[str, Any]) -> JournalRank | None:
    data = _first(payload, "data", "result", "rank") or payload
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        return None

    rank = JournalRank(
        sci=_first(data, "sci", "SCI", "jcr", "jcrQuartile"),
        cas_zone=_first(data, "cas_zone", "casZone", "zone", "中科院分区"),
        cas_small=_first(data, "cas_small", "casSmall", "subZone", "小类分区"),
        cas_top=_to_bool(_first(data, "cas_top", "casTop", "top", "是否Top")),
        impact_factor=_to_float(_first(data, "impact_factor", "impactFactor", "if", "IF")),
        five_year_if=_to_float(_first(data, "five_year_if", "fiveYearIF", "fiveYearIf", "5yif")),
        ei=_to_bool(_first(data, "ei", "EI")),
        cscd=_to_bool(_first(data, "cscd", "CSCD")),
        pku_core=_to_bool(_first(data, "pku_core", "pkuCore", "北大核心")),
        cssci=_to_bool(_first(data, "cssci", "CSSCI")),
        esi=_first(data, "esi", "ESI"),
        warning=_first(data, "warning", "warn", "message"),
    )
    if rank.model_dump(exclude_none=True):
        return rank
    return None


def _first(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return None


def _to_bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return bool(value)
    normalized = str(value).strip().casefold()
    if normalized in {"true", "yes", "y", "1", "是", "yes."}:
        return True
    if normalized in {"false", "no", "n", "0", "否", "no."}:
        return False
    return None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
