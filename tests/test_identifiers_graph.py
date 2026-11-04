import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from agentic_osint.graph import build_graph
from agentic_osint.identifiers import identifier_key, normalize_identifier


class IdentifierTests(unittest.TestCase):
    def test_email_local_case_is_not_merged(self):
        self.assertNotEqual(identifier_key("Alice@EXAMPLE.com", "email"), identifier_key("alice@example.com", "email"))
        self.assertEqual(identifier_key("Alice@EXAMPLE.com", "email"), identifier_key("Alice@example.com", "email"))

    def test_quoted_email_local_part_is_preserved(self):
        self.assertEqual(identifier_key('"a@B"@Example.com', "email")[2], '"a@B"@example.com')

    def test_domain_and_raw_are_separate(self):
        item = normalize_identifier("BÜCHER.example", "domain")
        self.assertEqual(item["raw"], "BÜCHER.example")
        self.assertEqual(item["comparison_key"][2], "xn--bcher-kva.example")

    def test_unsafe_transitional_idna_mapping_is_not_a_merge(self):
        with self.assertRaises(ValueError):
            identifier_key("faß.example", "domain")
        self.assertNotEqual(identifier_key("xn--fa-hia.example", "domain"), identifier_key("fass.example", "domain"))

    def test_onion_url_path_case_is_preserved(self):
        raw = "http://" + "a" * 56 + ".onion/Case?token=A"
        self.assertEqual(identifier_key(raw, "onion")[2], raw)
        self.assertNotEqual(identifier_key(raw, "onion"), identifier_key(raw.lower(), "onion"))

    def test_handles_need_platform_and_keep_case(self):
        with self.assertRaises(ValueError):
            identifier_key("Alice", "handle")
        self.assertNotEqual(identifier_key("Alice", "handle", "mastodon.social"), identifier_key("Alice", "handle", "github"))
        self.assertNotEqual(identifier_key("Alice", "handle", "github"), identifier_key("alice", "handle", "github"))

    def test_crypto_namespaces_prevent_cross_chain_merge(self):
        address = "0x" + "A" * 40
        self.assertNotEqual(identifier_key(address, "crypto", "eip155:1"), identifier_key(address, "crypto", "eip155:8453"))
        self.assertEqual(identifier_key(address, "crypto", "eip155:1"), identifier_key(address.lower(), "crypto", "eip155:1"))
        with self.assertRaises(ValueError):
            identifier_key(address, "crypto")

    def test_urls_are_not_silently_normalized(self):
        raw = "https://EXAMPLE.com/A?x=1&x=2#Part"
        self.assertEqual(identifier_key(raw, "url")[2], raw)
        self.assertNotEqual(identifier_key(raw, "url"), identifier_key(raw.lower(), "url"))
        with self.assertRaises(ValueError):
            identifier_key("https://user:pass@example.com/", "url")

    def test_phone_requires_country_prefix_and_ip_has_no_zone(self):
        with self.assertRaises(ValueError):
            identifier_key("020 7946 0000", "phone")
        self.assertEqual(identifier_key("+442079460000", "phone")[2], "+442079460000")
        with self.assertRaises(ValueError):
            identifier_key("fe80::1%12", "ip")
        self.assertEqual(identifier_key("2001:0db8::1", "ip")[2], "2001:db8::1")


class GraphTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = b"Alice@example.com example.com"
        (self.root / "capture.txt").write_bytes(self.data)
        self.pack = {"pack_id": "pack-a", "evidence": [{"id": "EV-1", "file": "capture.txt", "sha256": hashlib.sha256(self.data).hexdigest()}],
                     "observations": [{"ev": "EV-1", "identifier": {"raw": "Alice@example.com", "type": "email"}, "selector": {"type": "text", "start": 0, "end": 17}},
                                      {"ev": "EV-1", "identifier": {"raw": "example.com", "type": "domain"}, "selector": {"type": "text", "start": 18, "end": 29}}]}

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_hash_checked_observations_create_cooccurrence(self):
        graph = build_graph([self.pack], {"pack-a": self.root})
        self.assertEqual(len(graph["edges"]), 1)
        self.assertEqual(graph["edges"][0]["type"], "captured_cooccurrence")
        self.assertEqual(graph["edges"][0]["pack_id"], "pack-a")
        self.assertEqual(graph["issues"], [])

    def test_missing_bytes_only_allow_reported_layer(self):
        graph = build_graph([self.pack])
        self.assertEqual(graph["edges"][0]["type"], "producer_reported")
        self.assertEqual(len(graph["issues"]), 2)

    def test_unsupported_claim_with_valid_ev_is_not_source_verified(self):
        self.pack["observations"][0]["identifier"]["raw"] = "Bob@example.com"
        graph = build_graph([self.pack], {"pack-a": self.root})
        self.assertEqual(graph["edges"][0]["type"], "producer_reported")
        self.assertEqual(len(graph["issues"]), 1)

    def test_corrupt_artifact_excludes_entire_pack(self):
        (self.root / "capture.txt").write_bytes(self.data + b"!")
        graph = build_graph([self.pack], {"pack-a": self.root})
        self.assertEqual(graph["nodes"], [])
        self.assertEqual(graph["edges"], [])
        self.assertEqual(graph["excluded_packs"][0]["pack_id"], "pack-a")

    def test_json_pointer_requires_exact_scalar(self):
        data = json.dumps({"email": "Alice@example.com", "domain": "example.com"}).encode()
        (self.root / "capture.txt").write_bytes(data)
        self.pack["evidence"][0]["sha256"] = hashlib.sha256(data).hexdigest()
        self.pack["observations"][0]["selector"] = {"type": "json", "pointer": "/email"}
        self.pack["observations"][1]["selector"] = {"type": "json_pointer", "pointer": "/domain"}
        self.assertEqual(build_graph([self.pack], {"pack-a": self.root})["edges"][0]["type"], "captured_cooccurrence")
        self.pack["observations"][0]["selector"]["pointer"] = ""
        self.assertEqual(build_graph([self.pack], {"pack-a": self.root})["edges"][0]["type"], "producer_reported")

    def test_ambiguous_json_cannot_support_verified_edges(self):
        data = b'{"email":"Other@example.com","email":"Alice@example.com","domain":"example.com"}'
        (self.root / "capture.txt").write_bytes(data)
        self.pack["evidence"][0]["sha256"] = hashlib.sha256(data).hexdigest()
        self.pack["observations"][0]["selector"] = {"type": "json", "pointer": "/email"}
        self.pack["observations"][1]["selector"] = {"type": "json", "pointer": "/domain"}
        graph = build_graph([self.pack], {"pack-a": self.root})
        self.assertEqual(graph["edges"][0]["type"], "producer_reported")
        self.assertTrue(all("duplicate JSON" in i["reason"] for i in graph["issues"]))

    def test_invalid_json_pointer_escape_cannot_verify_source(self):
        data = b'{"email~2":"Alice@example.com","domain":"example.com"}'
        (self.root / "capture.txt").write_bytes(data)
        self.pack["evidence"][0]["sha256"] = hashlib.sha256(data).hexdigest()
        self.pack["observations"][0]["selector"] = {"type": "json", "pointer": "/email~2"}
        self.pack["observations"][1]["selector"] = {"type": "json", "pointer": "/domain"}
        graph = build_graph([self.pack], {"pack-a": self.root})
        self.assertEqual(graph["edges"][0]["type"], "producer_reported")
        self.assertTrue(any("pointer escape" in i["reason"] for i in graph["issues"]))

    def test_equal_bare_ev_ids_in_two_packs_do_not_join(self):
        other = json.loads(json.dumps(self.pack))
        other["pack_id"] = "pack-b"
        self.pack["observations"] = self.pack["observations"][:1]
        other["observations"] = other["observations"][1:]
        graph = build_graph([self.pack, other], {"pack-a": self.root, "pack-b": self.root})
        self.assertEqual(graph["edges"], [])
        self.assertEqual({o["pack_id"] for n in graph["nodes"] for o in n["observations"]}, {"pack-a", "pack-b"})

    def test_leads_have_their_own_unverified_layer(self):
        self.pack["leads"] = [{"id": "L-1", "from": {"raw": "example.com", "type": "domain"}, "to": {"raw": "Alice", "type": "handle", "namespace": "github"}}]
        graph = build_graph([self.pack], {"pack-a": self.root})
        self.assertEqual({e["type"] for e in graph["edges"]}, {"captured_cooccurrence", "lead_relation"})
        self.assertEqual(graph["edges"][-1]["verification"], "unverified_lead")

    def test_traversal_cannot_verify_source(self):
        self.pack["evidence"][0]["file"] = "../capture.txt"
        graph = build_graph([self.pack], {"pack-a": self.root})
        self.assertEqual(graph["edges"][0]["type"], "producer_reported")
        self.assertTrue(all(o["status"] == "producer_reported" for n in graph["nodes"] for o in n["observations"]))

    def test_duplicate_pack_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            build_graph([self.pack, self.pack])

    def test_graph_budgets_fail_closed(self):
        from unittest.mock import patch
        with patch("agentic_osint.graph.MAX_EDGES", 0):
            with self.assertRaises(ValueError):
                build_graph([self.pack])
        with patch("agentic_osint.graph.MAX_GRAPH_ARTIFACT_BYTES", 1):
            with self.assertRaises(ValueError):
                build_graph([self.pack], {"pack-a": self.root})

    def test_invalid_namespaceless_identifier_is_an_issue(self):
        self.pack["observations"][0]["identifier"] = {"raw": "Alice", "type": "handle"}
        graph = build_graph([self.pack])
        self.assertEqual(len(graph["nodes"]), 1)
        self.assertEqual(graph["edges"], [])
        self.assertTrue(any("namespace" in i["reason"] for i in graph["issues"]))


if __name__ == "__main__":
    unittest.main()
