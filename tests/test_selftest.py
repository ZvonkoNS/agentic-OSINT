"""Offline regression checks for self-test comparison, aggregation and contracts."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from agentic_osint.selftest import evaluate_spec, resolve_pointer, validate_spec

ROOT = Path(__file__).resolve().parents[1]


def spec(assertions=None):
    return {"schema": "l1-selftest/1.3", "agent": "L1-WEB", "assertions": assertions or [
        {"id": "WEB-01", "step": "S2", "description": "captured HTTP status",
         "path": "/values/S2/http_status", "required": True, "check": "equals", "expect": 200}]}


def observations(value=200, state="OBSERVED"):
    return {"schema": "agentic-osint/observations/1.3", "agent": "L1-WEB", "run_kind": "offline_fixture",
            "values": {"S2": {"http_status": value}},
            "availability": {"WEB-01": {"status": state, "evidence_refs": ["EV-1"]}}}


class PointerTests(unittest.TestCase):
    def test_escaped_tokens_and_arrays(self):
        data = {"a/b": {"~key": ["zero", {"value": 42}]}}
        self.assertEqual(resolve_pointer(data, "/a~1b/~0key/1/value"), 42)
        self.assertIs(resolve_pointer(data, ""), data)

    def test_missing_and_invalid_pointer(self):
        for pointer in ("/missing", "/a/01", "/a/-", "/a/2"):
            with self.subTest(pointer=pointer), self.assertRaises(KeyError):
                resolve_pointer({"a": [1]}, pointer)
        for pointer in ("no-leading-slash", "/bad~2escape"):
            with self.subTest(pointer=pointer), self.assertRaises(ValueError):
                resolve_pointer({}, pointer)


class VerdictTests(unittest.TestCase):
    def test_valid_observation_passes(self):
        result = evaluate_spec(spec(), observations())
        self.assertEqual(result["verdict"], "PASS")
        self.assertTrue(result["release_eligible"])
        self.assertEqual(result["required_checked"], 1)

    def test_mutated_capture_fails(self):
        expected = hashlib.sha256(b"original response").hexdigest()
        changed = hashlib.sha256(b"changed response").hexdigest()
        rule = spec()
        rule["assertions"][0]["expect"] = expected
        result = evaluate_spec(rule, observations(changed))
        self.assertEqual(result["verdict"], "FAIL")
        self.assertFalse(result["release_eligible"])

    def test_missing_required_never_passes(self):
        observed = observations()
        observed["values"] = {}
        result = evaluate_spec(spec(), observed)
        self.assertEqual(result["verdict"], "INCOMPLETE")
        self.assertFalse(result["checks"][0]["observed_present"])
        self.assertFalse(result["release_eligible"])

    def test_required_blocked_and_optional_blocked(self):
        rule = spec()
        rule["assertions"][0]["inconclusive_if_blocked"] = True
        result = evaluate_spec(rule, observations(state="BLOCKED"))
        self.assertEqual(result["checks"][0]["status"], "INCONCLUSIVE")
        self.assertEqual(result["verdict"], "INCOMPLETE")
        rule["assertions"][0]["required"] = False
        self.assertEqual(evaluate_spec(rule, observations(state="BLOCKED"))["verdict"], "INCONCLUSIVE")

    def test_unrun_and_error_are_not_positive_results(self):
        self.assertEqual(evaluate_spec(spec(), observations(state="NOT_RUN"))["verdict"], "INCOMPLETE")
        self.assertEqual(evaluate_spec(spec(), observations(state="ERROR"))["verdict"], "FAIL")

    def test_drift_is_not_pass_or_release(self):
        rule = spec()
        rule["assertions"][0]["may_drift"] = True
        observed = observations(404)
        observed["run_kind"] = "live_smoke"
        observed["availability"]["WEB-01"]["baseline_change_review"] = {
            "confirmed": True, "reviewer": "offline-test-operator", "reason": "Source change compared with an independent capture.",
            "evidence_refs": ["EV-2"]}
        result = evaluate_spec(rule, observed)
        self.assertEqual(result["verdict"], "DRIFT")
        self.assertFalse(result["release_eligible"])
        self.assertIn("operator-asserted", result["checks"][0]["reason"])

    def test_corrupt_offline_fixture_cannot_be_dismissed_as_drift(self):
        rule = spec()
        rule["assertions"][0]["may_drift"] = True
        self.assertEqual(evaluate_spec(rule, observations(404))["verdict"], "FAIL")
        observed = observations(404)
        observed["run_kind"] = "live_smoke"
        self.assertEqual(evaluate_spec(rule, observed)["verdict"], "FAIL")

    def test_nonfinite_values_are_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_spec(spec(), observations(float("nan")))

    def test_pathological_regex_is_bounded_and_cannot_pass(self):
        rule = spec()
        rule["assertions"][0].update(check="matches", expect="(a+)+$")
        self.assertEqual(evaluate_spec(rule, observations("a" * 40 + "!"))["verdict"], "FAIL")

    def test_bool_is_not_json_number(self):
        rule = spec()
        rule["assertions"][0]["expect"] = 1
        self.assertEqual(evaluate_spec(rule, observations(True))["verdict"], "FAIL")
        rule["assertions"][0].update(check="gte", expect=0)
        self.assertEqual(evaluate_spec(rule, observations(False))["verdict"], "FAIL")

    def test_numeric_and_collection_operators(self):
        cases = [("between", [18, 20], 19), ("gte", 5, 5), ("lte", 5, 4),
                 ("contains", "marker", "text marker text"), ("contains", 2, [1, 2]),
                 ("startswith", "at://", "at://id/post/1"),
                 ("all_startswith", "at://", ["at://id/1", "at://id/2"]),
                 ("matches", r"\d{14}", "20261104000000"), ("in", ["A", "B"], "A")]
        for check, expected, value in cases:
            rule = spec()
            rule["assertions"][0].update(check=check, expect=expected)
            with self.subTest(check=check):
                self.assertEqual(evaluate_spec(rule, observations(value))["verdict"], "PASS")
        rule["assertions"][0].update(check="all_startswith", expect="at://")
        self.assertEqual(evaluate_spec(rule, observations([]))["verdict"], "FAIL")

    def test_explicit_observed_absence(self):
        rule = spec()
        rule["assertions"][0].update(check="exists", expect=False)
        observed = observations()
        observed["values"] = {}
        self.assertEqual(evaluate_spec(rule, observed)["verdict"], "PASS")
        observed["availability"] = {}
        self.assertEqual(evaluate_spec(rule, observed)["verdict"], "INCOMPLETE")

    def test_missing_spec_cannot_be_success(self):
        for value in ({}, {"schema": "l1-selftest/1.3", "agent": "L1-WEB", "assertions": []}):
            with self.assertRaises(ValueError):
                evaluate_spec(value, observations())

    def test_invalid_contracts_are_rejected(self):
        cases = []
        for update in ({"path": "__import__('os')"}, {"required": "yes"}, {"check": "eval"},
                       {"check": "between", "expect": [20, 18]}, {"check": "matches", "expect": "["}):
            rule = spec()
            rule["assertions"][0].update(update)
            cases.append(rule)
        rule = spec()
        rule["assertions"].append(deepcopy(rule["assertions"][0]))
        cases.append(rule)
        for rule in cases:
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                validate_spec(rule)

    def test_source_instructions_are_inert_observation_text(self):
        hostile = (ROOT / "tests/fixtures/malicious-source.txt").read_text(encoding="utf-8")
        rule = spec()
        rule["assertions"][0]["expect"] = 200
        result = evaluate_spec(rule, observations(hostile))
        self.assertEqual(result["verdict"], "FAIL")
        self.assertIn("Ignore previous instructions", result["checks"][0]["observed"])

    def test_existing_citation_does_not_pass_unsupported_value(self):
        fixture = json.loads((ROOT / "tests/fixtures/unsupported-claim.json").read_text(encoding="utf-8"))
        rule = spec()
        rule["assertions"][0]["expect"] = fixture["evidence_text"]
        observed = observations(fixture["unsupported_statement"])
        observed["availability"]["WEB-01"]["evidence_refs"] = [fixture["misleading_evidence_reference"]]
        self.assertEqual(evaluate_spec(rule, observed)["verdict"], "FAIL")


class PublishedSpecTests(unittest.TestCase):
    def test_every_published_assertion_is_machine_addressable(self):
        files = sorted((ROOT / "selftest").glob("*.selftest.json"))
        self.assertEqual(len(files), 15)
        for path in files:
            data = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(path=path.name):
                validate_spec(data)
                self.assertFalse(data["validation"]["live_provider_verified"])
                self.assertEqual(data["validation"]["host_matrix"], [])
                selectors = [a["path"] for a in data["assertions"]]
                self.assertEqual(len(selectors), len(set(selectors)))

    def test_crypto_fixture_arithmetic_and_no_counterparty_allocation(self):
        fixture = json.loads((ROOT / "tests/fixtures/crypto-transactions.json").read_text(encoding="utf-8"))
        for tx in fixture["transactions"]:
            delta = sum(o["value"] for o in tx["outputs"] if o["address"] == fixture["target_address"]) - sum(i["value"] for i in tx["inputs"] if i["address"] == fixture["target_address"])
            self.assertEqual(delta, tx["expected_target_net_delta"])
            self.assertEqual(sum(i["value"] for i in tx["inputs"]) - sum(o["value"] for o in tx["outputs"]), tx["fee"])
            self.assertEqual(tx["counterparty_allocation"], "not established")

    def test_snowflake_fixture_retains_milliseconds(self):
        data = json.loads((ROOT / "selftest/L1-DSC.selftest.json").read_text(encoding="utf-8"))
        expected = next(a["expect"] for a in data["assertions"] if a["id"] == "DSC-04")
        self.assertEqual(expected, "2019-08-20T17:34:31.544Z")

    def test_generated_specs_match_the_generator(self):
        before = {p.name: p.read_bytes() for p in (ROOT / "selftest").glob("*.selftest.json")}
        subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "build/make_selftests.py")], cwd=ROOT, check=True, capture_output=True)
        self.assertEqual(before, {p.name: p.read_bytes() for p in (ROOT / "selftest").glob("*.selftest.json")})


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from jsonschema import Draft202012Validator, FormatChecker
        except ImportError:
            raise unittest.SkipTest("install the project dependencies for JSON Schema validation")
        cls.Validator = Draft202012Validator
        cls.formats = FormatChecker()

    def test_all_schemas_are_valid_draft_2020_12(self):
        for path in (ROOT / "schemas").glob("*.schema.json"):
            with self.subTest(schema=path.name):
                self.Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))

    def test_specs_observations_and_results_validate(self):
        schema = json.loads((ROOT / "schemas/selftest.schema.json").read_text(encoding="utf-8"))
        for path in (ROOT / "selftest").glob("*.selftest.json"):
            self.Validator(schema, format_checker=self.formats).validate(json.loads(path.read_text(encoding="utf-8")))
        for name, value in [("selftest-observations", observations()), ("selftest-result", evaluate_spec(spec(), observations()))]:
            schema = json.loads((ROOT / f"schemas/{name}.schema.json").read_text(encoding="utf-8"))
            self.Validator(schema, format_checker=self.formats).validate(value)

    def test_runtime_case_checkpoint_and_integrity_match_schemas(self):
        from agentic_osint.common import validate_schema
        from agentic_osint.store import init_pack, approve, ingest, checkpoint
        from agentic_osint.verify import verify_pack
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "pack"
            case = init_pack(root, case_reference="SCHEMA-TEST", target_type="file", target_value="input.txt")
            validate_schema("case", case)
            approve(root, "offline-test-operator", "CONFIRM")
            source = base / "input.txt"
            source.write_bytes(b"A harmless byte fixture.\n")
            ingest(root, source)
            value = checkpoint(root, base / "checkpoint.json")
            validate_schema("checkpoint", value)
            result = verify_pack(root)
            validate_schema("integrity", result)
            self.assertEqual(result["result"], "INCOMPLETE")

    def test_case_contract_rejects_unknown_keys_bad_ids_and_nonboolean_permissions(self):
        from agentic_osint.store import init_pack
        schema = json.loads((ROOT / "schemas/case.schema.json").read_text(encoding="utf-8"))
        validator = self.Validator(schema, format_checker=self.formats)
        with tempfile.TemporaryDirectory() as temp:
            original = init_pack(Path(temp) / "pack", case_reference="SCHEMA-TEST", target_type="url", target_value="https://example.com/")
        bad = deepcopy(original)
        bad["unexpected_permission"] = True
        self.assertTrue(list(validator.iter_errors(bad)))
        bad = deepcopy(original)
        bad["scope"]["third_party_lookups"] = "yes"
        self.assertTrue(list(validator.iter_errors(bad)))
        bad = deepcopy(original)
        bad["pack_id"] = "same-minute-id"
        self.assertTrue(list(validator.iter_errors(bad)))

    def test_invalid_state_failure_result_has_a_valid_contract(self):
        from agentic_osint.common import validate_schema
        value = {"schema": "agentic-osint/integrity/1.3", "pack_id": None, "result": "FAIL",
                 "byte_integrity": "FAIL", "workflow": "NOT_CHECKED", "content_support": "NOT_CHECKED",
                 "failures": [{"category": "state", "error": "malformed source"}], "claims": [],
                 "limitations": ["No source truth is established."]}
        validate_schema("integrity", value)

    def test_graph_output_schema_matches_reported_and_observed_layers(self):
        from agentic_osint.common import validate_schema
        from agentic_osint.graph import build_graph
        pack = {"pack_id": "schema-pack", "evidence": [], "observations": [
            {"ev": "EV-1", "identifier": {"type": "email", "raw": "Alice@EXAMPLE.com"},
             "selector": {"type": "text", "start": 0, "end": 17}},
            {"ev": "EV-1", "identifier": {"type": "domain", "raw": "example.com"},
             "selector": {"type": "text", "start": 18, "end": 29}}]}
        graph = build_graph([pack])
        validate_schema("graph", graph)
        self.assertEqual(graph["edges"][0]["type"], "producer_reported")

    def test_event_request_accounting_fields_are_action_specific(self):
        schema = json.loads((ROOT / "schemas/event.schema.json").read_text(encoding="utf-8"))
        validator = self.Validator(schema, format_checker=self.formats)
        base = {"sequence": 1, "time_utc": "2026-11-04T00:00:00.000Z", "action": "network_budget_reserved",
                "actor": "offline-test", "details": {"requests": 2}, "previous_hash": "0" * 64, "hash": "1" * 64}
        validator.validate(base)
        for invalid in (True, 0, -1, 1001, "2"):
            value = deepcopy(base)
            value["details"]["requests"] = invalid
            with self.subTest(requests=invalid):
                self.assertTrue(list(validator.iter_errors(value)))
        settled = deepcopy(base)
        settled.update(action="network_budget_settled", details={"requests": -1, "requests_observed": 1})
        validator.validate(settled)
        for details in ({"requests": -1}, {"requests": 1, "requests_observed": 1},
                        {"requests": 0, "requests_observed": False}):
            invalid = deepcopy(settled)
            invalid["details"] = details
            self.assertTrue(list(validator.iter_errors(invalid)))
        other = deepcopy(base)
        other["action"] = "claimed"
        self.assertTrue(list(validator.iter_errors(other)))

    def test_seal_and_addendum_contracts_are_strict(self):
        from agentic_osint.common import validate_schema
        pack_id = "dfc54eca-2b4e-4c62-85eb-0c96384c5baf"
        seal = {"schema": "agentic-osint/seal/1.3", "pack_id": pack_id, "sealed_utc": "2026-11-04T00:00:00Z",
                "manifest_sha256": "a" * 64, "anchor": "Independently retain this digest."}
        addendum = {"schema": "agentic-osint/addendum/1.3", "pack_id": pack_id, "sequence": 1,
                    "created_utc": "2026-11-04T00:01:00Z", "actor": "offline-test",
                    "actor_authentication": "operator-asserted", "note": "Supplemental local artifact.",
                    "original_name": "input.txt", "sha256": "a" * 64, "size": 10,
                    "previous_hash": "b" * 64, "hash": "c" * 64}
        validate_schema("seal", seal)
        validate_schema("addendum", addendum)
        for name, document, changes in [("seal", seal, {"extra": "unrecognized"}),
                                        ("addendum", addendum, {"sequence": True}),
                                        ("addendum", addendum, {"actor": "   "}),
                                        ("addendum", addendum, {"actor_authentication": "authenticated"})]:
            with self.subTest(schema=name, changes=changes), self.assertRaises(ValueError):
                validate_schema(name, {**document, **changes})


if __name__ == "__main__":
    unittest.main()
