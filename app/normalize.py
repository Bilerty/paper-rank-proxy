import re

SPACE_RE = re.compile(r"\s+")


def normalize_publication_name(name: str) -> str:
    cleaned = name.strip().casefold()
    cleaned = cleaned.replace("&", " and ")
    cleaned = re.sub(r"[^\w\s:.-]", " ", cleaned)
    return SPACE_RE.sub(" ", cleaned).strip()


def normalize_issn(issn: str) -> str:
    return issn.strip().replace("-", "").replace(" ", "").upper()


def build_lookup_key(publication_name: str | None = None, issn: str | None = None) -> str:
    if publication_name:
        return f"name:{normalize_publication_name(publication_name)}"
    if issn:
        return f"issn:{normalize_issn(issn)}"
    raise ValueError("publication_name or issn is required")
