from skills.knowledge.paper.id_utils import canonicalize_arxiv_id, resolve_paper_id


def test_canonicalize_arxiv_id_strips_version():
    assert canonicalize_arxiv_id("2602.04879v1") == "2602.04879"
    assert canonicalize_arxiv_id("2602.04879") == "2602.04879"


def test_canonicalize_arxiv_id_from_url():
    assert canonicalize_arxiv_id("https://arxiv.org/abs/2602.04879v3") == "2602.04879"
    assert canonicalize_arxiv_id("https://arxiv.org/pdf/2602.04879v2.pdf") == "2602.04879"
    assert canonicalize_arxiv_id("https://arxiv.org/html/2602.04879v1") == "2602.04879"


def test_resolve_paper_id_keeps_non_arxiv_local_id():
    assert resolve_paper_id("local-file-123") == "local-file-123"
