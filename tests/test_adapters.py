from decimal import localcontext
import hashlib
import io
from pathlib import Path
import stat
import struct
import tempfile
import unittest
import zipfile

from agentic_osint.adapters import (
    build_video_args, catalog_zip, classify_mx, detect_changes, discord_snowflake_utc,
    native_to_decimal, normalize_email, pdf_revision_status, sample_coverage, utxo_target_delta,
)


def zipped(entries, compression=zipfile.ZIP_STORED):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", compression=compression) as archive:
        for name, body in entries:
            archive.writestr(name, body)
    return data.getvalue()


class MethodAdapterTests(unittest.TestCase):
    def test_email_local_case_is_preserved_and_gravatar_transform_is_separate(self):
        first = normalize_email(" Alice@EXAMPLE.COM ")
        second = normalize_email("alice@example.com")
        self.assertEqual(first["comparison_key"], "Alice@example.com")
        self.assertNotEqual(first["comparison_key"], second["comparison_key"])
        self.assertEqual(first["gravatar_sha256"], second["gravatar_sha256"])
        self.assertEqual(first["gravatar_sha256"], hashlib.sha256(b"alice@example.com").hexdigest())
        self.assertEqual(normalize_email('"a@b"@example.com')["local_part"], '"a@b"')

    def test_email_invalid_or_unsupported_syntax_does_not_become_absence(self):
        for value in ["Name <a@example.com>", "a(comment)@example.com", "a..b@example.com", "@example.com", "a@[127.0.0.1]", "é@example.com"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_email(value)

    def test_null_mx_is_not_empty_mx_and_dns_errors_are_inconclusive(self):
        self.assertEqual(classify_mx(["0 ."])["classification"], "NULL_MX")
        self.assertEqual(classify_mx(["0 .", "0 ."])["classification"], "NULL_MX")
        self.assertEqual(classify_mx([])["classification"], "IMPLICIT_MX_UNTESTED")
        self.assertEqual(classify_mx(["0 .", "10 mx.example.com"])["classification"], "INVALID_MX_CONFIGURATION")
        self.assertEqual(classify_mx([], dns_status="NXDOMAIN")["classification"], "DOMAIN_NOT_FOUND")
        self.assertEqual(classify_mx([], dns_status="SERVFAIL")["classification"], "DNS_INCONCLUSIVE")
        self.assertIsNone(classify_mx(["10 mx.example.com"])["mailbox_exists"])

    def test_video_modes_are_single_target_and_nonmedia_skip_download(self):
        url = "https://www.youtube.com/watch?v=jNQXAC9IVRw&list=PLAYLIST"
        with tempfile.TemporaryDirectory() as directory:
            for mode in ["media", "metadata", "comments", "captions"]:
                args = build_video_args(url, mode=mode, output_dir=directory, max_bytes=1234)
                self.assertIn("--ignore-config", args)
                self.assertIn("--no-playlist", args)
                self.assertIn("--abort-on-unavailable-fragments", args)
                self.assertIn("--no-cookies", args)
                self.assertIn("--no-cookies-from-browser", args)
                self.assertEqual(args[args.index("--max-filesize") + 1], "1234")
                self.assertEqual(args[-2:], ["--", url])
                self.assertEqual("--skip-download" in args, mode != "media")
            captions = build_video_args(url, mode="captions", output_dir=directory)
            self.assertIn("--write-subs", captions)
            self.assertIn("--write-auto-subs", captions)
            comments = build_video_args(url, mode="comments", output_dir=directory)
            self.assertIn("youtube:comment_sort=top;max_comments=100,100,0,0,1", comments)

    def test_video_rejects_playlists_credentials_unknown_hosts_and_injected_options(self):
        with tempfile.TemporaryDirectory() as directory:
            for url in ["https://www.youtube.com/playlist?list=PL1", "https://youtube.com/channel/UC123",
                        "https://attacker.example/video", "https://a:b@youtube.com/watch?v=jNQXAC9IVRw",
                        "https://youtube.com/watch?v=jNQXAC9IVRw\n--exec=bad"]:
                with self.subTest(url=url), self.assertRaises(ValueError):
                    build_video_args(url, output_dir=directory)
            for path in ["relative", str(Path(directory) / "%(title)s")]:
                with self.assertRaises(ValueError):
                    build_video_args("https://youtu.be/jNQXAC9IVRw", output_dir=path)
            with self.assertRaises(ValueError):
                build_video_args("https://youtu.be/jNQXAC9IVRw", output_dir=directory, caption_languages=["en,--exec=bad"])

    def test_unchanged_text_does_not_hide_changed_media(self):
        result = detect_changes(b"same", b"same", before_text="same", after_text="same",
                                before_resources={"photo": b"old"}, after_resources={"photo": b"new"})
        self.assertEqual(result["text"], "TEXT_STABLE")
        self.assertEqual(result["resources"]["changed"], ["photo"])
        self.assertEqual(result["overall"], "CHANGES_OBSERVED")
        unchecked = detect_changes(b"same", b"same")
        self.assertEqual(unchecked["text"], "NOT_CHECKED")
        self.assertEqual(unchecked["resources"]["status"], "NOT_CHECKED")

    def test_native_conversion_never_uses_float_or_global_context_rounding(self):
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(native_to_decimal(123456789012345678901234567890123456789, 18), "123456789012345678901.234567890123456789")
        self.assertEqual(native_to_decimal(-1, 8), "-0.00000001")
        for value in [0.1, True, "1"]:
            with self.assertRaises(ValueError):
                native_to_decimal(value, 18)

    def test_multi_input_output_transaction_does_not_allocate_counterparty_flows(self):
        tx = {"vin": [{"prevout": {"value": 60, "scriptpubkey_address": "target"}},
                      {"prevout": {"value": 40, "scriptpubkey_address": "other-in"}}],
              "vout": [{"value": 20, "scriptpubkey_address": "target"},
                       {"value": 70, "scriptpubkey_address": "recipient"}]}
        result = utxo_target_delta(tx, "target")
        self.assertEqual(result["target_delta_raw"], -40)
        self.assertEqual(result["fee_raw"], 10)
        self.assertEqual(result["cooccurring_addresses"], ["other-in", "recipient"])
        self.assertEqual(result["counterparty_value_allocation"], "NOT_DETERMINABLE_FROM_INPUT_OUTPUT_COOCCURRENCE")
        tx["vin"][1] = {"prevout": None}
        result = utxo_target_delta(tx, "target")
        self.assertIsNone(result["target_delta_raw"])
        self.assertIsNone(result["fee_raw"])

    def test_unresolved_utxo_scripts_do_not_imply_a_complete_address_delta(self):
        tx = {"vin": [{"prevout": {"value": 100}}],
              "vout": [{"value": 90, "scriptpubkey_address": "target"}]}
        result = utxo_target_delta(tx, "target")
        self.assertIsNone(result["target_delta_raw"])
        self.assertEqual(result["address_coverage"], "UNRESOLVED_SCRIPTS")
        self.assertEqual(result["fee_raw"], 10)

    def test_invalid_utxo_values_and_coinbase_are_explicit(self):
        tx = {"vin": [{"is_coinbase": True}], "vout": [{"value": 50, "scriptpubkey_address": "target"}]}
        result = utxo_target_delta(tx, "target")
        self.assertTrue(result["coinbase"])
        self.assertIsNone(result["fee_raw"])
        self.assertEqual(result["target_delta_raw"], 50)
        tx["vout"][0]["value"] = True
        with self.assertRaises(ValueError):
            utxo_target_delta(tx, "target")

    def test_sample_rankings_remain_sampled_even_if_counts_coincidentally_match(self):
        result = sample_coverage(10, ["one", "two", "two"])
        self.assertEqual(result["coverage"], "SAMPLED")
        self.assertEqual(result["duplicate_count"], 1)
        self.assertEqual(result["omitted_count"], 8)
        self.assertEqual(sample_coverage(2, ["a", "b"])["coverage"], "SAMPLED")
        with self.assertRaises(ValueError):
            sample_coverage(3, ["a"], complete=True)
        self.assertEqual(sample_coverage(2, ["a", "b"], complete=True)["coverage"], "COMPLETE")

    def test_snowflake_requires_validated_object_and_preserves_milliseconds(self):
        self.assertEqual(discord_snowflake_utc("613425648685547541", object_type="guild", validated=True), "2019-08-20T17:34:31.544Z")
        for settings in [{"object_type": "guild"}, {"object_type": "widget_member", "validated": True}, {"object_type": "unknown", "validated": True}]:
            with self.assertRaises(ValueError):
                discord_snowflake_utc("613425648685547541", **settings)
        for value in [0, True, 1.2, "0001", 2**64]:
            with self.assertRaises(ValueError):
                discord_snowflake_utc(value, object_type="guild", validated=True)

    def test_pdf_eof_mutation_cannot_create_revision_fact(self):
        for data in [b"%PDF-1.7\n%%EOF", b"%PDF-1.7\nembedded %%EOF %%EOF %%EOF"]:
            result = pdf_revision_status(data)
            self.assertIsNone(result["incremental_updates"])
            self.assertEqual(result["status"], "NOT_VERIFIED")

    def test_zip_catalog_never_extracts_or_verifies_content_crc(self):
        raw = zipped([("folder/document.txt", b"evidence"), ("nested.zip", b"not expanded")])
        result = catalog_zip(raw)
        self.assertEqual(result["member_count"], 2)
        self.assertFalse(result["extraction_performed"])
        self.assertFalse(result["recursion_performed"])
        self.assertFalse(result["content_crc_verified"])
        self.assertTrue(result["members"][1]["nested_archive"])

    def test_zip_rejects_traversal_device_paths_and_collisions(self):
        for name in ["../secret", "/absolute", "C:/secret", "folder/../secret",
                     "con.txt", "folder/LPT1", "a:stream", "folder/name.", "a//b", "a/b/c/d"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                catalog_zip(zipped([(name, b"x")]), max_depth=3)
        with self.assertRaises(ValueError):
            catalog_zip(zipped([("A.txt", b"a"), ("a.txt", b"b")]))
        raw_backslash = zipped([("folder/secret", b"x")]).replace(b"folder/secret", b"folder\\secret")
        with self.assertRaises(ValueError):
            catalog_zip(raw_backslash)

    def test_zip_rejects_symlinks_and_excessive_declared_resources(self):
        link = zipfile.ZipInfo("link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaises(ValueError):
            catalog_zip(zipped([(link, "../../target")]))
        bomb = zipped([("bomb", b"0" * 10000)], compression=zipfile.ZIP_DEFLATED)
        with self.assertRaises(ValueError):
            catalog_zip(bomb, max_ratio=10)
        with self.assertRaises(ValueError):
            catalog_zip(zipped([("a", b"xx"), ("b", b"xx")]), max_uncompressed_bytes=3)
        with self.assertRaises(ValueError):
            catalog_zip(zipped([("a", b"x"), ("b", b"x")]), max_members=1)

    def test_zip_encryption_flags_are_listed_without_decryption(self):
        raw = bytearray(zipped([("encrypted", b"unchanged bytes")]))
        # Mark the local and central directory flags as encrypted. The catalog
        # must not call ZipFile.read(), which would request a password.
        struct.pack_into("<H", raw, 6, struct.unpack_from("<H", raw, 6)[0] | 1)
        central = raw.index(b"PK\x01\x02")
        struct.pack_into("<H", raw, central + 8, struct.unpack_from("<H", raw, central + 8)[0] | 1)
        result = catalog_zip(bytes(raw))
        self.assertTrue(result["members"][0]["encrypted"])
        self.assertFalse(result["extraction_performed"])


if __name__ == "__main__":
    unittest.main()
