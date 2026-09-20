import pytest

from link_lens.downloadability import parse_sample, probe_resource, select_downloadable


def test_reject_successful_html_empty_and_zip():
    for data in [b"", b"<html>Login</html>", b"PK\x03\x04archive"]:
        with pytest.raises(ValueError):
            parse_sample(data, "csv")
    assert (
        parse_sample(b"ABN\tName\n001234\tCompany\n", "csv")["rows"][1][0] == "001234"
    )


def test_replaces_unavailable_without_promoting_ids_or_using_labels():
    ranked = [
        {"dataset_id": str(i), "publisher": "p", "reason": "ranked"} for i in range(4)
    ]
    datasets = {
        str(i): {"id": str(i), "resources": [{"format": "csv"}]} for i in range(4)
    }

    def check(d):
        return {
            "dataset_id": d["id"],
            "status": "unavailable" if d["id"] == "0" else "available",
            "resource_id": "r",
        }

    selected, checks = select_downloadable(ranked, datasets, check=check, size=2)
    assert [r["dataset_id"] for r in selected] == ["1", "2"]
    assert checks["0"]["status"] == "unavailable"
    with pytest.raises(ValueError, match="Only 3"):
        select_downloadable(ranked, datasets, check=check, size=4)


def test_http_200_empty_is_not_downloadable(monkeypatch):
    import httpx

    monkeypatch.setattr(
        "link_lens.downloadability.public_resource_url", lambda url: url
    )
    real_client = httpx.Client
    transport = httpx.MockTransport(lambda req: httpx.Response(200, content=b""))
    monkeypatch.setattr(
        httpx, "Client", lambda **kw: real_client(transport=transport, **kw)
    )
    result = probe_resource(
        {"id": "r", "format": "csv", "url": "https://data.gov.au/empty.csv"}
    )
    assert result["http_status"] == 200
    assert result["status"] == "unavailable"
    assert "Empty response" in result["error"]


def test_index_csv_is_not_a_supported_data_download():
    with pytest.raises(ValueError, match="Resource index"):
        parse_sample(
            b"Resource name,Type,Download\nCompanies,XML/ZIP,https://data.gov.au/bulk.zip\n",
            "csv",
        )


def test_external_public_host_and_private_address_check(monkeypatch):
    from link_lens.downloadability import public_resource_url

    monkeypatch.setattr(
        "socket.getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("8.8.8.8", 443))]
    )
    assert (
        public_resource_url("http://publisher.example/data.csv")
        == "https://publisher.example/data.csv"
    )
    monkeypatch.setattr(
        "socket.getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("127.0.0.1", 443))]
    )
    with pytest.raises(ValueError, match="Non-public"):
        public_resource_url("https://publisher.example/data.csv")


def test_discovery_revision_pointer_preserves_original():
    from link_lens import store

    store.put("batches", "discovery-e", {"id": "old"})
    assert store.current_discovery("e")["id"] == "old"
    store.put("batches", "discovery-current-e", {"id": "new"})
    assert store.current_discovery("e")["id"] == "new"
    assert store.get("batches", "discovery-e")["id"] == "old"
