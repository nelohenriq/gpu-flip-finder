from src.ai.valuation import _normalize_model, margin, score_listing


def test_normalize_model_known():
    assert _normalize_model("RTX 3060 12GB used") == "RTX3060"
    assert _normalize_model("RX 6600 XT") == "RX6600"
    assert _normalize_model("gtx 1660 super") == "GTX1660"


def test_margin_calculation():
    assert abs(margin(100.0, 150.0) - 0.5) < 1e-9
    assert margin(100.0, 0.0) == -1.0


def test_score_listing_falls_back_when_no_comps(monkeypatch):
    class FakeDB:
        def query(self, *args, **kwargs):
            class Q:
                def filter(self, *args, **kwargs):
                    return self
                def all(self):
                    return []
            return Q()
    result = score_listing(FakeDB(), "RTX 3060", 140.0)
    assert result.model == "RTX3060"
    assert result.confidence == "low"
