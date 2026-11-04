"""Offline method and safety helpers; these do not query providers or run tools.

The helpers deliberately distinguish a computation from verified source facts.
They are building blocks, not a claim that a provider, AI host, PDF parser,
signature validator or downloader has passed an end-to-end operational test.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
import hashlib
import io
from pathlib import Path, PurePosixPath
import re
import stat
import struct
from typing import Any, Iterable, Mapping
import unicodedata
from urllib.parse import parse_qs, urlsplit
import zipfile


_ATOM = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
_LOCAL = rf'(?:{_ATOM}(?:\.{_ATOM})*|"(?:[\x20-\x21\x23-\x5b\x5d-\x7e]|\\[\x20-\x7e])*")'
_MAILBOX = re.compile(rf"(?P<local>{_LOCAL})@(?P<domain>[^@\s]+)")
_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")
_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtube-nocookie.com", "www.youtube-nocookie.com", "youtu.be", "www.youtu.be"}
_VIDEO_HOSTS = _YOUTUBE_HOSTS | {"vimeo.com", "www.vimeo.com", "player.vimeo.com", "dailymotion.com", "www.dailymotion.com", "dai.ly", "rumble.com", "www.rumble.com", "odysee.com", "www.odysee.com", "tiktok.com", "www.tiktok.com", "vm.tiktok.com", "x.com", "www.x.com", "twitter.com", "www.twitter.com", "facebook.com", "www.facebook.com", "fb.watch"}
_RESERVED_BASENAMES = {"con", "prn", "aux", "nul"} | {f"{prefix}{number}" for prefix in ("com", "lpt") for number in range(1, 10)}


def _integer(value: Any, name: str, minimum: int = 0, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{name} must be an integer within the supported range")
    return value


def _domain(value: str) -> str:
    try:
        domain = value.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError("Unsupported domain encoding") from exc
    if not domain or len(domain) > 253 or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part) for part in domain.split(".")):
        raise ValueError("Invalid domain syntax")
    return domain


def normalize_email(email: str) -> dict[str, str]:
    """Preserve ASCII local-part case, including supported quoted local parts.

    Comments, display-name forms, SMTP domain literals and non-ASCII local parts
    are explicitly unsupported, rather than classified as inactive mailboxes.
    Gravatar's provider-specific lowercase rule does not change mailbox identity.
    """
    if not isinstance(email, str):
        raise ValueError("A bare email address string is required")
    address = email.strip()
    match = _MAILBOX.fullmatch(address)
    if match is None:
        raise ValueError("Unsupported bare email syntax; no mailbox activity conclusion follows")
    local = match.group("local")
    if len(local.encode("ascii")) > 64:
        raise ValueError("Local part exceeds the supported 64-byte limit")
    domain = _domain(match.group("domain"))
    comparison = f"{local}@{domain}"
    if len(comparison.encode("ascii")) > 254:
        raise ValueError("Email address exceeds the supported length")
    # The Gravatar API documents trimming and lowercasing the entire supplied
    # email before SHA-256. This is a lookup transform, not an equivalence rule.
    gravatar = hashlib.sha256(address.lower().encode("utf-8")).hexdigest()
    return {"raw": email, "address": address, "local_part": local, "domain": domain,
            "comparison_key": comparison, "gravatar_sha256": gravatar}


def classify_mx(records: Iterable[str | tuple[int, str]], *, dns_status: str = "NOERROR") -> dict[str, Any]:
    """Classify DNS observations without probing SMTP or asserting mailbox life.

    NOERROR with no MX is IMPLICIT_MX_UNTESTED: A/AAAA fallback is possible.
    Explicit null MX is distinct. DNS failures cannot become a negative finding.
    """
    if not isinstance(dns_status, str):
        raise ValueError("DNS status must be a string")
    status = dns_status.upper()
    if status == "NXDOMAIN":
        return {"classification": "DOMAIN_NOT_FOUND", "dns_status": status, "records": [], "mailbox_exists": None}
    if status not in {"NOERROR", "NODATA"}:
        return {"classification": "DNS_INCONCLUSIVE", "dns_status": status, "records": [], "mailbox_exists": None}
    if isinstance(records, (str, bytes)):
        raise ValueError("MX records must be a collection, not one string")
    parsed = []
    for record in records:
        if isinstance(record, str):
            fields = record.split()
            if len(fields) != 2 or not re.fullmatch(r"[0-9]+", fields[0]):
                raise ValueError("Invalid MX observation")
            preference, exchange = int(fields[0]), fields[1]
        elif isinstance(record, (tuple, list)) and len(record) == 2:
            preference, exchange = record
        else:
            raise ValueError("MX observation must be 'preference exchange' or a pair")
        _integer(preference, "MX preference", maximum=65535)
        if not isinstance(exchange, str):
            raise ValueError("MX exchange must be a string")
        parsed.append({"preference": preference, "exchange": "." if exchange == "." else _domain(exchange)})
    if not parsed:
        classification = "IMPLICIT_MX_UNTESTED"
    elif any(row["exchange"] == "." for row in parsed):
        unique_records = {(row["preference"], row["exchange"]) for row in parsed}
        classification = "NULL_MX" if unique_records == {(0, ".")} else "INVALID_MX_CONFIGURATION"
    else:
        classification = "MX_ADVERTISED"
    return {"classification": classification, "dns_status": status, "records": parsed, "mailbox_exists": None}


def _video_host(url: str) -> str:
    if not isinstance(url, str) or any(ord(c) <= 32 or ord(c) == 127 for c in url) or "\\" in url:
        raise ValueError("A single HTTPS video URL without controls is required")
    try:
        parts = urlsplit(url)
        if parts.scheme != "https" or parts.username is not None or parts.password is not None or parts.port not in {None, 443}:
            raise ValueError("Only unauthenticated HTTPS watch URLs on their standard port are supported")
        host = (parts.hostname or "").lower()
    except ValueError as exc:
        raise ValueError("Invalid video URL") from exc
    if host not in _VIDEO_HOSTS:
        raise ValueError("No offline video adapter is defined for this host")
    if host in _YOUTUBE_HOSTS:
        path_parts = parts.path.strip("/").split("/")
        query = parse_qs(parts.query)
        if host.endswith("youtu.be"):
            candidate = path_parts[0] if len(path_parts) == 1 else ""
        elif parts.path.rstrip("/") == "/watch":
            values = query.get("v", [])
            candidate = values[0] if len(values) == 1 else ""
        elif len(path_parts) == 2 and path_parts[0] in {"shorts", "embed", "live"}:
            candidate = path_parts[1]
        else:
            candidate = ""
        if _VIDEO_ID.fullmatch(candidate) is None:
            raise ValueError("A YouTube video ID is required; playlists/channels are outside scope")
    elif not parts.path.strip("/") or any(word in parts.path.lower() for word in ("/playlist", "/sets/")):
        raise ValueError("A single watch URL is required, not a playlist or site root")
    return host


def _output_directory(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute() or any(ord(c) < 32 or ord(c) == 127 for c in str(path)) or "%" in str(path):
        raise ValueError("Output directory must be an absolute path without controls or template fields")
    if ".." in path.parts:
        raise ValueError("Output directory cannot traverse parent paths")
    for candidate in (path, *path.parents):
        if candidate.is_symlink() or getattr(candidate, "is_junction", lambda: False)():
            raise ValueError("Output directory cannot contain a symbolic-link component")
    if path.exists() and not path.is_dir():
        raise ValueError("Output directory is not a directory")
    return path


def build_video_args(
    url: str,
    *,
    mode: str = "media",
    output_dir: str | Path,
    max_bytes: int = 500_000_000,
    caption_languages: Iterable[str] = ("en",),
) -> list[str]:
    """Build an argument array, never a shell string and never execute it.

    Only fixed options are admitted. Run in a fresh approved evidence directory
    and an isolated process with a wall-clock/storage quota. --max-filesize is a
    downloader control, not a substitute for an external aggregate quota when
    media sizes are unknown. The command may need ffmpeg for separate streams.
    Provider/plugin functionality is not established by this offline helper.
    """
    host = _video_host(url)
    if mode not in {"media", "metadata", "comments", "captions", "captions_automatic"}:
        raise ValueError("Unknown video operation")
    _integer(max_bytes, "max_bytes", minimum=1, maximum=10_000_000_000)
    path = _output_directory(output_dir)
    if isinstance(caption_languages, str):
        raise ValueError("Caption languages must be a collection of explicit language tags")
    languages = list(caption_languages)
    if not languages or len(languages) > 20 or any(not isinstance(tag, str) or re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", tag) is None for tag in languages):
        raise ValueError("Use at most 20 explicit caption language tags")
    if mode == "comments" and host not in _YOUTUBE_HOSTS:
        raise ValueError("A bounded comments adapter is currently supplied only for YouTube")
    args = ["yt-dlp", "--ignore-config", "--no-playlist", "--no-plugin-dirs", "--no-remote-components",
            "--no-exec", "--no-cookies", "--no-cookies-from-browser", "--no-cache-dir", "--xff", "never",
            "--no-overwrites", "--no-write-playlist-metafiles", "--restrict-filenames", "--windows-filenames",
            "--socket-timeout", "15", "--retries", "2", "--fragment-retries", "2", "--file-access-retries", "1",
            "--extractor-retries", "1", "--abort-on-unavailable-fragments", "--max-filesize", str(max_bytes),
            "--max-downloads", "1", "--paths", str(path), "--output", "EV-%(id)s_%(format_id)s.%(ext)s", "--newline"]
    if mode != "media":
        args.append("--skip-download")
    if mode == "metadata":
        args.extend(["--dump-single-json", "--write-info-json"])
    elif mode == "comments":
        args.extend(["--write-info-json", "--write-comments", "--extractor-args", "youtube:comment_sort=top;max_comments=100,100,0,0,1"])
    elif mode in {"captions", "captions_automatic"}:
        args.extend(["--write-info-json", "--write-subs" if mode == "captions" else "--write-auto-subs", "--sub-langs", ",".join(languages)])
    else:
        args.extend(["--write-info-json", "--write-thumbnail", "--format", "bv*[height<=720]+ba/b[height<=720]"])
    args.extend(["--", url])
    return args


def detect_changes(
    before: bytes, after: bytes, *, before_text: str | None = None, after_text: str | None = None,
    before_resources: Mapping[str, bytes] | None = None, after_resources: Mapping[str, bytes] | None = None,
) -> dict[str, Any]:
    """Compare independent representations without claiming global page stability.

    Text, when supplied, must come from a recorded extraction method. Resources
    are only the captured subset, not all resources a live page might reference.
    """
    if not isinstance(before, bytes) or not isinstance(after, bytes):
        raise ValueError("Body observations must be bytes")
    if (before_text is None) != (after_text is None):
        raise ValueError("Text comparison needs both observations")
    if before_text is not None and (not isinstance(before_text, str) or not isinstance(after_text, str)):
        raise ValueError("Text observations must be strings")
    if (before_resources is None) != (after_resources is None):
        raise ValueError("Resource comparison needs both captured subsets")
    resource_result: dict[str, Any] = {"status": "NOT_CHECKED", "coverage": "not supplied"}
    if before_resources is not None:
        for mapping in (before_resources, after_resources):
            if not isinstance(mapping, Mapping) or any(not isinstance(k, str) or not isinstance(v, bytes) for k, v in mapping.items()):
                raise ValueError("Resources must map names to captured bytes")
        old, new = set(before_resources), set(after_resources)
        added, removed = sorted(new - old), sorted(old - new)
        changed = sorted(k for k in old & new if before_resources[k] != after_resources[k])
        resource_result = {"status": "CHANGED" if added or removed or changed else "NO_CHANGE_IN_CAPTURED_SUBSET",
                           "coverage": "captured subset only", "added": added, "removed": removed, "changed": changed}
    body_changed = before != after
    text_changed = None if before_text is None else before_text != after_text
    return {"body": "CHANGED" if body_changed else "BODY_STABLE",
            "before_body_sha256": hashlib.sha256(before).hexdigest(), "after_body_sha256": hashlib.sha256(after).hexdigest(),
            "text": "NOT_CHECKED" if text_changed is None else "TEXT_CHANGED" if text_changed else "TEXT_STABLE",
            "resources": resource_result,
            "overall": "CHANGES_OBSERVED" if body_changed or text_changed or resource_result["status"] == "CHANGED" else "NO_CHANGE_IN_CHECKED_REPRESENTATIONS"}


def native_to_decimal(value: int, decimals: int) -> str:
    """Exact base-unit conversion using no floating point or context rounding."""
    if isinstance(value, bool) or not isinstance(value, int) or value.bit_length() > 4096:
        raise ValueError("Native value must be a supported-size integer")
    _integer(decimals, "decimals", maximum=255)
    digits = len(str(abs(value)))
    if digits > 1000:
        raise ValueError("Native value exceeds the digit budget")
    with localcontext() as context:
        context.prec = max(28, digits + decimals + 2)
        return format(Decimal(value).scaleb(-decimals), "f")


def utxo_target_delta(transaction: Mapping[str, Any], target_address: str) -> dict[str, Any]:
    """Compute target-address input/output delta, never per-counterparty flows.

    Shape follows common explorer JSON: vin[].prevout.{value,scriptpubkey_address}
    and vout[].{value,scriptpubkey_address}; coinbase inputs set is_coinbase=true.
    Scriptless or non-address outputs remain in totals but are not attributed.
    Missing prevouts make the complete target delta and fee unknown.
    """
    if not isinstance(target_address, str) or not target_address:
        raise ValueError("An exact target address is required")
    if not isinstance(transaction, Mapping) or not isinstance(transaction.get("vin"), list) or not isinstance(transaction.get("vout"), list):
        raise ValueError("Transaction requires input and output lists")
    inputs, outputs = transaction["vin"], transaction["vout"]
    if not inputs or not outputs or len(inputs) + len(outputs) > 100_000:
        raise ValueError("Invalid or excessive transaction structure")
    input_total = output_total = target_in = target_out = 0
    input_complete = True
    input_addresses_complete = output_addresses_complete = True
    addresses: set[str] = set()
    coinbase = any(isinstance(vin, Mapping) and vin.get("is_coinbase") is True for vin in inputs)
    if coinbase and (len(inputs) != 1 or inputs[0].get("prevout") is not None):
        raise ValueError("Coinbase input structure is inconsistent")
    for vin in inputs:
        if not isinstance(vin, Mapping):
            raise ValueError("Input must be an object")
        previous = vin.get("prevout")
        if previous is None:
            if not coinbase:
                input_complete = False
                input_addresses_complete = False
            continue
        if not isinstance(previous, Mapping):
            raise ValueError("Previous output must be an object")
        value = _integer(previous.get("value"), "input value", maximum=2**64 - 1)
        address = previous.get("scriptpubkey_address")
        if address is not None and not isinstance(address, str):
            raise ValueError("Input address must be a string when exposed")
        if not address and previous.get("scriptpubkey_type") not in {"op_return", "nulldata"}:
            input_addresses_complete = False
        input_total += value
        if address:
            addresses.add(address)
        if address == target_address:
            target_in += value
    for output in outputs:
        if not isinstance(output, Mapping):
            raise ValueError("Output must be an object")
        value = _integer(output.get("value"), "output value", maximum=2**64 - 1)
        address = output.get("scriptpubkey_address")
        if address is not None and not isinstance(address, str):
            raise ValueError("Output address must be a string when exposed")
        if not address and output.get("scriptpubkey_type") not in {"op_return", "nulldata"}:
            output_addresses_complete = False
        output_total += value
        if address:
            addresses.add(address)
        if address == target_address:
            target_out += value
    if input_complete and not coinbase and output_total > input_total:
        raise ValueError("Outputs exceed observed inputs")
    target_complete = input_complete and input_addresses_complete and output_addresses_complete
    return {"target_address": target_address,
            "known_target_input_raw": target_in, "known_target_output_raw": target_out,
            "target_input_raw": target_in if input_complete and input_addresses_complete else None,
            "target_output_raw": target_out if output_addresses_complete else None,
            "known_target_delta_raw": target_out - target_in,
            "target_delta_raw": target_out - target_in if target_complete else None,
            "input_coverage": "COMPLETE" if input_complete else "MISSING_PREVOUTS", "coinbase": coinbase,
            "address_coverage": "COMPLETE" if input_addresses_complete and output_addresses_complete else "UNRESOLVED_SCRIPTS",
            "fee_raw": input_total - output_total if input_complete and not coinbase else None,
            "cooccurring_addresses": sorted(addresses - {target_address}),
            "counterparty_value_allocation": "NOT_DETERMINABLE_FROM_INPUT_OUTPUT_COOCCURRENCE"}


def sample_coverage(total_count: int | None, captured_ids: Iterable[str], *, complete: bool = False) -> dict[str, Any]:
    """Report sampled coverage without upgrading equal counts to verified history."""
    if total_count is not None:
        _integer(total_count, "total_count")
    if not isinstance(complete, bool) or isinstance(captured_ids, (str, bytes)):
        raise ValueError("Invalid coverage observations")
    ids = list(captured_ids)
    if len(ids) > 100_000 or any(not isinstance(value, str) or not value for value in ids):
        raise ValueError("Captured IDs must be nonempty strings within the count budget")
    unique = len(set(ids))
    if total_count is not None and unique > total_count:
        raise ValueError("Captured unique count exceeds the stated total")
    if complete and (total_count is None or unique != total_count):
        raise ValueError("Complete coverage requires a known matching total")
    return {"coverage": "COMPLETE" if complete else "SAMPLED" if total_count is not None else "UNKNOWN_TOTAL",
            "total_count": total_count, "captured_unique_count": unique, "duplicate_count": len(ids) - unique,
            "omitted_count": None if total_count is None else total_count - unique,
            "ranking_basis": "complete captured history" if complete else "captured sample only"}


def discord_snowflake_utc(value: str | int, *, object_type: str, validated: bool = False) -> str:
    """Compute millisecond UTC only after a trusted caller validates object type.

    ``validated`` means the exact ID was captured in a documented, real Discord
    object field. A numeric shape alone is insufficient. Widget member IDs are
    anonymized and are never accepted, even when the caller sets validated=True.
    """
    if validated is not True or object_type not in {"guild", "user", "channel", "message", "role", "application", "emoji", "sticker", "webhook", "interaction"}:
        raise ValueError("Snowflake computation requires a validated stable Discord object; widgets are excluded")
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("Snowflake must be exact decimal text or an integer")
    raw = str(value)
    if re.fullmatch(r"[1-9][0-9]{0,19}", raw) is None:
        raise ValueError("Snowflake must be a canonical positive decimal integer")
    number = int(raw)
    if number > 2**64 - 1:
        raise ValueError("Snowflake exceeds 64 bits")
    epoch = datetime(2015, 1, 1, tzinfo=timezone.utc)
    return (epoch + timedelta(milliseconds=number >> 22)).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def pdf_revision_status(data: bytes) -> dict[str, Any]:
    """Do not turn raw %%EOF occurrences into document-history assertions.

    Full xref/trailer/Prev and signature-coverage validation requires a dedicated
    supported parser. This standard-library helper truthfully leaves it unchecked.
    """
    if not isinstance(data, bytes) or not data.lstrip().startswith(b"%PDF-"):
        raise ValueError("PDF bytes are required")
    return {"incremental_updates": None, "status": "NOT_VERIFIED",
            "reason": "Requires validated xref/trailer/Prev-chain parsing; raw EOF counting is not a revision test",
            "signature_status": "NOT_VERIFIED"}


def _archive_path(name: str, *, max_depth: int) -> str:
    if not name or "\\" in name or name.startswith("/") or any(ord(c) < 32 or ord(c) == 127 for c in name):
        raise ValueError("Unsafe archive member path")
    parts = name.rstrip("/").split("/")
    if len(parts) > max_depth or any(part in {"", ".", ".."} or ":" in part or part.endswith((".", " ")) for part in parts):
        raise ValueError("Unsafe or excessive archive path depth")
    for part in parts:
        if part.split(".", 1)[0].casefold() in _RESERVED_BASENAMES:
            raise ValueError("Archive path contains a reserved device name")
    if PurePosixPath(name).is_absolute():
        raise ValueError("Absolute archive paths are prohibited")
    return unicodedata.normalize("NFC", name.rstrip("/")).casefold()


def catalog_zip(
    source: bytes | str | Path, *, max_archive_bytes: int = 10_000_000,
    max_members: int = 1000, max_uncompressed_bytes: int = 100_000_000,
    max_member_bytes: int = 20_000_000, max_depth: int = 10, max_ratio: int = 100,
) -> dict[str, Any]:
    """Bounded ZIP metadata catalog; never extracts or decompresses a member.

    Rejects path traversal, links/devices, ambiguous collisions, ZIP64/multidisk
    containers and excessive declared sizes before accepting the catalog. Nested
    archives and encrypted members are flagged, not opened. File contents and
    CRCs remain unverified. Process isolation is still required for hostile input.
    """
    for name, number in [("max_archive_bytes", max_archive_bytes), ("max_members", max_members),
                         ("max_uncompressed_bytes", max_uncompressed_bytes), ("max_member_bytes", max_member_bytes),
                         ("max_depth", max_depth), ("max_ratio", max_ratio)]:
        _integer(number, name, minimum=1)
    if isinstance(source, bytes):
        data = source
    else:
        path = Path(source)
        if path.is_symlink() or not path.is_file() or path.stat().st_size > max_archive_bytes:
            raise ValueError("Archive source is unsupported or exceeds its byte budget")
        with path.open("rb") as handle:
            data = handle.read(max_archive_bytes + 1)
    if len(data) > max_archive_bytes:
        raise ValueError("Archive exceeds its byte budget")
    offset = data.rfind(b"PK\x05\x06", max(0, len(data) - 65557))
    if offset < 0 or len(data) - offset < 22:
        raise ValueError("ZIP end-of-directory record is missing")
    _, disk, directory_disk, disk_entries, entries, directory_size, directory_offset, comment_size = struct.unpack_from("<4s4H2LH", data, offset)
    if offset + 22 + comment_size != len(data) or disk or directory_disk or disk_entries != entries:
        raise ValueError("Ambiguous or multidisk ZIP containers are not supported")
    if entries == 65535 or directory_size == 0xFFFFFFFF or directory_offset == 0xFFFFFFFF:
        raise ValueError("ZIP64 containers require a separately bounded parser")
    if entries > max_members or directory_offset + directory_size != offset:
        raise ValueError("ZIP directory count or extent exceeds the supported bounds")
    # ZipInfo normalizes Windows separators on Windows. Inspect original names
    # before constructing it so an ambiguous raw path cannot be hidden by that
    # transformation. Also require the local header to name the same member.
    cursor = directory_offset
    for _ in range(entries):
        if cursor + 46 > offset:
            raise ValueError("Truncated ZIP central directory")
        fields = struct.unpack_from("<4s6H3I5H2I", data, cursor)
        if fields[0] != b"PK\x01\x02":
            raise ValueError("Invalid ZIP directory member")
        flags, name_size, extra_size, member_comment = fields[3], fields[10], fields[11], fields[12]
        next_member = cursor + 46 + name_size + extra_size + member_comment
        if next_member > offset:
            raise ValueError("ZIP directory member exceeds the declared directory")
        raw_name = data[cursor + 46:cursor + 46 + name_size]
        raw_text = raw_name.decode("utf-8" if flags & 0x800 else "cp437")
        _archive_path(raw_text, max_depth=max_depth)
        local_offset = fields[16]
        if local_offset + 30 > directory_offset:
            raise ValueError("ZIP local header exceeds its permitted area")
        local = struct.unpack_from("<4s5H3I2H", data, local_offset)
        if local[0] != b"PK\x03\x04":
            raise ValueError("Invalid ZIP local header")
        local_name_size, local_extra_size = local[9], local[10]
        content_start = local_offset + 30 + local_name_size + local_extra_size
        if content_start + fields[8] > directory_offset or data[local_offset + 30:local_offset + 30 + local_name_size] != raw_name:
            raise ValueError("ZIP local name or extent disagrees with its directory")
        if local[2] != flags:
            raise ValueError("ZIP local flags disagree with its directory")
        cursor = next_member
    if cursor != offset:
        raise ValueError("ZIP central directory has unparsed trailing records")
    result = []
    seen: set[str] = set()
    total = 0
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = archive.infolist()
            if len(members) != entries or len(members) > max_members:
                raise ValueError("ZIP directory count is inconsistent")
            for member in members:
                key = _archive_path(member.filename, max_depth=max_depth)
                if key in seen:
                    raise ValueError("Archive member names collide after safe normalization")
                seen.add(key)
                mode = member.external_attr >> 16
                if stat.S_IFMT(mode) not in {0, stat.S_IFREG, stat.S_IFDIR}:
                    raise ValueError("Archive links and special device entries are prohibited")
                if member.file_size > max_member_bytes:
                    raise ValueError("Archive member exceeds its uncompressed byte budget")
                if member.file_size > max(1, member.compress_size) * max_ratio:
                    raise ValueError("Archive member exceeds its declared compression-ratio budget")
                total += member.file_size
                if total > max_uncompressed_bytes:
                    raise ValueError("Archive exceeds its aggregate uncompressed byte budget")
                if member.header_offset < 0 or member.header_offset >= directory_offset:
                    raise ValueError("Archive member points outside the local-file area")
                result.append({"name": member.filename, "compressed_bytes": member.compress_size,
                               "uncompressed_bytes": member.file_size, "encrypted": bool(member.flag_bits & 1),
                               "directory": member.is_dir(), "crc32_declared": f"{member.CRC:08x}",
                               "nested_archive": Path(member.filename).suffix.lower() in {".zip", ".7z", ".rar", ".gz", ".bz2", ".xz", ".tar"}})
    except zipfile.BadZipFile as exc:
        raise ValueError("Malformed ZIP container") from exc
    return {"members": result, "member_count": len(result), "total_uncompressed_bytes_declared": total,
            "extraction_performed": False, "recursion_performed": False, "content_crc_verified": False,
            "sha256": hashlib.sha256(data).hexdigest()}
