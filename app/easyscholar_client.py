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
        if not publication_name:
            return EasyScholarResult(
                status="configuration_error",
                publication_name=publication_name,
                issn=issn,
                detail="EasyScholar official API requires publicationName.",
            )
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
            "publicationName": publication_name,
        }

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
                status="upstream_error",
                publication_name=publication_name,
                issn=issn,
                raw_response=payload,
                upstream_status_code=response.status_code,
                detail="EasyScholar did not return a successful lookup.",
            )

        api_code = payload.get("code")
        if api_code is not None and api_code != 200:
            message = str(payload.get("msg") or "EasyScholar lookup failed.")
            status = "configuration_error" if "key" in message.casefold() else "not_found"
            return EasyScholarResult(
                status=status,
                publication_name=publication_name,
                issn=issn,
                raw_response=payload,
                upstream_status_code=response.status_code,
                detail=message,
            )

        rank = parse_easyscholar_rank(payload)
        status = "ok" if rank else "not_found"
        return EasyScholarResult(
            status=status,
            publication_name=publication_name,
            issn=issn,
            journal_rank=rank,
            raw_response=payload,
            upstream_status_code=response.status_code,
        )


def parse_easyscholar_rank(payload: dict[str, Any]) -> JournalRank | None:
    if payload.get("code") not in (None, 200):
        return None

    data = payload.get("data")
    if not isinstance(data, dict):
        return None

    official_rank = data.get("officialRank")
    if not isinstance(official_rank, dict):
        return None

    official_all = _string_dict(official_rank.get("all"))
    official_select = _string_dict(official_rank.get("select"))
    if not official_all and not official_select:
        return None

    rank = JournalRank(
        official_rank_all=official_all,
        official_rank_select=official_select,
        custom_rank=data.get("customRank") if isinstance(data.get("customRank"), dict) else None,
        sci=_official_value(official_select, official_all, "sci"),
        ssci=_official_value(official_select, official_all, "ssci"),
        cas_zone=_official_value(official_select, official_all, "sciUp", "sciBase"),
        cas_small=_official_value(official_select, official_all, "sciUpSmall"),
        cas_top=_official_value(official_select, official_all, "sciUpTop"),
        impact_factor=_to_float(
            _official_value(official_select, official_all, "sciif")
        ),
        five_year_if=_to_float(
            _official_value(official_select, official_all, "sciif5")
        ),
        ei=_official_value(official_select, official_all, "eii"),
        cscd=_official_value(official_select, official_all, "cscd"),
        pku_core=_official_value(official_select, official_all, "pku"),
        cssci=_official_value(official_select, official_all, "cssci"),
        esi=_official_value(official_select, official_all, "esi"),
        warning=_official_value(official_select, official_all, "sciwarn"),
    )
    return rank


def _string_dict(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items() if item not in (None, "")}


def _official_value(
    selected: dict[str, str],
    all_ranks: dict[str, str],
    *keys: str,
) -> str | None:
    for key in keys:
        value = selected.get(key)
        if value:
            return value
    for key in keys:
        value = all_ranks.get(key)
        if value:
            return value
    return None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
