"""Bounded, explicitly approved public-URL acquisition.

This module does not render, decompress, execute, or interpret response content.
The captured body is the HTTP entity body after transfer framing, with content
encoding (for example gzip) retained. It is not a packet/TLS transcript.

Permission to capture a URL must be obtained by the caller. Exact URL approval
is checked again before every redirect and before DNS resolution. Connections
use one of the already validated numeric addresses, with normal certificate and
hostname validation for HTTPS, rather than resolving the hostname a second time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import http.client
import ipaddress
import math
import queue
import re
import socket
import ssl
import threading
import time
from typing import Any, Callable, Iterable, Protocol
from urllib.parse import quote, urljoin, urlsplit, urlunsplit


REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_SENSITIVE_HEADER = re.compile(r"authorization|cookie|token|secret|api[-_]?key", re.I)
_FORBIDDEN_TRANSLATION_NETWORKS = (
    ipaddress.ip_network("64:ff9b::/96"),
    ipaddress.ip_network("64:ff9b:1::/48"),
)
_IPV4_SPECIAL_COMPAT = ipaddress.ip_network("192.0.0.0/24")
_IPV4_SPECIAL_PUBLIC_EXCEPTIONS = {ipaddress.ip_address("192.0.0.9"), ipaddress.ip_address("192.0.0.10")}


class CaptureError(ValueError):
    """A capture failed; already acquired hops remain available for preservation."""

    def __init__(
        self,
        message: str,
        *,
        hops: Iterable[CaptureHop] = (),
        partial_body: bytes = b"",
    ) -> None:
        super().__init__(message)
        self.hops = tuple(hops)
        self.partial_body = partial_body
        # Unknown unless the built-in fetcher recorded its own transport attempts.
        self.requests_attempted: int | None = None


class DestinationPolicyError(CaptureError):
    """The destination is unapproved, malformed, or not public."""


class CaptureLimitError(CaptureError):
    """A configured byte, request, redirect, or time budget was exhausted."""


def redact_url(url: str) -> str:
    """Redact all query/fragment values, including unrecognized signed tokens.

    Exact originals are retained in the restricted CaptureHop, not in this safe
    presentation value. No assumption is made that a URL hash anonymizes a case.
    """
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
        if ":" in host:
            host = f"[{host}]"
        if parts.port:
            host += f":{parts.port}"
        return urlunsplit(
            (parts.scheme, host, parts.path, "[REDACTED]" if parts.query else "",
             "[REDACTED]" if parts.fragment else "")
        )
    except (TypeError, ValueError):
        return "[invalid URL]"


def _safe_headers(headers: tuple[tuple[str, str], ...]) -> list[list[str]]:
    result = []
    for name, value in headers:
        if _SENSITIVE_HEADER.search(name):
            value = "[REDACTED]"
        elif name.lower() in {"location", "content-location", "referer"}:
            value = redact_url(value)
        result.append([name, value])
    return result


@dataclass(frozen=True)
class RequestTarget:
    """A fully validated, pinned destination supplied to a transport."""

    url: str
    scheme: str
    host: str
    port: int
    path: str
    ip: str
    address_family: int
    resolved_addresses: tuple[str, ...]
    timeout: float

    @property
    def host_header(self) -> str:
        host = f"[{self.host}]" if ":" in self.host else self.host
        default_port = 443 if self.scheme == "https" else 80
        return host if self.port == default_port else f"{host}:{self.port}"


@dataclass(frozen=True)
class CaptureHop:
    url: str
    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes = field(repr=False)
    connected_ip: str
    resolved_addresses: tuple[str, ...]
    started_utc: str
    finished_utc: str
    tls_verified: bool
    complete: bool = True
    error: str | None = None
    http_version: str = "unknown"

    @property
    def body_sha256(self) -> str:
        return hashlib.sha256(self.body).hexdigest()

    @property
    def size_bytes(self) -> int:
        return len(self.body)

    def to_dict(self, *, redact: bool = True) -> dict[str, Any]:
        """Metadata only: raw body bytes remain separately accessible."""
        return {
            "url": redact_url(self.url) if redact else self.url,
            "status": self.status,
            "headers": _safe_headers(self.headers) if redact else [list(h) for h in self.headers],
            "body_sha256": self.body_sha256,
            "size_bytes": self.size_bytes,
            "connected_ip": self.connected_ip,
            "resolved_addresses": list(self.resolved_addresses),
            "started_utc": self.started_utc,
            "finished_utc": self.finished_utc,
            "time_source": "local system clock; synchronization not independently verified",
            "tls_verified": self.tls_verified,
            "tls_validation": ("system trust store and requested-hostname verification" if self.tls_verified
                               else "not applicable (HTTP)" if urlsplit(self.url).scheme == "http"
                               else "not verified by transport"),
            "body_representation": "HTTP entity body; transfer framing removed; content encoding preserved",
            "http_version": self.http_version,
            "complete": self.complete,
            "error": self.error,
        }


@dataclass(frozen=True)
class CaptureResult:
    body: bytes = field(repr=False)
    final_url: str
    hops: tuple[CaptureHop, ...]

    @property
    def status(self) -> int:
        return self.hops[-1].status

    @property
    def headers(self) -> tuple[tuple[str, str], ...]:
        return self.hops[-1].headers

    def to_dict(self, *, redact: bool = True) -> dict[str, Any]:
        return {
            "final_url": redact_url(self.final_url) if redact else self.final_url,
            "status": self.status,
            "total_body_bytes": sum(h.size_bytes for h in self.hops),
            "hops": [h.to_dict(redact=redact) for h in self.hops],
        }


class Response(Protocol):
    status: int

    def getheaders(self) -> list[tuple[str, str]]: ...
    def read(self, amount: int) -> bytes: ...
    def close(self) -> None: ...


def _public_ip(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise DestinationPolicyError("Resolver returned a non-numeric address") from exc
    if not address.is_global or address.is_multicast or address.is_unspecified or address.is_reserved:
        raise DestinationPolicyError("Destination is not an allowed public unicast address")
    # Python <3.13 classified some special-use IPv4 addresses as global. Keep
    # the safe decision stable on all supported Python releases.
    if isinstance(address, ipaddress.IPv4Address) and address in _IPV4_SPECIAL_COMPAT and address not in _IPV4_SPECIAL_PUBLIC_EXCEPTIONS:
        raise DestinationPolicyError("Destination is in a non-public special-use range")
    if isinstance(address, ipaddress.IPv6Address):
        if address.is_site_local:
            raise DestinationPolicyError("Deprecated IPv6 site-local destinations are prohibited")
        if address.ipv4_mapped is not None:
            _public_ip(str(address.ipv4_mapped))
        # Transition mechanisms can route to a different embedded IPv4 endpoint.
        if address.sixtofour is not None or address.teredo is not None:
            raise DestinationPolicyError("IPv6 transition addresses are not supported")
        if any(address in network for network in _FORBIDDEN_TRANSLATION_NETWORKS):
            raise DestinationPolicyError("IPv6 translation addresses are not supported")
    return address


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise CaptureLimitError("Capture time budget exhausted")
    return remaining


def _resolve_with_deadline(
    resolver: Callable[..., Any], host: str, port: int, deadline: float,
) -> Any:
    """Bound waiting for the OS resolver without waiting on a stuck executor.

    Python cannot cancel a blocking system resolver. The daemon worker may finish
    later, but cannot perform HTTP work; at most one worker is created per hop.
    """
    output: queue.Queue[tuple[bool, Any]] = queue.Queue(maxsize=1)

    def run() -> None:
        try:
            output.put((True, resolver(host, port, type=socket.SOCK_STREAM)))
        except Exception as exc:  # Exception is propagated without target-bearing text.
            output.put((False, exc))

    threading.Thread(target=run, daemon=True).start()
    try:
        ok, value = output.get(timeout=_remaining(deadline))
    except queue.Empty as exc:
        raise CaptureLimitError("DNS resolution exceeded the capture time budget") from exc
    if not ok:
        raise CaptureError("DNS resolution failed") from value
    return value


def _target(
    url: str,
    allowed: frozenset[str],
    allow_http: bool,
    resolver: Callable[..., Any],
    deadline: float,
) -> RequestTarget:
    if url not in allowed:
        raise DestinationPolicyError("URL is not exactly approved: " + redact_url(url))
    if any(ord(ch) <= 32 or ord(ch) == 127 for ch in url) or "\\" in url:
        raise DestinationPolicyError("URL contains whitespace, controls, or a backslash")
    if re.search(r"%(?![0-9a-fA-F]{2})", url):
        raise DestinationPolicyError("URL contains an invalid percent escape")
    try:
        parts = urlsplit(url)
        if parts.scheme not in ({"https", "http"} if allow_http else {"https"}):
            raise DestinationPolicyError("Only HTTPS is allowed unless HTTP was explicitly authorized")
        if parts.username is not None or parts.password is not None or "@" in parts.netloc:
            raise DestinationPolicyError("URLs with embedded credentials are prohibited")
        host = parts.hostname
        if not host or "%" in host:
            raise DestinationPolicyError("URL has no valid host or contains a scoped/escaped host")
        host = host.rstrip(".").encode("idna").decode("ascii").lower()
        if not host or len(host) > 253:
            raise DestinationPolicyError("URL has an invalid hostname")
        port = parts.port if parts.port is not None else (443 if parts.scheme == "https" else 80)
        if not 1 <= port <= 65535:
            raise DestinationPolicyError("URL has an invalid port")
    except (UnicodeError, ValueError) as exc:
        if isinstance(exc, CaptureError):
            raise
        raise DestinationPolicyError("Malformed URL") from exc

    addresses: list[tuple[int, str]] = []
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        # Numeric shorthand, leading-zero/octal and hex spellings are rejected
        # before the OS resolver can reinterpret them as private IPv4 addresses.
        if re.fullmatch(r"[0-9.]+", host) or any(label.startswith("0x") for label in host.split(".")):
            raise DestinationPolicyError("Ambiguous numeric IPv4 spelling is prohibited")
        if any(not label or len(label) > 63 or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label) for label in host.split(".")):
            raise DestinationPolicyError("URL has an invalid hostname")
        infos = _resolve_with_deadline(resolver, host, port, deadline)
        if not isinstance(infos, (list, tuple)) or not infos or len(infos) > 128:
            raise DestinationPolicyError("Resolver returned an empty or excessive answer set")
        for info in infos:
            try:
                family, _, _, _, sockaddr = info
                address = _public_ip(sockaddr[0])
            except (TypeError, IndexError, ValueError) as exc:
                if isinstance(exc, CaptureError):
                    raise
                raise DestinationPolicyError("Resolver returned a malformed answer") from exc
            expected_family = socket.AF_INET6 if address.version == 6 else socket.AF_INET
            if family != expected_family:
                raise DestinationPolicyError("Resolver address family does not match its numeric address")
            pair = (family, str(address))
            if pair not in addresses:
                addresses.append(pair)
    else:
        address = _public_ip(str(literal))
        addresses.append((socket.AF_INET6 if address.version == 6 else socket.AF_INET, str(address)))
    family, pinned_ip = addresses[0]
    path = quote(parts.path or "/", safe="/%:@!$&'()*+,;=-._~")
    if parts.query:
        path += "?" + quote(parts.query, safe="/%?:@!$&'()*+,;=-._~")
    return RequestTarget(url, parts.scheme, host, port, path, pinned_ip, family,
                         tuple(address for _, address in addresses), _remaining(deadline))


class _PinnedConnection(http.client.HTTPConnection):
    def __init__(self, target: RequestTarget) -> None:
        super().__init__(target.host, target.port, timeout=target.timeout)
        self.target = target
        self._deadline_timer: threading.Timer | None = None

    def _expire(self) -> None:
        # Closing the current socket enforces a wall-clock bound even if a peer
        # drip-feeds TLS or header bytes inside each individual socket timeout.
        sock = self.sock
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()

    def close(self) -> None:
        if self._deadline_timer is not None:
            self._deadline_timer.cancel()
        super().close()

    def connect(self) -> None:
        sock = socket.socket(self.target.address_family, socket.SOCK_STREAM)
        sock.settimeout(self.target.timeout)
        self.sock = sock
        self._deadline_timer = threading.Timer(self.target.timeout, self._expire)
        self._deadline_timer.daemon = True
        self._deadline_timer.start()
        try:
            destination: tuple[Any, ...] = (self.target.ip, self.target.port)
            if self.target.address_family == socket.AF_INET6:
                destination += (0, 0)
            sock.connect(destination)
            if self.target.scheme == "https":
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=self.target.host, do_handshake_on_connect=False)
                self.sock = sock
                sock.do_handshake()
            self.sock = sock
        except BaseException:
            self.close()
            raise


class _HTTPResponse:
    def __init__(self, response: http.client.HTTPResponse, connection: _PinnedConnection) -> None:
        self._response = response
        self._connection = connection
        self.status = response.status
        self.version = response.version
        self.tls_verified = connection.target.scheme == "https"

    def getheaders(self) -> list[tuple[str, str]]:
        return self._response.getheaders()

    def set_timeout(self, seconds: float) -> None:
        sock = self._connection.sock
        if sock is None and self._response.fp is not None:
            sock = getattr(getattr(self._response.fp, "raw", None), "_sock", None)
        if sock is not None:
            sock.settimeout(seconds)

    def read(self, amount: int) -> bytes:
        # read1 bounds each blocking read, allowing an overall deadline check even
        # when a server drip-feeds a body within the socket's per-read timeout.
        return self._response.read1(amount)

    def close(self) -> None:
        try:
            self._response.close()
        finally:
            self._connection.close()


def _http_transport(target: RequestTarget) -> Response:
    connection = _PinnedConnection(target)
    try:
        connection.request("GET", target.path, headers={
            "Host": target.host_header,
            "User-Agent": "agentic-OSINT/1.3 (+https://github.com/ZvonkoNS/agentic-OSINT)",
            "Accept-Encoding": "identity",
            "Connection": "close",
        })
        return _HTTPResponse(connection.getresponse(), connection)
    except BaseException:
        connection.close()
        raise


def _body(response: Response, headers: tuple[tuple[str, str], ...], budget: int, deadline: float) -> bytes:
    lengths = [value.strip() for name, value in headers if name.lower() == "content-length"]
    if lengths:
        if len(set(lengths)) != 1 or not lengths[0].isdigit():
            raise CaptureError("Invalid or contradictory Content-Length headers")
        if any(name.lower() == "transfer-encoding" for name, _ in headers):
            raise CaptureError("Ambiguous Content-Length and Transfer-Encoding headers")
        if int(lengths[0]) > budget:
            raise CaptureLimitError("Declared response length exceeds the remaining byte budget")
    collected = bytearray()
    try:
        while True:
            remaining_time = _remaining(deadline)
            set_timeout = getattr(response, "set_timeout", None)
            if set_timeout is not None:
                set_timeout(remaining_time)
            chunk = response.read(min(65536, budget - len(collected) + 1))
            if not isinstance(chunk, bytes):
                raise CaptureError("Transport returned a non-byte response body")
            if len(collected) + len(chunk) > budget:
                collected.extend(chunk[:budget - len(collected)])
                raise CaptureLimitError("Response exceeded the byte budget")
            collected.extend(chunk)
            _remaining(deadline)
            if not chunk:
                if lengths and len(collected) != int(lengths[0]):
                    raise CaptureError("Response body ended before Content-Length bytes were received")
                return bytes(collected)
    except CaptureError as exc:
        exc.partial_body = bytes(collected)
        raise
    except (OSError, http.client.HTTPException) as exc:
        raise CaptureError("Response body could not be acquired completely", partial_body=bytes(collected)) from exc


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def fetch_public(
    url: str,
    allowed_urls: Iterable[str],
    *,
    max_bytes: int = 10_000_000,
    max_redirects: int = 5,
    timeout: float = 20,
    max_requests: int = 6,
    allow_http: bool = False,
    resolver: Callable[..., Any] | None = None,
    transport: Callable[[RequestTarget], Response] | None = None,
) -> CaptureResult:
    """Capture only exactly approved public destinations within fixed budgets.

    ``timeout`` is an overall acquisition budget, including DNS, redirects and
    body reads. A custom transport must respect ``RequestTarget.timeout`` and
    must connect to ``RequestTarget.ip`` without resolving ``host`` again.
    Tests inject transports; production callers should use the default transport.

    HTTP error bodies are evidence, so a 403/404 is returned rather than retried.
    The caller determines required-step success from the captured status. Errors
    retain complete and partial acquired hops in ``CaptureError.hops``.
    """
    if not isinstance(url, str) or isinstance(allowed_urls, (str, bytes)):
        raise DestinationPolicyError("URL and approved URL collection must be strings and a collection")
    allowed_values = list(allowed_urls)
    if not all(isinstance(value, str) for value in allowed_values):
        raise DestinationPolicyError("Every approved URL must be a string")
    for name, value, floor in (("max_bytes", max_bytes, 1), ("max_redirects", max_redirects, 0), ("max_requests", max_requests, 1)):
        if isinstance(value, bool) or not isinstance(value, int) or value < floor:
            raise ValueError(f"{name} must be an integer >= {floor}")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a finite positive number")
    if not isinstance(allow_http, bool):
        raise ValueError("allow_http must be a boolean")
    allowed = frozenset(allowed_values)
    resolver = resolver or socket.getaddrinfo
    transport = transport or _http_transport
    deadline = time.monotonic() + timeout
    hops: list[CaptureHop] = []
    total_bytes = 0
    attempts = 0
    current = url
    redirects = 0
    try:
        while True:
            if len(hops) >= max_requests:
                raise CaptureLimitError("Request budget exhausted")
            target = _target(current, allowed, allow_http, resolver, deadline)
            started = _utc()
            try:
                attempts += 1
                response = transport(target)
            except (OSError, http.client.HTTPException) as exc:
                raise CaptureError("HTTP connection or TLS verification failed") from exc
            try:
                status = response.status
                if isinstance(status, bool) or not isinstance(status, int) or not 100 <= status <= 599:
                    raise CaptureError("Transport returned an invalid HTTP status")
                headers = tuple((str(name), str(value)) for name, value in response.getheaders())
                version = {10: "HTTP/1.0", 11: "HTTP/1.1"}.get(getattr(response, "version", None), "unknown")
                tls_verified = target.scheme == "https" and getattr(response, "tls_verified", False) is True
                try:
                    body = _body(response, headers, max_bytes - total_bytes, deadline)
                except CaptureError as exc:
                    hops.append(CaptureHop(current, status, headers, exc.partial_body, target.ip,
                                           target.resolved_addresses, started, _utc(), tls_verified,
                                           False, str(exc), version))
                    raise
                hop = CaptureHop(current, status, headers, body, target.ip, target.resolved_addresses,
                                 started, _utc(), tls_verified, http_version=version)
                hops.append(hop)
                total_bytes += len(body)
            finally:
                response.close()
            if status not in REDIRECT_STATUSES:
                return CaptureResult(body, current, tuple(hops))
            locations = [value for name, value in headers if name.lower() == "location"]
            if len(locations) != 1 or not locations[0]:
                raise CaptureError("Redirect response requires exactly one nonempty Location header")
            if redirects >= max_redirects:
                raise CaptureLimitError("Redirect budget exhausted")
            current = urljoin(current, locations[0])
            redirects += 1
    except CaptureError as exc:
        exc.hops = tuple(hops)
        exc.requests_attempted = attempts
        raise
