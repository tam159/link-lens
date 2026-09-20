import pytest
from link_lens import store
from link_lens.settings import settings


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "LINK_LENS_DATABASE_URL", "sqlite:///" + str(tmp_path / "test.sqlite")
    )
    monkeypatch.setenv("LINK_LENS_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    settings.cache_clear()
    store.engine.cache_clear()
    store.metadata.create_all(store.engine())
    yield
    store.engine().dispose()
    store.engine.cache_clear()
    settings.cache_clear()


@pytest.fixture
def spec():
    from link_lens.contracts import MappingSpec

    return MappingSpec.model_validate(
        {
            "reader": {"format": "csv"},
            "record_grain": "One row per legal entity",
            "subject_role": "legal_entity",
            "source_kind": "company_register",
            "subject_label_field": "name",
            "fields": [
                {
                    "source_fields": ["name"],
                    "canonical_field": "entity.legal_name",
                    "transformations": [{"op": "trim"}],
                    "confidence": 0.9,
                    "evidence": "Explicit legal entity name column",
                },
                {
                    "source_fields": ["abn"],
                    "canonical_field": "entity.abn",
                    "transformations": [{"op": "abn"}],
                    "confidence": 0.9,
                    "evidence": "Explicit ABN column with checksum validation",
                },
            ],
            "unmapped_fields": [],
            "source_reliability": 0.9,
            "limitations": ["Synthetic fixture, never a submitted agent config."],
        }
    )


@pytest.fixture
def snapshot():
    return {
        "id": "snapshot",
        "format": "csv",
        "source_id": "source-a",
        "observed_at": "2025-01-01T00:00:00Z",
        "observed_at_basis": "publication proxy",
        "receipt": {"retrieved_at": "2025-02-01T00:00:00Z"},
        "licence": "CC BY",
        "sha256": "a" * 64,
    }
