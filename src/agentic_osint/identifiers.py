"""Conservative identifier keys: normalization never overwrites the source value."""
from __future__ import annotations

import ipaddress
import re
import unicodedata
from urllib.parse import urlsplit

_KINDS = {"domain", "email", "ip", "phone", "handle", "crypto", "url", "hash", "entity", "video", "discord", "onion"}
_ALIASES = {"username": "handle", "profile": "url", "profile_url": "url", "ip_address": "ip", "cryptocurrency": "crypto"}


def _domain(value: str) -> str:
    """IDNA-canonical DNS key, without asserting a registrable-domain boundary."""
    if not value or any(c.isspace() for c in value) or any(c in value for c in "/@:\\"):
        raise ValueError("domain must be a bare DNS name")
    value = unicodedata.normalize("NFC", value.removesuffix(".")).lower()
    try:
        ascii_name = value.encode("idna").decode("ascii").lower()
        # The standard-library codec is IDNA2003. Its transitional mappings
        # (e.g. faß -> fass) can collapse distinct IDNA2008 DNS names. Accept
        # reversible names only; a tested IDNA2008 adapter must handle others.
        if not value.isascii() and ascii_name.encode("ascii").decode("idna").lower() != value:
            raise ValueError("IDN needs an explicit IDNA2008 adapter; unsafe transitional mapping")
    except UnicodeError as exc:
        raise ValueError("invalid IDNA domain") from exc
    if len(ascii_name) > 253 or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in ascii_name.split(".")):
        raise ValueError("invalid DNS labels")
    return ascii_name


def identifier_key(raw: str, kind: str, namespace: str | None = None) -> tuple[str, str, str]:
    """Return (type, namespace, comparison value), preserving uncertain distinctions.

    Handles require a platform/instance namespace. They remain case-sensitive by
    default; a provider adapter may supply a separately documented comparison key.
    Crypto namespaces must identify a specific chain AND network (e.g.
    ``eip155:1`` or ``bitcoin:mainnet``). This function is an identity key, not an
    address-checksum validator or an assertion that an account exists.
    """
    if not isinstance(raw, str) or not raw or raw != raw.strip():
        raise ValueError("raw identifier must be a nonempty, unpadded string")
    if not isinstance(kind, str):
        raise ValueError("identifier type must be text")
    kind = _ALIASES.get(kind.lower(), kind.lower())
    if kind not in _KINDS:
        raise ValueError(f"unsupported identifier type: {kind}")
    if namespace is not None and (not isinstance(namespace, str) or not namespace.strip()):
        raise ValueError("namespace must be nonempty text")
    ns = namespace.strip().lower() if namespace else ""
    if kind == "domain":
        return kind, "dns", _domain(raw)
    if kind == "email":
        # The final @ splits the domain even in quoted local parts containing @.
        local, separator, domain = raw.rpartition("@")
        if not separator or not local or not domain or any(c in raw for c in "\r\n\x00"):
            raise ValueError("email must contain a local part and DNS domain")
        return kind, "smtp", local + "@" + _domain(domain)
    if kind == "ip":
        try:
            if "%" in raw:
                raise ValueError("scoped IP literals require local context")
            return kind, "ip", ipaddress.ip_address(raw).compressed
        except ValueError as exc:
            raise ValueError("invalid or scoped IP address") from exc
    if kind == "phone":
        # No guesses about national country prefixes, extensions or allocation.
        if not re.fullmatch(r"\+[1-9][0-9]{1,14}", raw):
            raise ValueError("phone comparison requires an explicit E.164 value")
        return kind, "e164", raw
    if kind == "handle":
        if not ns:
            raise ValueError("handle requires platform/instance namespace")
        return kind, ns, raw
    if kind == "crypto":
        if not ns or ":" not in ns:
            raise ValueError("crypto requires chain/network namespace")
        # EVM address byte identity ignores checksum capitalization. Validation
        # of EIP-55 remains the chain adapter's separate responsibility.
        value = raw.lower() if ns.startswith("eip155:") and re.fullmatch(r"0x[0-9a-fA-F]{40}", raw) else raw
        return kind, ns, value
    if kind == "url":
        try:
            parsed = urlsplit(raw)
            if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname or parsed.username is not None or parsed.password is not None:
                raise ValueError("URL requires HTTP(S), a host and no credentials")
        except ValueError as exc:
            raise ValueError("invalid URL") from exc
        # Preserve signed query parameters, escaping and path case. Deliberately
        # do not equate a URL to its canonical redirect or a domain node.
        return kind, "url", raw
    if kind == "hash":
        if not ns:
            raise ValueError("hash requires an algorithm namespace")
        if not re.fullmatch(r"[0-9a-fA-F]+", raw):
            raise ValueError("hash must be hexadecimal")
        return kind, ns, raw.lower()
    if kind in {"video", "discord", "entity"} and not ns:
        raise ValueError(f"{kind} requires an authority/platform namespace")
    if kind == "onion":
        if "://" in raw:
            parsed = urlsplit(raw)
            if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname or not parsed.hostname.lower().endswith(".onion") or parsed.username is not None:
                raise ValueError("invalid onion URL")
            return kind, "tor", raw  # Path and query case remain significant.
        return kind, "tor", raw.lower()
    return kind, ns, raw


def normalize_identifier(raw: str, kind: str, namespace: str | None = None) -> dict:
    """Return a serializable identity record with the untouched source string."""
    key = identifier_key(raw, kind, namespace)
    return {"raw": raw, "type": key[0], "namespace": key[1], "comparison_key": list(key)}
