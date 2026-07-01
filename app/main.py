from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import require_token
from app.config import Settings, get_settings
from app.database import check_db, create_session_factory, init_db, session_dependency
from app.easyscholar_client import EasyScholarClient
from app.rank_service import RankService
from app.rate_limit import AsyncRateLimiter
from app.schemas import BatchRankRequest, BatchRankResponse, RankResponse, RefreshRankRequest


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    settings.ensure_database_parent()
    session_factory = create_session_factory(settings)
    rate_limiter = AsyncRateLimiter(settings.easyscholar_rate_limit_per_second)
    client = EasyScholarClient(settings=settings, rate_limiter=rate_limiter)
    service = RankService(settings=settings, client=client)
    get_session = session_dependency(session_factory)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        settings.ensure_runtime_ready()
        init_db(settings)
        yield

    app = FastAPI(
        title="paper-rank-proxy",
        description="Journal rank cache proxy for paper search workflows.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.dependency_overrides[get_settings] = lambda: settings

    @app.get("/health")
    def health() -> dict[str, str]:
        check_db(settings)
        return {"status": "ok", "database": "ok", "service": "paper-rank-proxy"}

    @app.get("/rank", response_model=RankResponse, dependencies=[Depends(require_token)])
    async def get_rank(
        publication_name: str = Query(
            ...,
            min_length=1,
            description="Journal publication name. Required by the EasyScholar official API.",
        ),
        issn: str | None = Query(default=None, min_length=1),
        force_refresh: bool = False,
        session: Session = Depends(get_session),
    ) -> RankResponse:
        return await service.get_rank(
            session=session,
            publication_name=publication_name,
            issn=issn,
            force_refresh=force_refresh,
            request_type="single",
        )

    @app.post(
        "/rank/batch",
        response_model=BatchRankResponse,
        dependencies=[Depends(require_token)],
    )
    async def batch_rank(
        request: BatchRankRequest,
        session: Session = Depends(get_session),
    ) -> BatchRankResponse:
        if len(request.items) > settings.rank_batch_max_size:
            raise HTTPException(
                status_code=413,
                detail=f"Batch size cannot exceed {settings.rank_batch_max_size}.",
            )
        items = []
        for item in request.items:
            items.append(
                await service.get_rank(
                    session=session,
                    publication_name=item.publication_name,
                    issn=item.issn,
                    force_refresh=request.force_refresh,
                    request_type="batch",
                )
            )
        return BatchRankResponse(items=items)

    @app.post("/rank/refresh", response_model=RankResponse, dependencies=[Depends(require_token)])
    async def refresh_rank(
        request: RefreshRankRequest,
        session: Session = Depends(get_session),
    ) -> RankResponse:
        return await service.get_rank(
            session=session,
            publication_name=request.publication_name,
            issn=request.issn,
            force_refresh=True,
            request_type="refresh",
        )

    return app


app = create_app()
