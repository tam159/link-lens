import pytest
from openpyxl import Workbook
from link_lens.contracts import ReaderSpec, Operation
from link_lens.readers import read_records, record, partition, inspect_resource
from link_lens.extraction import extract, validate, valid_abn, valid_acn, operation


def test_tsv_and_preserved_zeros(tmp_path):
    path = tmp_path / "csv"
    path.write_text("name\tabn\tpostcode\r\nAcme\t001234567\t0800\r\n")
    h, rows = read_records(path, ReaderSpec(format="csv", delimiter="\t"), "sha")
    assert rows[0]["values"]["postcode"] == "0800"
    assert rows[0]["values"]["abn"] == "001234567"
    assert inspect_resource(path, "csv")["detected_delimiter"] == "\t"


def test_intro_excel_numeric_ids(tmp_path):
    book = Workbook()
    book.active.title = "Information"
    book.active.append(["Read this first"])
    sheet = book.create_sheet("Entities")
    sheet.append(["name", "abn"])
    sheet.append(["ATO", 51824753556])
    path = tmp_path / "content-hash"
    book.save(path)
    assert len(inspect_resource(path, "xlsx")["sheets"]) == 2
    h, rows = read_records(path, ReaderSpec(format="xlsx", sheet="Entities"), "sha")
    assert rows[0]["values"]["abn"] == "51824753556"


def test_cr_and_quoted_newline(tmp_path):
    path = tmp_path / "csv"
    path.write_bytes(b'name,abn\r"Hello\rWorld",51824753556\rpartial,')
    _, rows = read_records(path, ReaderSpec(format="csv"), "sha", partial=True)
    assert len(rows) == 1 and rows[0]["values"]["name"] == "Hello\rWorld"


def test_wrong_delimiter_is_detected(spec, snapshot, tmp_path):
    path = tmp_path / "csv"
    path.write_text("name\tabn\nAcme\t51824753556\n")
    headers, rows = read_records(path, spec.reader, "sha")
    report = validate(spec, headers, rows, snapshot)
    assert (
        not report["passed"]
        and "Referenced columns absent" in report["blocking_issues"][0]
    )


def test_disjoint_and_reproducible_partitions():
    rows = [record("sha", "csv", i, {"name": str(i)}) for i in range(1, 1001)]
    parts = partition(rows)
    assert parts == partition(list(rows))
    ids = [{r["record_id"] for r in p} for p in parts.values()]
    assert len(set.union(*ids)) == 1000 and not (
        ids[0] & ids[1] or ids[1] & ids[2] or ids[0] & ids[2]
    )
    assert all(r["locator"]["row"] > 10 for r in parts["final"])


def test_checksum_and_no_suffix_inference():
    assert valid_abn("51824753556") and valid_acn("000000019")
    assert not valid_abn("00000000000") and not valid_acn("000000000")
    assert operation("51824753556", Operation(op="acn")) is None
    with pytest.raises(ValueError):
        operation("51.824753556e9", Operation(op="digits"))


def test_missing_and_bad_identifier_abstain(spec, snapshot):
    rows = [
        record("sha", "csv", 20, {"name": "Example", "abn": ""}),
        record("sha", "csv", 21, {"name": "Bad", "abn": "123"}),
    ]
    result = extract(spec, rows, snapshot)
    assert len(result["observations"]) == 2 and len(result["issues"]) == 1
    assert all(o["field"] == "entity.legal_name" for o in result["observations"])


def test_timestamp_missing_quarantines(spec, snapshot):
    snapshot["observed_at"] = None
    result = validate(
        spec,
        ["name", "abn"],
        [record("sha", "csv", 20, {"name": "Example", "abn": "51824753556"})],
        snapshot,
    )
    assert not result["passed"] and result["observations"] == 0


def test_deterministic_claims_and_envelopes(spec, snapshot):
    rows = [record("sha", "csv", 20, {"name": "Example", "abn": "51824753556"})]
    result = extract(spec, rows, snapshot)
    assert result == extract(spec, rows, snapshot)
    obs = result["observations"][0]
    assert obs["raw_locator"]["row"] == 20 and set(obs["confidence"]) == {
        "source_reliability",
        "field_confidence",
    }
    assert obs["config_hash"] and obs["licence"] and obs["source_record_id"]


def test_encoding_checks_beyond_ascii_preview(tmp_path):
    path = tmp_path / "csv"
    path.write_bytes(b"name,abn\n" + b"Plain,\n" * 6000 + b"Legacy \xd0 text,\n")
    inspection = inspect_resource(path, "csv")
    assert inspection["detected_encoding"] == "cp1252"
    _, rows = read_records(
        path, ReaderSpec(format="csv", encoding="cp1252"), "hash", limit=7000
    )
    assert len(rows) == 6001
