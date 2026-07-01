from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class RankRequestItem(BaseModel):
    publication_name: str | None = Field(default=None, min_length=1)
    issn: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def require_lookup_value(self):
        if not self.publication_name and not self.issn:
            raise ValueError("publication_name or issn is required")
        return self


class BatchRankRequest(BaseModel):
    items: list[RankRequestItem] = Field(min_length=1)
    force_refresh: bool = False


class RefreshRankRequest(RankRequestItem):
    pass


class JournalRank(BaseModel):
    sci: str | None = None
    cas_zone: str | None = None
    cas_small: str | None = None
    cas_top: bool | None = None
    impact_factor: float | None = None
    five_year_if: float | None = None
    ei: bool | None = None
    cscd: bool | None = None
    pku_core: bool | None = None
    cssci: bool | None = None
    esi: str | None = None
    warning: str | None = None


class RankResponse(BaseModel):
    publication_name: str | None = None
    normalized_name: str | None = None
    issn: str | None = None
    source: str = "easyscholar"
    status: Literal["ok", "not_found", "upstream_error", "configuration_error"]
    cache_hit: bool
    fetched_at: str | None = None
    expires_at: str | None = None
    journal_rank: JournalRank | None = None
    detail: str | None = None


class BatchRankResponse(BaseModel):
    items: list[RankResponse]


class EasyScholarResult(BaseModel):
    status: Literal["ok", "not_found", "upstream_error", "configuration_error"]
    publication_name: str | None = None
    issn: str | None = None
    journal_rank: JournalRank | None = None
    raw_response: dict[str, Any] | None = None
    upstream_status_code: int | None = None
    detail: str | None = None
