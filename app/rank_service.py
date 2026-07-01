import json
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.config import Settings
from app.easyscholar_client import EasyScholarClient
from app.models import JournalRankCache, RankQueryLog
from app.normalize import build_lookup_key, normalize_issn, normalize_publication_name
from app.schemas import EasyScholarResult, JournalRank, RankResponse


class RankService:
    def __init__(self, settings: Settings, client: EasyScholarClient):
        self._settings = settings
        self._client = client

    async def get_rank(
        self,
        session: Session,
        publication_name: str | None = None,
        issn: str | None = None,
        force_refresh: bool = False,
        request_type: str = "single",
    ) -> RankResponse:
        lookup_key = build_lookup_key(publication_name=publication_name, issn=issn)
        cached = session.query(JournalRankCache).filter_by(lookup_key=lookup_key).one_or_none()
        if cached and not force_refresh and _parse_dt(cached.expires_at) > _now():
            self._log(session, lookup_key, request_type, True, cached.status)
            return _cache_to_response(cached, cache_hit=True)

        result = await self._client.lookup(publication_name=publication_name, issn=issn)
        record = self._upsert_cache(session, lookup_key, publication_name, issn, result, cached)
        self._log(
            session,
            lookup_key,
            request_type,
            False,
            result.status,
            result.upstream_status_code,
            result.detail,
        )
        session.commit()
        return _cache_to_response(record, cache_hit=False, detail=result.detail)

    def _upsert_cache(
        self,
        session: Session,
        lookup_key: str,
        requested_publication_name: str | None,
        requested_issn: str | None,
        result: EasyScholarResult,
        cached: JournalRankCache | None,
    ) -> JournalRankCache:
        now = _now()
        ttl_days = (
            self._settings.rank_cache_ttl_days
            if result.status == "ok"
            else self._settings.rank_cache_negative_ttl_days
        )
        expires_at = now + timedelta(days=ttl_days)
        rank = result.journal_rank
        publication_name = result.publication_name or requested_publication_name
        issn = result.issn or requested_issn
        normalized_name = normalize_publication_name(publication_name) if publication_name else None

        record = cached or JournalRankCache(
            lookup_key=lookup_key,
            created_at=_format_dt(now),
        )
        record.publication_name = publication_name
        record.normalized_name = normalized_name
        record.issn = normalize_issn(issn) if issn else None
        record.source = "easyscholar"
        record.status = result.status
        record.rank_json = rank.model_dump_json() if rank else None
        record.raw_response_json = (
            json.dumps(result.raw_response, ensure_ascii=False) if result.raw_response else None
        )
        record.official_rank_all_json = (
            json.dumps(rank.official_rank_all, ensure_ascii=False) if rank else None
        )
        record.official_rank_select_json = (
            json.dumps(rank.official_rank_select, ensure_ascii=False) if rank else None
        )
        record.custom_rank_json = (
            json.dumps(rank.custom_rank, ensure_ascii=False) if rank and rank.custom_rank else None
        )
        record.sci = rank.sci if rank else None
        record.ssci = rank.ssci if rank else None
        record.cas_zone = rank.cas_zone if rank else None
        record.cas_small = rank.cas_small if rank else None
        record.cas_top = rank.cas_top if rank else None
        record.impact_factor = rank.impact_factor if rank else None
        record.five_year_if = rank.five_year_if if rank else None
        record.ei = rank.ei if rank else None
        record.cscd = rank.cscd if rank else None
        record.pku_core = rank.pku_core if rank else None
        record.cssci = rank.cssci if rank else None
        record.esi = rank.esi if rank else None
        record.warning = rank.warning if rank else result.detail
        record.fetched_at = _format_dt(now)
        record.expires_at = _format_dt(expires_at)
        record.updated_at = _format_dt(now)
        session.add(record)
        return record

    def _log(
        self,
        session: Session,
        lookup_key: str,
        request_type: str,
        cache_hit: bool,
        status: str,
        upstream_status_code: int | None = None,
        error_message: str | None = None,
    ) -> None:
        session.add(
            RankQueryLog(
                lookup_key=lookup_key,
                request_type=request_type,
                cache_hit=int(cache_hit),
                status=status,
                upstream_status_code=upstream_status_code,
                error_message=error_message,
                created_at=_format_dt(_now()),
            )
        )
        session.commit()


def _cache_to_response(
    record: JournalRankCache,
    cache_hit: bool,
    detail: str | None = None,
) -> RankResponse:
    rank = JournalRank.model_validate_json(record.rank_json) if record.rank_json else None
    return RankResponse(
        publication_name=record.publication_name,
        normalized_name=record.normalized_name,
        issn=record.issn,
        source=record.source,
        status=record.status,
        cache_hit=cache_hit,
        fetched_at=record.fetched_at,
        expires_at=record.expires_at,
        journal_rank=rank,
        detail=detail,
    )


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _format_dt(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
