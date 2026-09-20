from link_lens.resolution import resolve
from link_lens.profiles import assemble_profiles, impact
from link_lens.extraction import extract
from link_lens.readers import record


def pair(spec, snapshot):
    rows = [record("a", "csv", 20, {"name": "Original Ltd", "abn": "51824753556"})]
    first = extract(spec, rows, snapshot)
    second_snapshot = {**snapshot, "source_id": "source-b", "id": "second"}
    second = extract(
        spec,
        [record("b", "csv", 20, {"name": "Different Name", "abn": "51824753556"})],
        second_snapshot,
    )
    return first["observations"] + second["observations"], first["candidates"] + second[
        "candidates"
    ]


def test_exact_links_and_equal_conflict(spec, snapshot):
    obs, candidates = pair(spec, snapshot)
    linked = resolve(obs, candidates)
    assert len(linked["entities"]) == len(linked["links"]) == 1
    profile = assemble_profiles(obs, linked["entities"])[0]
    assert profile["fields"]["entity.legal_name"]["status"] == "unresolved"
    assert "value" not in profile["fields"]["entity.legal_name"]
    assert len(profile["fields"]["entity.legal_name"]["alternatives"]) == 2
    assert all(
        i["profiles_without_remaining_cross_source_support"] == 1
        for i in impact(obs, candidates, linked["entities"], [profile])
    )


def test_same_name_not_identity(spec, snapshot):
    obs, candidates = pair(spec, snapshot)
    for o in obs:
        if o["field"] == "entity.legal_name":
            o["value"] = "Same Name"
    obs = [o for o in obs if o["field"] != "entity.abn"]
    linked = resolve(obs, candidates)
    assert not linked["links"] and len(linked["unlinked"]) == 2


def test_conflicting_identifiers_block(spec, snapshot):
    obs, candidates = pair(spec, snapshot)
    for source, value in [("source-a", "000000019"), ("source-b", "000000027")]:
        base = next(o for o in obs if o["source_id"] == source)
        obs.append({**base, "field": "entity.acn", "value": value})
    linked = resolve(obs, candidates)
    assert not linked["entities"] and all(
        "conflicting" in i["reason"] for i in linked["unlinked"]
    )


def test_group_relationship_is_not_identity(spec, snapshot):
    obs, candidates = pair(spec, snapshot)
    candidates[-1]["subject_role"] = "reporting_group"
    assert not resolve(obs, candidates)["links"]


def test_repeated_trading_names_are_retained(spec, snapshot):
    obs, candidates = pair(spec, snapshot)
    extra = {**candidates[0], "source_record_id": "extra"}
    candidates.append(extra)
    obs.extend(
        [
            {**o, "source_record_id": "extra", "id": o["id"] + "x"}
            for o in list(obs)
            if o["source_id"] == "source-a"
        ]
    )
    linked = resolve(obs, candidates)
    assert len(linked["entities"]) == 1 and len(linked["entities"][0]["records"]) == 3
    assert len(linked["links"]) == 2


def test_field_authority_preserves_loser(spec, snapshot):
    obs, candidates = pair(spec, snapshot)
    for o in obs:
        if o["source_id"] == "source-b":
            o["source_kind"] = "tax_disclosure"
            o["observed_at"] = "2026-01-01T00:00:00+00:00"
    profiles = assemble_profiles(obs, resolve(obs, candidates)["entities"])
    name = profiles[0]["fields"]["entity.legal_name"]
    assert (
        name["value"] == "Original Ltd"
        and name["alternatives"][0]["value"] == "Different Name"
    )
    assert name["provenance"][0]["source_id"] == "source-a"


def test_internal_entity_id_survives_new_identifier(spec, snapshot):
    obs, candidates = pair(spec, snapshot)
    previous = [
        {"id": "stable-internal-id", "identifiers": {"entity.acn": ["000000019"]}}
    ]
    base = obs[0]
    obs.append({**base, "field": "entity.acn", "value": "000000019"})
    linked = resolve(obs, candidates, existing_entities=previous)
    assert linked["entities"][0]["id"] == "stable-internal-id"
