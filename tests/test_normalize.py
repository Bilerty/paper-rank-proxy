from app.normalize import build_lookup_key, normalize_issn, normalize_publication_name


def test_normalize_publication_name():
    assert (
        normalize_publication_name(" IEEE Transactions  on Power Systems ")
        == "ieee transactions on power systems"
    )


def test_normalize_ampersand():
    assert normalize_publication_name("Power & Energy") == "power and energy"


def test_normalize_issn():
    assert normalize_issn("0885-8950") == "08858950"


def test_build_lookup_key_prefers_issn():
    assert build_lookup_key("Applied Energy", "0306-2619") == "issn:03062619"
