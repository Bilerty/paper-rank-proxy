from sqlalchemy.orm import Session

from app.database import create_session_factory, init_db
from app.easyscholar_client import EasyScholarClient
from app.rank_service import RankService
from app.schemas import EasyScholarResult, JournalRank


class FakeEasyScholarClient(EasyScholarClient):
    def __init__(self):
        self.calls = 0

    async def lookup(self, publication_name=None, issn=None):
        self.calls += 1
        return EasyScholarResult(
            status="ok",
            publication_name=publication_name,
            issn=issn,
            journal_rank=JournalRank(sci="Q1", cas_zone="Engineering 1", impact_factor=8.7),
            raw_response={"data": {"sci": "Q1"}},
            upstream_status_code=200,
        )


def test_rank_service_uses_cache(settings):
    init_db(settings)
    session_factory = create_session_factory(settings)
    fake_client = FakeEasyScholarClient()
    service = RankService(settings=settings, client=fake_client)

    session: Session = session_factory()
    try:
        first = _run(service.get_rank(session, publication_name="Applied Energy"))
        second = _run(service.get_rank(session, publication_name="Applied Energy"))
    finally:
        session.close()

    assert first.cache_hit is False
    assert second.cache_hit is True
    assert fake_client.calls == 1
    assert second.journal_rank is not None
    assert second.journal_rank.sci == "Q1"


def _run(coro):
    import asyncio

    return asyncio.run(coro)
