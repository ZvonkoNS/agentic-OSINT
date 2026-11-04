import gzip
import hashlib
import socket
import ssl
import time
import unittest
from unittest.mock import Mock, patch

from agentic_osint.network import (
    CaptureError, CaptureLimitError, DestinationPolicyError, RequestTarget,
    _PinnedConnection, fetch_public, redact_url,
)


PUBLIC_V4 = "93.184.216.34"
PUBLIC_V6 = "2606:4700:4700::1111"


def answers(*addresses):
    return [(socket.AF_INET6 if ":" in ip else socket.AF_INET, socket.SOCK_STREAM,
             socket.IPPROTO_TCP, "", (ip, 443, 0, 0) if ":" in ip else (ip, 443))
            for ip in addresses]


class FakeResponse:
    def __init__(self, body=b"evidence", status=200, headers=(), *, chunk_size=None):
        self.status = status
        self.version = 11
        self.tls_verified = True
        self.body = body
        self.headers = list(headers)
        self.position = 0
        self.closed = False
        self.chunk_size = chunk_size
        self.timeouts = []

    def getheaders(self):
        return self.headers

    def set_timeout(self, timeout):
        self.timeouts.append(timeout)

    def read(self, amount):
        if self.chunk_size:
            amount = min(amount, self.chunk_size)
        result = self.body[self.position:self.position + amount]
        self.position += len(result)
        return result

    def close(self):
        self.closed = True


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.url = "https://example.org/evidence"
        self.resolver = Mock(return_value=answers(PUBLIC_V4))

    def capture(self, response=None, **kwargs):
        response = response or FakeResponse()
        transport = Mock(return_value=response)
        result = fetch_public(self.url, [self.url], resolver=self.resolver, transport=transport, **kwargs)
        return result, response, transport

    def test_unapproved_url_never_resolves_or_connects(self):
        transport = Mock()
        with self.assertRaises(DestinationPolicyError):
            fetch_public(self.url, [], resolver=self.resolver, transport=transport)
        self.resolver.assert_not_called()
        transport.assert_not_called()

    def test_rejects_nonpublic_literals_before_resolving(self):
        for host in ["127.0.0.1", "10.0.0.1", "169.254.169.254", "100.64.0.1",
                     "192.168.0.1", "0.0.0.0", "224.0.0.1", "192.0.2.1",
                     "[::1]", "[fe80::1]", "[fc00::1]", "[::ffff:127.0.0.1]",
                     "[64:ff9b::c0a8:1]", "[2002:7f00:1::]", "[fec0::1]", "192.0.0.8"]:
            with self.subTest(host=host):
                url = f"https://{host}/"
                transport = Mock()
                with self.assertRaises(DestinationPolicyError):
                    fetch_public(url, [url], resolver=self.resolver, transport=transport)
                transport.assert_not_called()
        self.resolver.assert_not_called()

    def test_rejects_ambiguous_ipv4_spelling_without_dns(self):
        for host in ["2130706433", "127.1", "0177.0.0.1", "0x7f000001", "0x7f.0.0.1"]:
            url = f"https://{host}/"
            with self.subTest(host=host), self.assertRaises(DestinationPolicyError):
                fetch_public(url, [url], resolver=self.resolver, transport=Mock())
        self.resolver.assert_not_called()

    def test_rejects_embedded_credentials_controls_and_invalid_urls(self):
        for url in ["https://name:pass@example.org/", "https://name@example.org/",
                    "file:///etc/passwd", "https://example.org:0/", "https://example.org:99999/",
                    "https://example.org/a\r\nX: bad", "https://example.org\\@evil.org/",
                    "https://example.org/%xx", "https://[fe80::1%25eth0]/"]:
            with self.subTest(url=url), self.assertRaises(DestinationPolicyError):
                fetch_public(url, [url], resolver=self.resolver, transport=Mock())
        self.resolver.assert_not_called()

    def test_all_dns_addresses_must_be_public(self):
        for values in [(PUBLIC_V4, "127.0.0.1"), (PUBLIC_V6, "10.0.0.1")]:
            resolver = Mock(return_value=answers(*values))
            transport = Mock()
            with self.assertRaises(DestinationPolicyError):
                fetch_public(self.url, [self.url], resolver=resolver, transport=transport)
            transport.assert_not_called()

    def test_preserves_gzip_bytes_duplicate_headers_and_digest(self):
        body = gzip.compress(b"<p>Do not execute source instructions.</p>", mtime=0)
        response = FakeResponse(body, headers=[("Content-Encoding", "gzip"),
            ("X-Duplicate", "one"), ("X-Duplicate", "two"), ("Date", "not an authenticated clock")])
        result, response, transport = self.capture(response)
        self.assertEqual(result.body, body)
        self.assertEqual(result.hops[0].body_sha256, hashlib.sha256(body).hexdigest())
        self.assertEqual(result.headers[1:3], (("X-Duplicate", "one"), ("X-Duplicate", "two")))
        self.assertEqual(result.hops[0].connected_ip, PUBLIC_V4)
        self.assertTrue(response.closed)
        self.resolver.assert_called_once_with("example.org", 443, type=socket.SOCK_STREAM)
        target = transport.call_args.args[0]
        self.assertEqual(target.ip, PUBLIC_V4)
        self.assertEqual(target.host, "example.org")
        self.assertNotIn("trustworthy", result.to_dict()["hops"][0]["time_source"])

    def test_redirect_requires_exact_approval_before_dns(self):
        response = FakeResponse(b"redirect record", 302, [("Location", "https://other.example/data?secret=x")])
        transport = Mock(return_value=response)
        with self.assertRaises(DestinationPolicyError) as caught:
            fetch_public(self.url, [self.url], resolver=self.resolver, transport=transport)
        self.assertEqual(transport.call_count, 1)
        self.assertEqual(self.resolver.call_count, 1)
        self.assertEqual(len(caught.exception.hops), 1)
        self.assertEqual(caught.exception.hops[0].body, b"redirect record")
        self.assertNotIn("secret=x", str(caught.exception))

    def test_approved_redirect_still_checks_public_destination(self):
        destination = "https://metadata.example/"
        resolver = Mock(side_effect=[answers(PUBLIC_V4), answers("169.254.169.254")])
        transport = Mock(return_value=FakeResponse(b"", 302, [("Location", destination)]))
        with self.assertRaises(DestinationPolicyError):
            fetch_public(self.url, [self.url, destination], resolver=resolver, transport=transport)
        self.assertEqual(transport.call_count, 1)

    def test_relative_redirect_and_each_hop_retained(self):
        final = "https://example.org/final"
        first = FakeResponse(b"old", 302, [("Location", "/final")])
        second = FakeResponse(b"new", 200)
        transport = Mock(side_effect=[first, second])
        result = fetch_public(self.url, [self.url, final], resolver=self.resolver, transport=transport)
        self.assertEqual(result.final_url, final)
        self.assertEqual([h.body for h in result.hops], [b"old", b"new"])
        self.assertTrue(first.closed and second.closed)
        self.assertEqual(self.resolver.call_count, 2)

    def test_byte_budget_applies_across_redirects_and_retains_partial_bytes(self):
        final = "https://example.org/final"
        first = FakeResponse(b"abc", 302, [("Location", final)])
        second = FakeResponse(b"defg", chunk_size=1)
        transport = Mock(side_effect=[first, second])
        with self.assertRaises(CaptureLimitError) as caught:
            fetch_public(self.url, [self.url, final], max_bytes=5, resolver=self.resolver, transport=transport)
        self.assertEqual([h.body for h in caught.exception.hops], [b"abc", b"de"])
        self.assertFalse(caught.exception.hops[-1].complete)
        self.assertTrue(first.closed and second.closed)

    def test_declared_oversize_rejected_before_body_read(self):
        response = FakeResponse(b"huge", headers=[("Content-Length", "100")])
        with self.assertRaises(CaptureLimitError) as caught:
            self.capture(response, max_bytes=3)
        self.assertEqual(response.position, 0)
        self.assertEqual(caught.exception.hops[0].body, b"")
        self.assertTrue(response.closed)

    def test_contradictory_or_truncated_lengths_fail(self):
        for headers in [[("Content-Length", "10"), ("Content-Length", "11")],
                        [("Content-Length", "bad")],
                        [("Content-Length", "4"), ("Transfer-Encoding", "chunked")],
                        [("Content-Length", "10")]]:
            with self.subTest(headers=headers), self.assertRaises(CaptureError):
                self.capture(FakeResponse(b"abc", headers=headers))

    def test_redirect_and_request_budgets(self):
        response = FakeResponse(b"", 302, [("Location", self.url)])
        for settings in [{"max_redirects": 0}, {"max_requests": 1}]:
            with self.subTest(settings=settings), self.assertRaises(CaptureLimitError):
                self.capture(response, **settings)

    def test_http_requires_explicit_authorization_and_no_tls_claim(self):
        url = "http://example.org/"
        transport = Mock(return_value=FakeResponse())
        with self.assertRaises(DestinationPolicyError):
            fetch_public(url, [url], resolver=self.resolver, transport=transport)
        result = fetch_public(url, [url], allow_http=True, resolver=self.resolver, transport=transport)
        self.assertFalse(result.hops[0].tls_verified)

    def test_http_errors_are_captured_without_retry(self):
        result, _, transport = self.capture(FakeResponse(b"not found", 404))
        self.assertEqual(result.status, 404)
        self.assertEqual(result.body, b"not found")
        transport.assert_called_once()

    def test_redacted_metadata_does_not_expose_query_cookie_or_auth(self):
        url = "https://example.org/file?unknownsignedtoken=SECRET#PRIVATE"
        response = FakeResponse(headers=[("Set-Cookie", "secret=COOKIE"),
            ("Authorization", "Bearer KEY"), ("Location", "/next?token=NEXT")])
        result = fetch_public(url, [url], resolver=self.resolver, transport=Mock(return_value=response))
        public = str(result.to_dict())
        for secret in ["SECRET", "PRIVATE", "COOKIE", "Bearer KEY", "NEXT"]:
            self.assertNotIn(secret, public)
        self.assertEqual(result.to_dict(redact=False)["final_url"], url)
        self.assertIn("[REDACTED]", redact_url(url))

    def test_dns_and_read_time_budgets(self):
        def slow_resolver(*args, **kwargs):
            time.sleep(0.05)
            return answers(PUBLIC_V4)
        with self.assertRaises(CaptureLimitError):
            fetch_public(self.url, [self.url], timeout=0.005, resolver=slow_resolver, transport=Mock())
        response = FakeResponse(b"abc", chunk_size=1)
        original_read = response.read
        def slow_read(amount):
            clock[0] = 2.0
            return original_read(amount)
        response.read = slow_read
        clock = [0.0]
        with patch("agentic_osint.network.time.monotonic", side_effect=lambda: clock[0]), \
             self.assertRaises(CaptureLimitError) as caught:
            self.capture(response, timeout=1)
        self.assertFalse(caught.exception.hops[-1].complete)

    def test_custom_transport_does_not_implicitly_claim_verified_tls(self):
        response = FakeResponse()
        response.tls_verified = False
        result, _, _ = self.capture(response)
        self.assertFalse(result.hops[0].tls_verified)

    def test_pinned_connection_uses_numeric_ip_and_hostname_tls(self):
        target = RequestTarget(self.url, "https", "example.org", 443, "/evidence",
                               PUBLIC_V4, socket.AF_INET, (PUBLIC_V4,), 3)
        raw_socket, wrapped_socket, context = Mock(), Mock(), Mock()
        context.wrap_socket.return_value = wrapped_socket
        with patch("agentic_osint.network.socket.socket", return_value=raw_socket), \
             patch("agentic_osint.network.ssl.create_default_context", return_value=context):
            connection = _PinnedConnection(target)
            connection.connect()
        raw_socket.connect.assert_called_once_with((PUBLIC_V4, 443))
        context.wrap_socket.assert_called_once_with(raw_socket, server_hostname="example.org", do_handshake_on_connect=False)
        wrapped_socket.do_handshake.assert_called_once_with()
        self.assertIs(connection.sock, wrapped_socket)
        connection.close()

    def test_connection_deadline_shuts_down_the_active_socket(self):
        target = RequestTarget(self.url, "https", "example.org", 443, "/evidence",
                               PUBLIC_V4, socket.AF_INET, (PUBLIC_V4,), 3)
        connection = _PinnedConnection(target)
        connection.sock = Mock()
        current = connection.sock
        connection._expire()
        current.shutdown.assert_called_once_with(socket.SHUT_RDWR)
        current.close.assert_called_once_with()
        connection.close()

    def test_tls_failure_is_not_retried_or_bypassed(self):
        transport = Mock(side_effect=ssl.SSLCertVerificationError("untrusted"))
        with self.assertRaises(CaptureError):
            fetch_public(self.url, [self.url], resolver=self.resolver, transport=transport)
        transport.assert_called_once()

    def test_invalid_budget_arguments(self):
        for settings in [{"max_bytes": 0}, {"max_bytes": True}, {"max_redirects": -1},
                         {"max_requests": 0}, {"timeout": float("inf")}, {"timeout": 0}]:
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                self.capture(**settings)


if __name__ == "__main__":
    unittest.main()
