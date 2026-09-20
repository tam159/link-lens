import json
from link_lens.exports import okf_export
from link_lens.profiles import assemble_profiles
from link_lens.resolution import resolve
from link_lens.extraction import extract
from link_lens.readers import record
from link_lens import store


def test_okf_matches_profiles_with_no_broken_links(tmp_path, spec, snapshot):
    obs = []
    candidates = []
    sources = []
    for sid in ["source-a", "source-b"]:
        snapshot = {**snapshot, "source_id": sid}
        rows = [
            record(
                sid, "csv", 20, {"name": "Example </script> Ltd", "abn": "51824753556"}
            )
        ]
        result = extract(spec, rows, snapshot)
        obs += result["observations"]
        candidates += result["candidates"]
        sources.append(
            {
                "id": sid,
                "portal": "https://data.gov.au/data",
                "metadata": {"title": sid, "license_title": "CC BY"},
            }
        )
    profiles = assemble_profiles(obs, resolve(obs, candidates)["entities"])
    root = tmp_path / "okf"
    stats = okf_export({"observations": obs, "profiles": profiles}, sources, root)
    assert stats["broken_links"] == 0
    dossier = (
        root / "entities" / f"{profiles[0]['canonical_entity_key']}.md"
    ).read_text()
    serialized = dossier.split("```json\n")[1].split("\n```")[0]
    assert json.loads(serialized) == profiles[0]
    assert store.blob_path(stats["viewer_artifact"]).exists()
    assert "Example </script> Ltd" not in (root / "viewer.html").read_text()
