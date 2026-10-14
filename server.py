#!/usr/bin/env python3
"""ArcDossier v0.5 — Arc ecosystem research service.

Stdlib only. Serves the static product and its evidence-first research APIs.

  * /api/chain     — live Arc RPC snapshot for Arc mainnet and Arc testnet
  * /api/probe     — server-side fetch of a source page, with a content receipt
  * /api/dossier   — evidence assembly: RPC proof of Arc deployment on both
                     networks + live source probes + a transparent score

Deployment reads PORT and ARCDOSSIER_HOST from the environment. A command-line
port remains available for maintenance and testing.

Endpoints can be overridden with ARC_RPC_MAINNET / ARC_RPC_TESTNET.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from knowledge_base import KnowledgeBase

VERSION = "0.5"
DEFAULT_PORT = int(os.environ.get("PORT", "8080"))
DEFAULT_HOST = os.environ.get("ARCDOSSIER_HOST", "0.0.0.0")
USER_AGENT = "ArcDossier/0.5 (+https://arcdossier.site)"
DOCS_ROOT = "https://docs.arc.io"

NETWORKS = {
    "mainnet": {
        "label": "Arc",
        "rpc": os.environ.get("ARC_RPC_MAINNET", "https://rpc.mainnet.arc.io"),
        "chainId": 5042,
        "chainIdHex": "0x13b2",
        "explorer": "https://explorer.arc.io",
    },
    "testnet": {
        "label": "Arc Testnet",
        "rpc": os.environ.get("ARC_RPC_TESTNET", "https://rpc.testnet.arc.io"),
        "chainId": 5042002,
        "chainIdHex": "0x4cef52",
        "explorer": "https://explorer.testnet.arc.io",
    },
}
NETWORK_ORDER = ["mainnet", "testnet"]

RPC_TIMEOUT = 12
FETCH_TIMEOUT = 10
MAX_BODY = 512 * 1024
MAX_REDIRECTS = 4
PROBE_CACHE_TTL = 300
# Token activity windows are coarse by nature and a scan costs many RPC calls, so
# they are cached longer than a plain page probe. "Re-check live" still forces a rescan.
TOKEN_CACHE_TTL = 900
CHAIN_CACHE_TTL = 15
PROBE_RATE_LIMIT = 40          # probes per minute, per process
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_DIR = os.path.join(STATIC_DIR, "data", "research_package")
KNOWLEDGE_DB = os.environ.get("ARCDOSSIER_DB", os.path.join(STATIC_DIR, "data", "arcdossier.sqlite3"))
KNOWLEDGE = KnowledgeBase(KNOWLEDGE_DB, package_dir=KNOWLEDGE_DIR)


def load_dotenv(path: str = None) -> int:
    """Read KEY=VALUE lines from a private .env file into the environment.

    Keeps the secret out of shell history and out of the source tree: the file is
    git-ignored, and anything already exported in the real environment wins.
    """
    path = path or os.path.join(STATIC_DIR, ".env")
    if not os.path.exists(path):
        return 0
    loaded = 0
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, _, value = line.partition("=")
                name = name.strip()
                value = value.strip().strip('"').strip("'")
                if name and name not in os.environ:
                    os.environ[name] = value
                    loaded += 1
    except OSError:
        return 0
    return loaded


DOTENV_LOADED = load_dotenv()

# This machine's egress resolves public hosts through a transparent proxy inside
# 198.18.0.0/15 — an IANA benchmarking range that Python's ipaddress module
# reports as "private". Without this override every probe would be rejected as
# SSRF. Loopback, RFC1918, link-local and reserved stay blocked.
ALLOW_PROXY_RANGE = True
PROXY_NET = ipaddress.ip_network("198.18.0.0/15")

STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}

# Bundled webfonts. Redistribution is permitted under the SIL Open Font
# License 1.1; the licence texts ship alongside the files in fonts/.
FONT_DIR = "fonts"
FONT_FILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.(woff2|txt|json)$")
FONT_MIME = {
    ".woff2": "font/woff2",
    ".txt": "text/plain; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}

# --------------------------------------------------------------------------
# Curated catalog
# --------------------------------------------------------------------------
# Addresses are re-verified with eth_getCode at request time; a catalog entry
# that fails its own check is reported as a failed check, not as a fact. Source
# for every address below: the Arc documentation at https://docs.arc.io

OFFICIAL_SOCIAL = {"arc": "Arc Network"}

# arc.io is the canonical website: the official X profile declares arc.io, and
# arc.network redirects to it. Both names resolve to the same curated entry so an
# alias never produces a weaker dossier than the canonical name.
_ARC_ENTRY = {
    "name": "Arc Network",
    "description": "Circle's USDC-native L1 for stablecoin finance. The official Arc surface.",
    "website": "https://arc.io",
    "docs": "https://docs.arc.io",
    "social": "https://x.com/arc",
}
OFFICIAL_SURFACES = {
    "arc.io": _ARC_ENTRY,
    "www.arc.io": _ARC_ENTRY,
    "arc.network": _ARC_ENTRY,
    "www.arc.network": _ARC_ENTRY,
}

KNOWN_CONTRACTS = {
    "0x3600000000000000000000000000000000000000": ("USDC (ERC-20 interface, 6 decimals)", DOCS_ROOT),
    "0x89b50855aa3be2f677cd6303cec089b5f319d72a": ("EURC (6 decimals)", DOCS_ROOT),
    "0xe9185f0c5f296ed1797aae4238d26ccabeadb86c": ("USYC", DOCS_ROOT),
    "0xf0c4a4ce82a5746abaad9425360ab04fbba432bf": ("cirBTC (8 decimals)", DOCS_ROOT),
    "0x2c4047028a72803939b6fb674d01bc059b5c4961": ("Bridged WETH (18 decimals)", DOCS_ROOT),
    "0x8fe6b999dc680ccfdd5bf7eb0974218be2542daa": ("CCTP TokenMessengerV2", DOCS_ROOT),
    "0xe737e5cebeeba77efe34d4aa090756590b1ce275": ("CCTP MessageTransmitterV2", DOCS_ROOT),
    "0xb43db544e2c27092c107639ad201b3defabcf192": ("CCTP TokenMinterV2", DOCS_ROOT),
    "0x0077777d7eba4688bdef3e311b846f25870a19b9": ("Gateway Wallet", DOCS_ROOT),
    "0x0022222abe238cc2c7bb1f21003f0a260052475b": ("Gateway Minter", DOCS_ROOT),
    "0x8004a818bfb912233c491871b3d84c89a494bd9e": ("ERC-8004 IdentityRegistry", DOCS_ROOT),
    "0x8004b663056a597dffe9eccc1965a193b7388713": ("ERC-8004 ReputationRegistry", DOCS_ROOT),
    "0x8004cb1bf31daf7788923b405b754f57aceb4272": ("ERC-8004 ValidationRegistry", DOCS_ROOT),
    "0x522faf9a91c41c443c66765030741e4aace147d0": ("Multicall3From", DOCS_ROOT),
    "0xca11bde05977b3631167028862be2a173976ca11": ("Multicall3", DOCS_ROOT),
    "0x000000000022d473030f116ddee9f6b43ac78ba3": ("Permit2", DOCS_ROOT),
}

# Documented heuristic, not a proof: known non-Arc surfaces stop at the gate.
NON_ARC_MARKERS = [
    "solana.com", "ethereum.org", "base.org", "polygon.technology",
    "arbitrum.io", "optimism.io", "sui.io", "aptosfoundation.org", "bitcoin.org",
]

ECOSYSTEM_TOKENS = ["arc.io", "arc.network", "docs.arc.io", "arc testnet", "arc mainnet"]

# --------------------------------------------------------------------------
# Caches and rate limiting
# --------------------------------------------------------------------------

_cache_lock = threading.Lock()
_probe_cache: dict = {}
_chain_cache: dict = {}
_probe_times: list = []


def _cache_get(cache: dict, key: str, ttl: int):
    with _cache_lock:
        hit = cache.get(key)
    if hit and (time.time() - hit["at"]) < ttl:
        return hit["value"]
    return None


def _cache_put(cache: dict, key: str, value):
    with _cache_lock:
        cache[key] = {"at": time.time(), "value": value}


def _rate_ok() -> bool:
    now = time.time()
    with _cache_lock:
        _probe_times[:] = [t for t in _probe_times if now - t < 60]
        if len(_probe_times) >= PROBE_RATE_LIMIT:
            return False
        _probe_times.append(now)
    return True


# --------------------------------------------------------------------------
# Arc RPC
# --------------------------------------------------------------------------

class RpcError(Exception):
    pass


def rpc_call(network: str, method: str, params: list):
    """One JSON-RPC call against an Arc endpoint. Returns (result, latency_ms)."""
    endpoint = NETWORKS[network]["rpc"]
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"content-type": "application/json", "user-agent": USER_AGENT},
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=RPC_TIMEOUT) as response:
            raw = response.read(4 * 1024 * 1024)
    except urllib.error.HTTPError as exc:
        raise RpcError("HTTP %s from %s" % (exc.code, NETWORKS[network]["rpc"]))
    except Exception as exc:
        raise RpcError("%s unreachable: %s" % (NETWORKS[network]["rpc"], exc.__class__.__name__))
    latency = round((time.time() - started) * 1000)
    try:
        decoded = json.loads(raw.decode("utf-8", "replace"))
    except ValueError:
        raise RpcError("non-JSON payload from RPC")
    if decoded.get("error"):
        raise RpcError(decoded["error"].get("message", "unknown RPC error"))
    return decoded.get("result"), latency


def chain_snapshot(fresh: bool = False) -> dict:
    """Live read of both networks. Cached briefly so the UI can poll cheaply."""
    if not fresh:
        cached = _cache_get(_chain_cache, "chains", CHAIN_CACHE_TTL)
        if cached:
            return cached
    checked_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    networks = []
    for key in NETWORK_ORDER:
        config = NETWORKS[key]
        entry = {
            "key": key,
            "label": config["label"],
            "expectedChainId": config["chainId"],
            "rpc": config["rpc"],
            "rpcHost": urllib.parse.urlparse(config["rpc"]).netloc,
            "explorer": config["explorer"],
        }
        try:
            chain_id, latency = rpc_call(key, "eth_chainId", [])
            head, _ = rpc_call(key, "eth_blockNumber", [])
            version, _ = rpc_call(key, "web3_clientVersion", [])
            actual = int(chain_id, 16)
            entry.update(
                {
                    "ok": actual == config["chainId"],
                    "chainId": actual,
                    "chainIdHex": chain_id,
                    "blockNumber": int(head, 16),
                    "latencyMs": latency,
                    "clientVersion": version,
                }
            )
            if actual != config["chainId"]:
                entry["error"] = "chainId mismatch: expected %s, got %s" % (config["chainId"], actual)
        except RpcError as exc:
            entry.update({"ok": False, "error": str(exc)})
        networks.append(entry)
    snapshot = {"checkedAt": checked_at, "networks": networks}
    _cache_put(_chain_cache, "chains", snapshot)
    return snapshot


# ERC-20 read selectors.
SELECTOR_DECIMALS = "0x313ce567"
SELECTOR_SYMBOL = "0x95d89b41"
SELECTOR_NAME = "0x06fdde03"


def _decode_abi_string(hexdata: str) -> str:
    """Decode a string return value that is either a dynamic string or bytes32."""
    if not hexdata or hexdata == "0x":
        return ""
    try:
        raw = bytes.fromhex(hexdata[2:])
    except ValueError:
        return ""
    if len(raw) == 32:
        return raw.rstrip(b"\x00").decode("utf-8", "replace").strip()
    if len(raw) >= 64:
        offset = int.from_bytes(raw[:32], "big")
        if offset + 32 <= len(raw):
            length = int.from_bytes(raw[offset:offset + 32], "big")
            chunk = raw[offset + 32:offset + 32 + length]
            return chunk.decode("utf-8", "replace").strip()
    return ""


def erc20_metadata(network: str, address: str) -> dict:
    """Read symbol/name/decimals on-chain. Absence of these is not an error."""
    meta = {"readOn": network, "networkLabel": NETWORKS[network]["label"]}
    try:
        decimals_raw, _ = rpc_call(network, "eth_call", [{"to": address, "data": SELECTOR_DECIMALS}, "latest"])
        meta["decimals"] = int(decimals_raw, 16)
    except (RpcError, ValueError):
        pass
    for field, selector in (("symbol", SELECTOR_SYMBOL), ("name", SELECTOR_NAME)):
        try:
            raw, _ = rpc_call(network, "eth_call", [{"to": address, "data": selector}, "latest"])
            value = _decode_abi_string(raw)
            if value:
                meta[field] = value
        except RpcError:
            pass
    return meta if any(key in meta for key in ("decimals", "symbol", "name")) else {}


def contract_evidence(address: str, fresh: bool = False) -> dict:
    """Prove or disprove an Arc deployment by reading bytecode on both networks."""
    key = "code:" + address.lower()
    if not fresh:
        cached = _cache_get(_probe_cache, key, PROBE_CACHE_TTL)
        if cached:
            return cached

    checked_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    record = {
        "address": address,
        "checkedAt": checked_at,
        "networks": {},
        "explorerUrls": {
            key: "%s/address/%s" % (NETWORKS[key]["explorer"], address) for key in NETWORK_ORDER
        },
    }
    deployed_on = []
    for network in NETWORK_ORDER:
        entry = {"network": network, "label": NETWORKS[network]["label"]}
        try:
            code, latency = rpc_call(network, "eth_getCode", [address, "latest"])
            head, _ = rpc_call(network, "eth_blockNumber", [])
            size = max(0, (len(code) - 2) // 2) if code else 0
            entry.update(
                {
                    "ok": True,
                    "deployed": size > 0,
                    "bytecodeBytes": size,
                    "checkedAtBlock": int(head, 16),
                    "latencyMs": latency,
                    "bytecodeHash": "0x" + hashlib.sha256(code.encode()).hexdigest(),
                }
            )
            if size:
                deployed_on.append(network)
        except RpcError as exc:
            entry.update({"ok": False, "error": str(exc)})
        record["networks"][network] = entry

    record["deployedOn"] = deployed_on

    if "mainnet" in deployed_on:
        record["verdict"] = "Bytecode found at this address on Arc mainnet — the address is a contract on Arc."
    elif "testnet" in deployed_on:
        record["verdict"] = "Bytecode found on Arc testnet only. No contract at this address on Arc mainnet."
    elif any(item.get("ok") for item in record["networks"].values()):
        record["verdict"] = "No bytecode at this address on Arc mainnet or testnet. Either an externally owned account, or a contract on a different chain."
    else:
        record["verdict"] = "Arc RPC could not be reached for this check."

    known = KNOWN_CONTRACTS.get(address.lower())
    if known:
        record["knownAs"] = known[0]
        record["knownSource"] = known[1]

    read_on = "mainnet" if "mainnet" in deployed_on else ("testnet" if "testnet" in deployed_on else None)
    if read_on:
        meta = erc20_metadata(read_on, address)
        if meta:
            record["erc20"] = meta
            if address.lower() == "0x3600000000000000000000000000000000000000":
                record["erc20"]["note"] = (
                    "Native USDC gas accounting uses 18 decimals; this ERC-20 interface reports 6. "
                    "They are the same balance — never add them as two rows."
                )
    _cache_put(_probe_cache, key, record)
    return record


# --------------------------------------------------------------------------
# Live source probe
# --------------------------------------------------------------------------

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


class ProbeError(Exception):
    pass


def _assert_fetchable(url: str):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ProbeError("only http and https are fetched")
    host = parsed.hostname
    if not host:
        raise ProbeError("no host in URL")
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror:
        raise ProbeError("host does not resolve: %s" % host)
    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        if ALLOW_PROXY_RANGE and address in PROXY_NET:
            continue
        if (
            address.is_loopback
            or address.is_private
            or address.is_link_local
            or address.is_reserved
            or address.is_multicast
            or address.is_unspecified
        ):
            raise ProbeError("refusing to fetch a non-public address (%s)" % address)


_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_DESC_RE = re.compile(
    r'<meta[^>]+(?:name|property)=["\'](?:description|og:description|og:title)["\'][^>]*content=["\'](.*?)["\']',
    re.I | re.S,
)
_DESC_RE_REVERSED = re.compile(
    r'<meta[^>]+content=["\'](.*?)["\'][^>]*(?:name|property)=["\'](?:description|og:description)["\']',
    re.I | re.S,
)
_TAG_RE = re.compile(r"<[^>]+>")
_LINK_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)
_DOCS_HINT_RE = re.compile(r"(^|\.)docs\.|/docs?(/|$)|documentation", re.I)
_REPO_RE = re.compile(r"^https?://(www\.)?github\.com/[^/]+/[^/?#]+$", re.I)


def discover_links(text: str, base: str) -> dict:
    """Follow only links the page actually publishes — never guess a URL."""
    found = {"docs": None, "github": None}
    for href in _LINK_RE.findall(text):
        if href.startswith(("#", "mailto:", "javascript:")):
            continue
        absolute = urllib.parse.urljoin(base, href)
        parsed = urllib.parse.urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            continue
        if not found["docs"] and _DOCS_HINT_RE.search(parsed.path or "/"):
            found["docs"] = absolute.split("#")[0]
        if not found["github"] and _REPO_RE.match(absolute.split("#")[0]):
            found["github"] = absolute.split("#")[0]
    return found


def _clean(text: str, limit: int = 220) -> str:
    text = _TAG_RE.sub(" ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def probe_url(url: str, fresh: bool = False) -> dict:
    """Fetch a page server-side and return a receipt for what actually came back."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    key = "probe:" + url
    if not fresh:
        cached = _cache_get(_probe_cache, key, PROBE_CACHE_TTL)
        if cached:
            return cached
    if not _rate_ok():
        return {"ok": False, "url": url, "error": "probe rate limit reached, wait a moment"}

    record = {"url": url, "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    current = url
    started = time.time()
    try:
        for _ in range(MAX_REDIRECTS + 1):
            _assert_fetchable(current)
            request = urllib.request.Request(
                current,
                headers={
                    "user-agent": USER_AGENT,
                    "accept": "text/html,application/xhtml+xml,application/json;q=0.8,*/*;q=0.5",
                    "accept-language": "en-US,en;q=0.9",
                },
            )
            try:
                response = _OPENER.open(request, timeout=FETCH_TIMEOUT)
            except urllib.error.HTTPError as exc:
                if exc.code in (301, 302, 303, 307, 308):
                    location = exc.headers.get("Location")
                    if not location:
                        record.update({"ok": False, "httpStatus": exc.code, "error": "redirect without Location"})
                        break
                    current = urllib.parse.urljoin(current, location)
                    continue
                body = b""
                try:
                    body = exc.read(MAX_BODY)
                except Exception:
                    pass
                record.update(
                    {
                        "ok": False,
                        "httpStatus": exc.code,
                        "finalUrl": current,
                        "error": "source returned HTTP %s" % exc.code,
                    }
                )
                if body:
                    record["bodySha256"] = "sha256:" + hashlib.sha256(body).hexdigest()
                break
            with response:
                body = response.read(MAX_BODY + 1)
                truncated = len(body) > MAX_BODY
                body = body[:MAX_BODY]
                charset = response.headers.get_content_charset() or "utf-8"
                text = body.decode(charset, "replace")
                title_match = _TITLE_RE.search(text)
                desc_match = _DESC_RE.search(text) or _DESC_RE_REVERSED.search(text)
                lowered = text.lower()
                mentions = sorted({token for token in ECOSYSTEM_TOKENS if token in lowered})
                record.update(
                    {
                        "ok": True,
                        "httpStatus": response.status,
                        "finalUrl": response.geturl(),
                        "contentType": response.headers.get("content-type", ""),
                        "bytes": len(body),
                        "truncated": truncated,
                        "title": _clean(title_match.group(1), 160) if title_match else "",
                        "description": _clean(desc_match.group(1), 240) if desc_match else "",
                        "bodySha256": "sha256:" + hashlib.sha256(body).hexdigest(),
                        "ecosystemMentions": mentions,
                        "discovered": discover_links(text, response.geturl()),
                        "surfaces": extract_surfaces(text, response.geturl()),
                        "selfReported": extract_self_reported(text),
                    }
                )
                break
        else:
            record.update({"ok": False, "error": "too many redirects"})
    except ProbeError as exc:
        record.update({"ok": False, "error": str(exc)})
    except socket.timeout:
        record.update({"ok": False, "error": "source timed out"})
    except Exception as exc:
        record.update({"ok": False, "error": "%s: %s" % (exc.__class__.__name__, exc)})
    record["elapsedMs"] = round((time.time() - started) * 1000)
    _cache_put(_probe_cache, key, record)
    return record


# --------------------------------------------------------------------------
# Deterministic token metrics
# --------------------------------------------------------------------------
# Trader-facing facts read straight from the chain. Nothing here involves a
# model: every value is either a decoded eth_call result or a count of logs the
# server actually retrieved. Window-based figures are labelled as such, because
# a bounded log scan is not a holder snapshot.

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

ERC20_CALLS = {
    "totalSupply": "0x18160ddd",
    "decimals": "0x313ce567",
    "symbol": "0x95d89b41",
    "name": "0x06fdde03",
}

# Structural probes. Each one is an actual eth_call: a decodable answer is far
# stronger evidence than finding four bytes in the bytecode, because a selector
# can appear in a contract purely as data.
STRUCTURE_PROBES = {
    "implementation": ("0x5c60da1b", "address"),
    "owner": ("0x8da5cb5b", "address"),
    "admin": ("0xf851a440", "address"),
    "paused": ("0x5c975abb", "bool"),
}

# Quick screens trade window length for latency: fewer RPC calls, shorter history.
SCAN_PROFILES = {
    "quick": {"max_calls": 5, "max_span": 8000, "log_budget": 6000, "max_seconds": 12},
    "deep": {"max_calls": 14, "max_span": 60000, "log_budget": 20000, "max_seconds": 30},
}
SCAN_START_CHUNK = 2000
SCAN_MIN_CHUNK = 250
SCAN_MAX_CHUNK = 5000
SCAN_MAX_CALLS = 14
SCAN_MAX_SPAN = 60000
SCAN_LOG_BUDGET = 20000
SCAN_MAX_SECONDS = 30
BLOCKS_ARE_HALF_SECOND = 0.5


def _decode_address(word: str):
    if not word or word == "0x" or len(word) < 42:
        return None
    candidate = "0x" + word[-40:]
    return None if candidate.lower() == ZERO_ADDRESS else candidate


def _decode_bool(word: str):
    if not word or word == "0x":
        return None
    try:
        return int(word, 16) != 0
    except ValueError:
        return None


def _eth_call(network: str, address: str, data: str):
    result, _ = rpc_call(network, "eth_call", [{"to": address, "data": data}, "latest"])
    return result


def format_units(value: int, decimals: int) -> str:
    """Compact human-readable amount. Exact integers stay in the raw fields."""
    if decimals <= 0:
        return "{:,}".format(value)
    scale = 10 ** decimals
    whole, fraction = divmod(value, scale)
    if whole >= 10 ** 12:
        return "%.2fT" % (whole / 10 ** 12)
    if whole >= 10 ** 9:
        return "%.2fB" % (whole / 10 ** 9)
    if whole >= 10 ** 6:
        return "%.2fM" % (whole / 10 ** 6)
    if whole >= 10 ** 3:
        return "%.2fK" % (whole / 10 ** 3)
    if fraction == 0:
        return "{:,}".format(whole)
    digits = ("%0*d" % (decimals, fraction)).rstrip("0")
    return "{:,}.{}".format(whole, digits[:6])


def scan_transfers(network: str, address: str, profile: str = "deep") -> dict:
    """Walk backwards through Transfer logs with adaptive chunking.

    The endpoint's result cap is dynamic — the same block span can succeed or be
    rejected minutes apart — so this backs off on the documented range errors and
    reports exactly which blocks it managed to cover.
    """
    plan = SCAN_PROFILES.get(profile) or SCAN_PROFILES["deep"]
    head, _ = rpc_call(network, "eth_blockNumber", [])
    head = int(head, 16)

    logs = []
    chunk = SCAN_START_CHUNK
    cursor = head
    covered_from = head
    calls = 0
    capped_by = None
    chunks_done = 0
    scan_failed = False
    started = time.time()

    while calls < plan["max_calls"] and (head - cursor) < plan["max_span"]:
        if time.time() - started > plan["max_seconds"]:
            capped_by = "time_budget"
            break
        from_block = max(0, cursor - chunk + 1)
        calls += 1
        batch = None
        for attempt in range(3):
            try:
                batch, _ = rpc_call(
                    network,
                    "eth_getLogs",
                    [{
                        "fromBlock": hex(from_block),
                        "toBlock": hex(cursor),
                        "address": address,
                        "topics": [TRANSFER_TOPIC],
                    }],
                )
                batch = batch or []
                break
            except RpcError as exc:
                message = str(exc)
                if "range" in message or "results" in message:
                    if chunk <= SCAN_MIN_CHUNK:
                        capped_by = "rpc_result_cap"
                        break
                    chunk = max(SCAN_MIN_CHUNK, chunk // 2)
                    batch = "shrink"
                    break
                # Transient throttling surfaces as a non-JSON body; back off.
                if attempt < 2:
                    time.sleep(0.6 * (attempt + 1))
                    continue
                capped_by = "rpc_error"
                scan_failed = chunks_done == 0
                break
        if batch == "shrink":
            continue
        if batch is None:
            break

        logs.extend(batch)
        covered_from = from_block
        cursor = from_block - 1
        chunks_done += 1
        if len(logs) >= plan["log_budget"]:
            capped_by = "log_budget"
            break
        if len(batch) < 200 and chunk < SCAN_MAX_CHUNK:
            chunk = min(SCAN_MAX_CHUNK, chunk * 2)
        time.sleep(0.15)

    if capped_by is None:
        capped_by = "call_budget"

    def timestamp_of(block_number: int):
        try:
            block, _ = rpc_call(network, "eth_getBlockByNumber", [hex(block_number), False])
            return int(block["timestamp"], 16) if block else None
        except (RpcError, KeyError, TypeError):
            return None

    return {
        "logs": logs,
        "headBlock": head,
        "fromBlock": covered_from,
        "toBlock": head,
        "blocksCovered": head - covered_from + 1,
        "rpcCalls": calls,
        "cappedBy": capped_by,
        "fromTimestamp": timestamp_of(covered_from),
        "toTimestamp": timestamp_of(head),
        "finalChunk": chunk,
        "scanFailed": scan_failed,
        "profile": profile,
    }


def token_metrics(address: str, fresh: bool = False, profile: str = "deep") -> dict:
    """Identity, contract structure and a bounded activity window for a token."""
    key = "metrics:%s:%s" % (profile, address.lower())
    if not fresh:
        cached = _cache_get(_probe_cache, key, TOKEN_CACHE_TTL)
        if cached:
            return cached

    record = {
        "address": address,
        "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "networks": {},
    }

    for network in NETWORK_ORDER:
        entry = {"network": network, "label": NETWORKS[network]["label"]}
        try:
            code, _ = rpc_call(network, "eth_getCode", [address, "latest"])
        except RpcError as exc:
            entry["error"] = str(exc)
            record["networks"][network] = entry
            continue
        if not code or code == "0x":
            entry["deployed"] = False
            record["networks"][network] = entry
            continue

        entry["deployed"] = True

        identity = {}
        try:
            raw = _eth_call(network, address, ERC20_CALLS["decimals"])
            identity["decimals"] = int(raw, 16)
        except (RpcError, ValueError, TypeError):
            pass
        for field, selector in (("symbol", "symbol"), ("name", "name")):
            try:
                value = _decode_abi_string(_eth_call(network, address, ERC20_CALLS[selector]))
                if value:
                    identity[field] = value
            except RpcError:
                pass
        try:
            raw = _eth_call(network, address, ERC20_CALLS["totalSupply"])
            supply = int(raw, 16)
            identity["totalSupplyRaw"] = str(supply)
            if identity.get("decimals") is not None:
                identity["totalSupply"] = format_units(supply, identity["decimals"])
        except (RpcError, ValueError, TypeError):
            pass
        entry["identity"] = identity

        structure = []
        for name, (selector, kind) in STRUCTURE_PROBES.items():
            probe = {"name": name, "selector": selector}
            try:
                raw = _eth_call(network, address, selector)
            except RpcError as exc:
                probe.update({"callable": False, "reason": str(exc)})
                structure.append(probe)
                continue
            if raw is None or raw == "0x":
                probe.update({"callable": False, "reason": "no return value"})
            elif kind == "address":
                decoded = _decode_address(raw)
                probe.update({"callable": True, "value": decoded})
                if decoded is None:
                    probe["reason"] = "returns the zero address"
            else:
                decoded = _decode_bool(raw)
                probe.update({"callable": decoded is not None, "value": decoded})
            structure.append(probe)
        entry["structure"] = structure

        scan = scan_transfers(network, address, profile=profile)
        logs = scan.pop("logs")
        decimals = identity.get("decimals")
        supply = int(identity["totalSupplyRaw"]) if identity.get("totalSupplyRaw") else None

        senders, receivers, net = set(), set(), {}
        mints = burns = 0
        large = 0
        large_threshold = (supply // 100) if supply else None
        for log in logs:
            topics = log.get("topics") or []
            if len(topics) < 3:
                continue
            source = "0x" + topics[1][-40:]
            target = "0x" + topics[2][-40:]
            try:
                value = int(log.get("data", "0x0"), 16)
            except ValueError:
                value = 0
            senders.add(source)
            receivers.add(target)
            if source.lower() == ZERO_ADDRESS:
                mints += 1
            else:
                net[source] = net.get(source, 0) - value
            if target.lower() == ZERO_ADDRESS:
                burns += 1
            else:
                net[target] = net.get(target, 0) + value
            if large_threshold and value >= large_threshold:
                large += 1

        duration_minutes = None
        if scan.get("fromTimestamp") and scan.get("toTimestamp"):
            duration_minutes = max(1, round((scan["toTimestamp"] - scan["fromTimestamp"]) / 60))

        movers = sorted(
            ({"address": key, "netRaw": str(value),
              "net": format_units(value, decimals) if decimals is not None else str(value)}
             for key, value in net.items() if value > 0),
            key=lambda item: int(item["netRaw"]),
            reverse=True,
        )[:5]

        gross_inflow = sum(value for value in net.values() if value > 0)
        for mover in movers:
            mover["sharePct"] = round(100 * int(mover["netRaw"]) / gross_inflow, 2) if gross_inflow else None

        scan_failed = scan.get("scanFailed", False)
        entry["activity"] = {
            "scanFailed": scan_failed,
            "transfers": len(logs),
            "uniqueSenders": len(senders),
            "uniqueReceivers": len(receivers),
            "uniqueAddresses": len(senders | receivers),
            "mints": mints,
            "burns": burns,
            "largeTransfers": large,
            "largeThreshold": format_units(large_threshold, decimals) if (large_threshold and decimals is not None) else None,
            "durationMinutes": duration_minutes,
            "transfersPerMinute": round(len(logs) / duration_minutes, 2) if duration_minutes else None,
            "topNetInflow": movers,
            "window": {
                "profile": scan.get("profile"),
                "fromBlock": scan["fromBlock"],
                "toBlock": scan["toBlock"],
                "blocksCovered": scan["blocksCovered"],
                "fromTimestamp": scan["fromTimestamp"],
                "toTimestamp": scan["toTimestamp"],
                "rpcCalls": scan["rpcCalls"],
                "cappedBy": scan["cappedBy"],
                "estimatedMinutes": round(scan["blocksCovered"] * BLOCKS_ARE_HALF_SECOND / 60, 1),
            },
            "caveat": "Window-based activity from a bounded log scan. This is not a holder snapshot and not a full history.",
        }

        signals = []
        implementation = next((p for p in structure if p["name"] == "implementation"), {})
        owner = next((p for p in structure if p["name"] == "owner"), {})
        admin = next((p for p in structure if p["name"] == "admin"), {})
        paused = next((p for p in structure if p["name"] == "paused"), {})

        if implementation.get("value"):
            signals.append({
                "id": "upgradeable",
                "severity": "watch",
                "label": "Upgradeable proxy",
                "detail": "Contract logic can be replaced by the proxy admin. The implementation address is %s." % implementation["value"],
            })
        if owner.get("value"):
            signals.append({
                "id": "owner",
                "severity": "watch",
                "label": "Owner role present",
                "detail": "owner() returns %s. Whoever controls that address holds any owner-restricted power." % owner["value"],
            })
        if admin.get("value") and admin.get("value") != owner.get("value"):
            signals.append({
                "id": "admin",
                "severity": "watch",
                "label": "Separate proxy admin",
                "detail": "admin() returns %s, which is a different address from the owner." % admin["value"],
            })
        if paused.get("callable"):
            signals.append({
                "id": "pausable",
                "severity": "watch" if paused.get("value") else "info",
                "label": "Pausable transfers",
                "detail": "paused() is callable and currently returns %s. Transfers can be halted by the operator." % ("true" if paused.get("value") else "false"),
            })
        if mints:
            signals.append({
                "id": "mint-observed",
                "severity": "risk",
                "label": "Minting observed in window",
                "detail": "%d of the %d transfers in the scanned window came from the zero address, which is supply being created." % (mints, len(logs)),
            })
        elif not scan_failed:
            signals.append({
                "id": "mint-not-seen",
                "severity": "info",
                "label": "No minting in window",
                "detail": "No transfer originated from the zero address in the scanned window. This does not prove the supply cannot be minted.",
            })
        if burns:
            signals.append({
                "id": "burn-observed",
                "severity": "info",
                "label": "Burning observed in window",
                "detail": "%d transfers went to the zero address in the scanned window." % burns,
            })
        if len(logs) == 0 and scan_failed:
            signals.append({
                "id": "scan-incomplete",
                "severity": "info",
                "label": "Log scan incomplete",
                "detail": "The RPC refused every log query for this contract, so activity could not be measured. No conclusion about activity is drawn.",
            })
        elif len(logs) == 0:
            signals.append({
                "id": "no-activity",
                "severity": "risk",
                "label": "No transfers in window",
                "detail": "The scanned window of %s blocks contains no Transfer events for this contract." % entry["activity"]["window"]["blocksCovered"],
            })
        elif len(senders | receivers) and len(logs) / max(1, len(senders | receivers)) >= 20:
            signals.append({
                "id": "activity-concentration",
                "severity": "watch",
                "label": "Activity concentrated in few addresses",
                "detail": "%d transfers across only %d addresses (%.1f per address), which is consistent with bots or self-directed volume rather than broad distribution."
                          % (len(logs), len(senders | receivers), len(logs) / len(senders | receivers)),
            })
        if large:
            signals.append({
                "id": "large-transfers",
                "severity": "watch",
                "label": "Large transfers present",
                "detail": "%d transfers moved at least 1%% of total supply (>= %s) inside the window." % (large, entry["activity"]["largeThreshold"]),
            })
        entry["signals"] = signals
        record["networks"][network] = entry

    _cache_put(_probe_cache, key, record)
    return record


# --------------------------------------------------------------------------
# Explorer facts (Blockscout-compatible API)
# --------------------------------------------------------------------------
# The explorer answers questions the RPC cannot: how many holders exist, how the
# supply is distributed, and whether the source was verified. Only metadata is
# read — never the published source itself.

EXPLORER_TIMEOUT = 15
# Explorer hosts that answered with a bot-protection challenge during this process.
_explorer_blocked = set()
HOLDER_PAGE_SIZE = 50


def explorer_get(network: str, params: dict):
    base = NETWORKS[network]["explorer"] + "/api"
    url = base + "?" + urllib.parse.urlencode(params)
    return _explorer_fetch(url)


def explorer_json(network: str, path: str):
    return _explorer_fetch(NETWORKS[network]["explorer"] + path)


def _explorer_fetch(url: str):
    """The explorer throttles bursts, and a screen makes several lookups in a row.

    Returns None if the data is unavailable for any reason. A Cloudflare bot
    challenge is reported as such rather than silently retried: bypassing it is
    not something this tool should attempt.
    """
    for attempt in range(3):
        request = urllib.request.Request(url, headers={"user-agent": USER_AGENT, "accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=EXPLORER_TIMEOUT) as response:
                return json.loads(response.read(4 * 1024 * 1024).decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                try:
                    body = exc.read(4096).decode("utf-8", "replace")
                except Exception:
                    body = ""
                if "just a moment" in body.lower() or "cf-chl" in body.lower() or "cloudflare" in body.lower():
                    _explorer_blocked.add(urllib.parse.urlparse(url).netloc)
                    return None
            if exc.code in (429, 500, 502, 503) and attempt < 2:
                time.sleep(1.2 * (attempt + 1))
                continue
            return None
        except Exception:
            if attempt < 2:
                time.sleep(0.8 * (attempt + 1))
                continue
            return None
    return None


def explorer_token_facts(network: str, address: str, fresh: bool = False) -> dict:
    """Holder count, supply distribution and verification status for one token."""
    key = "explorer:%s:%s" % (network, address.lower())
    if not fresh:
        cached = _cache_get(_probe_cache, key, TOKEN_CACHE_TTL)
        if cached:
            return cached

    record = {"network": network, "label": NETWORKS[network]["label"], "ok": False}

    info = explorer_json(network, "/api/v2/tokens/" + address)
    host = urllib.parse.urlparse(NETWORKS[network]["explorer"]).netloc
    if host in _explorer_blocked:
        record["unavailable"] = ("The %s explorer is behind a bot-protection challenge and refused automated "
                                 "lookups. Holder data was not read from this network." % host)

    if isinstance(info, dict) and info.get("name"):
        holders_count = info.get("holders_count")
        record.update({
            "ok": True,
            "name": info.get("name"),
            "symbol": info.get("symbol"),
            "decimals": info.get("decimals"),
            "type": info.get("type"),
            "reputation": info.get("reputation"),
            "holdersCount": int(holders_count) if holders_count not in (None, "") else None,
            "totalSupply": info.get("total_supply"),
            "volume24h": info.get("volume_24h"),
            "marketCap": info.get("circulating_market_cap"),
            "iconUrl": info.get("icon_url"),
        })

    source = explorer_get(network, {"module": "contract", "action": "getsourcecode", "address": address})
    try:
        entry = (source or {}).get("result", [{}])[0]
    except (AttributeError, IndexError, TypeError):
        entry = {}
    if isinstance(entry, dict) and (entry.get("ContractName") or entry.get("SourceCode")):
        record["verification"] = {
            "verified": bool(entry.get("SourceCode")),
            "contractName": entry.get("ContractName") or None,
            "compiler": entry.get("CompilerVersion") or None,
            "isProxy": str(entry.get("IsProxy", "")).lower() == "true",
            "license": entry.get("LicenseType") or None,
        }
    elif info is not None:
        record.setdefault("verification", {"verified": False, "contractName": None})

    holders = explorer_json(
        network,
        "/api/v2/tokens/%s/holders?items_count=%d" % (address, HOLDER_PAGE_SIZE),
    )
    items = (holders or {}).get("items") or []
    if items:
        supply = None
        try:
            supply = int(record.get("totalSupply") or 0)
        except (TypeError, ValueError):
            supply = None
        parsed = []
        for item in items:
            holder = item.get("address") or {}
            try:
                value = int(item.get("value") or 0)
            except (TypeError, ValueError):
                value = 0
            parsed.append({
                "address": holder.get("hash"),
                "value": value,
                "isContract": bool(holder.get("is_contract")),
                "sharePct": round(100 * value / supply, 4) if supply else None,
            })
        parsed.sort(key=lambda row: row["value"], reverse=True)

        def top_share(count: int):
            if not supply:
                return None
            return round(100 * sum(row["value"] for row in parsed[:count]) / supply, 2)

        record["distribution"] = {
            "sampleSize": len(parsed),
            "truncated": bool((holders or {}).get("next_page_params")),
            "topHolders": [
                {
                    "address": row["address"],
                    "amount": format_units(row["value"], int(record.get("decimals") or 0) or 0),
                    "sharePct": row["sharePct"],
                    "isContract": row["isContract"],
                }
                for row in parsed[:10]
            ],
            "top1Pct": top_share(1),
            "top10Pct": top_share(10),
            "caveat": "Shares are computed against the token's reported total supply, using the explorer's "
                      "first %d holders." % len(parsed),
        }

    _cache_put(_probe_cache, key, record)
    return record


# --------------------------------------------------------------------------
# Cross-source discovery
# --------------------------------------------------------------------------
# One input should lead to the project's other surfaces. That works from a website
# or an X profile, because both publish outbound links. It does NOT work from a
# contract address: the chain has no registry mapping an address to a website, and
# the explorer publishes token metadata rather than a project home page. Where a
# direction is impossible, the dossier says so instead of guessing.

SOCIAL_LINK_RE = re.compile(r"^https?://(?:www\.)?(?:x\.com|twitter\.com)/([A-Za-z0-9_]{2,20})/?$")
EXTERNAL_LINK_RE = re.compile(r"^https?://([A-Za-z0-9.-]+\.[A-Za-z]{2,})(/.*)?$")
ADDRESS_IN_TEXT_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")

# Paths and hosts on X that are never a project handle, and hosts that are never
# a project website.
X_NON_HANDLES = {
    "i", "home", "explore", "search", "hashtag", "intent", "messages", "notifications",
    "settings", "compose", "login", "signup", "tos", "privacy", "share", "about",
}
NON_PROJECT_HOSTS = {
    "x.com", "twitter.com", "t.co", "github.com", "youtube.com", "youtu.be", "discord.gg",
    "discord.com", "t.me", "telegram.me", "medium.com", "linkedin.com", "reddit.com",
    "facebook.com", "instagram.com", "google.com", "apple.com", "w3.org", "schema.org",
    "gstatic.com", "googleapis.com", "cloudflare.com", "jsdelivr.net", "unpkg.com",
}
# Hosts whose subdomains are platform infrastructure rather than project websites.
# X serves profile images, video and scripts from *.twimg.com; treating those as a
# project's home page was a real bug in the first version of this discovery.
NON_PROJECT_SUFFIXES = (
    "twimg.com", "twitter.com", "x.com", "googleusercontent.com", "gstatic.com",
    "cloudflare.com", "akamaihd.net", "fbcdn.net", "licdn.com", "onion",
)


def is_project_host(host: str) -> bool:
    host = (host or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if not host or host in NON_PROJECT_HOSTS:
        return False
    return not any(host == suffix or host.endswith("." + suffix) for suffix in NON_PROJECT_SUFFIXES)


URL_ANY_RE = re.compile(r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+")
# X renders the profile's website as a React payload with an unquoted key:
#   entities:{url:{urls:[{display_url:"arc.io",expanded_url:"http://arc.io/",...
# so neither an href scan nor a quoted-JSON scan finds it.
BIO_URL_RE = re.compile(r'(?:expanded_url|display_url)\s*:\s*"?(https?://[^",}\s]+|[A-Za-z0-9.-]+\.[A-Za-z]{2,}[^",}\s]*)')
TWO_LABEL_TLDS = {"co.uk", "com.au", "co.jp", "com.br", "co.in", "org.uk", "ac.uk", "com.cn"}


def registrable_domain(host: str) -> str:
    """Collapse subdomains so studio.arc.io and www.arc.io both mean arc.io."""
    host = (host or "").lower().strip(".")
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    if ".".join(parts[-2:]) in TWO_LABEL_TLDS and len(parts) >= 3:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _host_of(url: str) -> str:
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url
    try:
        return (urllib.parse.urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def extract_surfaces(text: str, base: str) -> dict:
    """Pull social handles, candidate project domains and addresses out of a page."""
    social, addresses = [], []
    declared, linked, mentioned = [], [], []
    for href in _LINK_RE.findall(text or ""):
        if href.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue
        absolute = urllib.parse.urljoin(base, href)
        parsed = urllib.parse.urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            continue

        social_match = SOCIAL_LINK_RE.match(absolute.split("?")[0])
        if social_match and social_match.group(1).lower() not in X_NON_HANDLES:
            handle = social_match.group(1)
            if handle not in social:
                social.append(handle)
            continue

        host_match = EXTERNAL_LINK_RE.match(absolute)
        if host_match:
            host = host_match.group(1).lower()
            if is_project_host(host) and host not in linked:
                linked.append(host)

    body = text or ""
    for match in BIO_URL_RE.findall(body):
        host = _host_of(match)
        if is_project_host(host) and host not in declared:
            declared.append(host)
    for match in URL_ANY_RE.findall(body):
        host = _host_of(match)
        if is_project_host(host) and host not in mentioned:
            mentioned.append(host)

    for match in ADDRESS_IN_TEXT_RE.findall(body):
        if match.lower() not in [value.lower() for value in addresses]:
            addresses.append(match)

    # Order: a link the profile declares first, then real hrefs, then any URL that
    # merely appears in the page. Subdomains collapse to one registrable domain,
    # preferring the shortest host seen for it.
    ordered, seen = [], set()
    for host in declared + linked + mentioned:
        root = registrable_domain(host)
        if not root or root in seen:
            continue
        seen.add(root)
        ordered.append(root)

    return {
        "social": social[:5],
        "domains": ordered[:8],
        "declaredDomains": [registrable_domain(h) for h in declared][:5],
        "addresses": addresses[:5],
    }


# --------------------------------------------------------------------------
# Third-party data providers
# --------------------------------------------------------------------------
# Two free sources, matched by the project's own domain and X handle rather than
# by guessing at names:
#
#   DefiLlama  — TVL, category (which is also how product type is detected),
#                chains, market cap, funding rounds, and recorded security incidents
#   CoinGecko  — market cap, FDV, 24h volume, price change, categories
#
# Team identity has no free structured source. RootData would cover it but exposes
# no public API, so that dimension stays unmeasured rather than being filled with
# whatever a website claims about itself.

LLAMA_INDEX_TTL = 1800
GECKO_TTL = 900
_llama_index = {"at": 0.0, "rows": None}


def _norm_host(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = value.split("/")[0].split("?")[0]
    return value[4:] if value.startswith("www.") else value


def _norm_handle(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"^https?://(www\.)?(x\.com|twitter\.com)/", "", value)
    return value.lstrip("@").split("/")[0].split("?")[0]


def llama_index(fresh: bool = False) -> list:
    """Slim index of DefiLlama protocols. The full payload is ~9 MB, so only the
    fields used for matching and display are kept, cached for 30 minutes."""
    with _cache_lock:
        if not fresh and _llama_index["rows"] and (time.time() - _llama_index["at"]) < LLAMA_INDEX_TTL:
            return _llama_index["rows"]
    request = urllib.request.Request("https://api.llama.fi/protocols",
                                     headers={"user-agent": USER_AGENT, "accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            raw = json.loads(response.read(32 * 1024 * 1024).decode("utf-8", "replace"))
    except Exception:
        return _llama_index["rows"] or []
    rows = [
        {
            "name": item.get("name"),
            "slug": item.get("slug") or item.get("id"),
            "category": item.get("category"),
            "chains": item.get("chains") or [],
            "tvl": item.get("tvl"),
            "mcap": item.get("mcap"),
            "change1d": item.get("change_1d"),
            "change7d": item.get("change_7d"),
            "url": item.get("url"),
            "twitter": item.get("twitter"),
            "symbol": item.get("symbol"),
            "listedAt": item.get("listedAt"),
        }
        for item in raw
        if isinstance(item, dict)
    ]
    with _cache_lock:
        _llama_index["rows"] = rows
        _llama_index["at"] = time.time()
    return rows


def llama_match(domain: str = "", handle: str = "", name: str = "") -> dict:
    """Match on the declared domain first, then the X handle, then a name hit.

    Domain and handle matching are exact joins against fields the project itself
    supplied to DefiLlama, so they do not depend on fuzzy name similarity.
    """
    rows = llama_index()
    if not rows:
        return {}
    host = _norm_host(domain)
    if host:
        for row in rows:
            if _norm_host(row.get("url")) == host:
                return {"matchedBy": "website domain", "row": row}
        for row in rows:
            candidate = _norm_host(row.get("url"))
            if candidate and (candidate.endswith("." + host) or host.endswith("." + candidate)):
                return {"matchedBy": "website domain (subdomain)", "row": row}
    handle = _norm_handle(handle)
    if handle:
        for row in rows:
            if _norm_handle(row.get("twitter")) == handle:
                return {"matchedBy": "X handle", "row": row}
    name = (name or "").strip().lower()
    if len(name) >= 4:
        for row in rows:
            if (row.get("name") or "").strip().lower() == name:
                return {"matchedBy": "exact name", "row": row}
    return {}


def llama_fees(slug: str) -> dict:
    """24h/7d/30d fees for a protocol, where DefiLlama tracks them.

    Fees and revenue are the difference between "has TVL" and "has usage", which is
    what the data module is supposed to judge. Absent data returns {} rather than zeros.
    """
    if not slug:
        return {}
    key = "llama:fees:" + slug
    cached = _cache_get(_probe_cache, key, LLAMA_INDEX_TTL)
    if cached is not None:
        return cached
    request = urllib.request.Request(
        "https://api.llama.fi/summary/fees/" + urllib.parse.quote(slug) + "?dataType=dailyFees",
        headers={"user-agent": USER_AGENT, "accept": "application/json"})
    record = {}
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            payload = json.loads(response.read(8 * 1024 * 1024).decode("utf-8", "replace"))
        if isinstance(payload, dict):
            record = {
                "fees24h": payload.get("total24h"),
                "fees7d": payload.get("total7d"),
                "fees30d": payload.get("total30d"),
                "feesChange7dPct": payload.get("change_7d"),
                "revenue24h": payload.get("total24h") if payload.get("dataType") == "dailyRevenue" else None,
            }
            record = {k: v for k, v in record.items() if v is not None}
    except Exception:
        record = {}
    _cache_put(_probe_cache, key, record)
    return record


def llama_detail(slug: str) -> dict:
    """Per-protocol detail: funding rounds and security incidents.

    The bulk /raises endpoint is paid, but the per-protocol field is not, and it
    carries the round, the amount and the sector.
    """
    if not slug:
        return {}
    key = "llama:detail:" + slug
    cached = _cache_get(_probe_cache, key, LLAMA_INDEX_TTL)
    if cached is not None:
        return cached
    request = urllib.request.Request("https://api.llama.fi/protocol/" + urllib.parse.quote(slug),
                                     headers={"user-agent": USER_AGENT, "accept": "application/json"})
    record = {}
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read(16 * 1024 * 1024).decode("utf-8", "replace"))
        raises = payload.get("raises") or []
        hacks = payload.get("hacks") or []
        record = {
            "slug": slug,
            "name": payload.get("name"),
            "url": payload.get("url"),
            "funding": [
                {
                    "date": time.strftime("%Y-%m-%d", time.gmtime(item["date"])) if item.get("date") else None,
                    "round": item.get("round"),
                    "amountUsdM": item.get("amount"),
                    "sector": (item.get("sector") or "")[:160],
                    "leadInvestors": item.get("leadInvestors") or [],
                    "otherInvestors": item.get("otherInvestors") or [],
                }
                for item in raises
                if isinstance(item, dict)
            ],
            "incidents": [
                {
                    "date": time.strftime("%Y-%m-%d", time.gmtime(item["date"])) if item.get("date") else None,
                    "name": item.get("name"),
                    "classification": item.get("classification"),
                    "technique": item.get("technique"),
                    "amountUsd": item.get("amount"),
                    "chains": item.get("chain") or [],
                }
                for item in hacks
                if isinstance(item, dict)
            ],
            "audits": payload.get("audits"),
            "auditLinks": len(payload.get("audit_links") or []) if payload.get("audit_links") else 0,
        }
    except Exception:
        record = {}
    _cache_put(_probe_cache, key, record)
    return record


def llama_arc_chain_metrics(fresh: bool = False) -> dict:
    """Public Arc network metrics from DefiLlama's chain-level endpoints."""
    key = "llama:chain:arc"
    if not fresh:
        cached = _cache_get(_probe_cache, key, GECKO_TTL)
        if cached is not None:
            return cached

    def fetch_json(url: str, limit: int = 16 * 1024 * 1024):
        request = urllib.request.Request(
            url, headers={"user-agent": USER_AGENT, "accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read(limit).decode("utf-8", "replace"))
        except Exception:
            return None

    chains = fetch_json("https://api.llama.fi/v2/chains") or []
    stablecoin_chains = fetch_json("https://stablecoins.llama.fi/stablecoinchains") or []
    dex = fetch_json(
        "https://api.llama.fi/overview/dexs/Arc?excludeTotalDataChart=true&"
        "excludeTotalDataChartBreakdown=true&dataType=dailyVolume") or {}
    fees = fetch_json(
        "https://api.llama.fi/overview/fees/Arc?excludeTotalDataChart=true&"
        "excludeTotalDataChartBreakdown=true&dataType=dailyFees") or {}

    chain = next((row for row in chains if str(row.get("name", "")).lower() == "arc"), {})
    stablecoins = next(
        (row for row in stablecoin_chains if str(row.get("name", "")).lower() == "arc"), {})
    circulating = stablecoins.get("totalCirculatingUSD") or {}
    stablecoin_usd = sum(value for value in circulating.values() if isinstance(value, (int, float)))
    record = {
        "name": "Arc",
        "chainId": chain.get("chainId"),
        "tvlUsd": chain.get("tvl"),
        "stablecoinSupplyUsd": stablecoin_usd or None,
        "dexVolume24hUsd": dex.get("total24h"),
        "dexVolume7dUsd": dex.get("total7d"),
        "dexVolume30dUsd": dex.get("total30d"),
        "fees24hUsd": fees.get("total24h"),
        "fees7dUsd": fees.get("total7d"),
        "fees30dUsd": fees.get("total30d"),
        "sourceUrl": "https://defillama.com/chain/Arc",
    }
    record = {name: value for name, value in record.items() if value is not None}
    _cache_put(_probe_cache, key, record)
    return record


def clean_project_name(raw: str) -> str:
    """'Lido | Liquid Staking for Ethereum' -> 'Lido'.

    Page titles carry taglines; passing one straight to a search API was why
    CoinGecko kept missing and RootData kept being called instead.
    """
    text = (raw or "").strip()
    text = re.split(r"[|\u2013\u2014:\u00b7]| - ", text)[0]
    text = re.sub(r"\s+", " ", text).strip(" -·|")
    return text[:60]


def gecko_lookup(name: str, symbol: str = "") -> dict:
    """CoinGecko free tier: resolve a name to a coin id, then read market fields.

    Tries the project name first, then the ticker. A page title or a tagline is
    never used as the query.
    """
    query = (name or symbol or "").strip()
    if query and " " in query and len(query) > 24 and symbol:
        query = symbol.strip()
    if len(query) < 2:
        return {}
    key = "gecko:" + query.lower()
    cached = _cache_get(_probe_cache, key, GECKO_TTL)
    if cached is not None:
        return cached

    record = {}
    try:
        search = urllib.request.Request(
            "https://api.coingecko.com/api/v3/search?query=" + urllib.parse.quote(query),
            headers={"user-agent": USER_AGENT, "accept": "application/json"})
        with urllib.request.urlopen(search, timeout=25) as response:
            hits = (json.loads(response.read(4 * 1024 * 1024).decode("utf-8", "replace")).get("coins") or [])
        if not hits:
            _cache_put(_probe_cache, key, {})
            return {}
        coin_id = hits[0].get("id")
        detail = urllib.request.Request(
            "https://api.coingecko.com/api/v3/coins/" + urllib.parse.quote(coin_id) +
            "?localization=false&tickers=false&community_data=false&developer_data=true",
            headers={"user-agent": USER_AGENT, "accept": "application/json"})
        with urllib.request.urlopen(detail, timeout=25) as response:
            payload = json.loads(response.read(8 * 1024 * 1024).decode("utf-8", "replace"))
        market = payload.get("market_data") or {}
        developer = payload.get("developer_data") or {}
        record = {
            "id": coin_id,
            "name": payload.get("name"),
            "symbol": payload.get("symbol"),
            "marketCapUsd": (market.get("market_cap") or {}).get("usd"),
            "fdvUsd": (market.get("fully_diluted_valuation") or {}).get("usd"),
            "volume24hUsd": (market.get("total_volume") or {}).get("usd"),
            "priceChange24hPct": market.get("price_change_percentage_24h"),
            "priceChange7dPct": market.get("price_change_percentage_7d"),
            "categories": (payload.get("categories") or [])[:5],
            "homepage": ((payload.get("links") or {}).get("homepage") or [None])[0],
            "twitter": (payload.get("links") or {}).get("twitter_screen_name"),
            "githubCommits4w": developer.get("commit_count_4_weeks"),
            "stars": developer.get("stars"),
            "marketCapRank": payload.get("market_cap_rank"),
        }
    except Exception:
        record = {}
    _cache_put(_probe_cache, key, record)
    return record


# --- RootData -------------------------------------------------------------
# Preferred second, not first: the account runs on a limited free quota, and
# CoinGecko already covers token market data for free. RootData is therefore only
# reached for what CoinGecko cannot answer, and every call is budgeted, cached for
# a day, and counted.
#
# What this tier actually returns (verified against a live key):
#   total_funding, investors[], social_media.website/X, tags, establishment_date,
#   token_symbol, countries, rd_score, rd_hot_index, tvl_score, transparency
# What it does NOT return: team members. The `team` field is absent even with
# include_team=1, and a people search matches on the query string rather than on
# project affiliation, so it cannot be used to name a project's team.

ROOTDATA_BASE = "https://api.rootdata.com/open/"
ROOTDATA_API_KEY = os.environ.get("ROOTDATA_API_KEY", "")
ROOTDATA_LANGUAGE = os.environ.get("ROOTDATA_LANGUAGE", "en")
ROOTDATA_DAILY_CALLS = int(os.environ.get("ROOTDATA_DAILY_CALLS", "30"))
ROOTDATA_TTL = 86400
ROOTDATA_USAGE_FILE = os.path.join(STATIC_DIR, "reports", "rootdata-usage.json")

ROOTDATA_ENGLISH = {
    "基础设施": "Infrastructure",
    "贝莱德": "BlackRock",
}


def _rootdata_english(value):
    if not isinstance(value, str):
        return value
    return ROOTDATA_ENGLISH.get(value.strip(), value.strip())


def rootdata_enabled() -> bool:
    return bool(ROOTDATA_API_KEY)


def _rootdata_usage() -> dict:
    try:
        with open(ROOTDATA_USAGE_FILE, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def _rootdata_charge() -> bool:
    """Count one call against today's budget. Returns False when exhausted."""
    day = time.strftime("%Y-%m-%d", time.gmtime())
    usage = _rootdata_usage()
    used = usage.get(day, 0)
    if used >= ROOTDATA_DAILY_CALLS:
        return False
    usage = {day: used + 1}
    try:
        os.makedirs(os.path.dirname(ROOTDATA_USAGE_FILE), exist_ok=True)
        with open(ROOTDATA_USAGE_FILE, "w", encoding="utf-8") as handle:
            json.dump(usage, handle)
    except OSError:
        pass
    return True


def rootdata_calls_today() -> int:
    return _rootdata_usage().get(time.strftime("%Y-%m-%d", time.gmtime()), 0)


def _rootdata_post(path: str, body: dict) -> dict:
    if not _rootdata_charge():
        return {"error": "daily RootData call budget reached"}
    request = urllib.request.Request(
        ROOTDATA_BASE + path,
        data=json.dumps(body).encode("utf-8"),
        headers={"apikey": ROOTDATA_API_KEY, "language": ROOTDATA_LANGUAGE,
                 "content-type": "application/json", "user-agent": USER_AGENT},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read(8 * 1024 * 1024).decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        return {"error": "HTTP %s" % exc.code}
    except Exception as exc:
        return {"error": exc.__class__.__name__}


def _name_similarity(a: str, b: str) -> float:
    a = re.sub(r"[^a-z0-9]", "", (a or "").lower())
    b = re.sub(r"[^a-z0-9]", "", (b or "").lower())
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.8
    common = len(set(a) & set(b))
    return common / max(len(set(a)), len(set(b)))


def rootdata_lookup(name: str, domain: str = "", handle: str = "") -> dict:
    """Search by name, then accept a candidate only if its own website or X handle
    matches what we already know. A name match alone is a guess, so it is not
    accepted; the mismatch is reported instead."""
    if not rootdata_enabled():
        return {"available": False, "reason": "no RootData key configured"}

    query = (name or "").strip()
    if len(query) < 3:
        return {"available": True, "matched": None, "reason": "project name too short to search reliably"}

    key = "rootdata:%s:%s" % (query.lower(), _norm_host(domain))
    cached = _cache_get(_probe_cache, key, ROOTDATA_TTL)
    if cached is not None:
        return cached

    search = _rootdata_post("ser_inv", {"query": query, "include_tags": 1})
    if search.get("error"):
        return {"available": True, "matched": None, "reason": "RootData search failed: %s" % search["error"]}
    hits = search.get("data") or []
    projects = [item for item in hits if isinstance(item, dict) and item.get("type") == 1]
    if not projects:
        result = {"available": True, "matched": None, "reason": "RootData returned no project for this name"}
        _cache_put(_probe_cache, key, result)
        return result

    projects.sort(key=lambda item: _name_similarity(query, item.get("name")), reverse=True)
    want_host = _norm_host(domain)
    want_handle = _norm_handle(handle)
    rejected = []

    for candidate in projects[:2]:          # at most two detail calls
        detail = _rootdata_post("get_item", {
            "project_id": candidate.get("id"), "include_team": 1, "include_investors": 1})
        data = detail.get("data") or {}
        if not isinstance(data, dict) or not data:
            rejected.append({"name": candidate.get("name"), "reason": detail.get("error") or "no detail returned"})
            continue
        social = data.get("social_media") or {}
        site_host = _norm_host(social.get("website") or "")
        handle_out = _norm_handle(social.get("X") or "")
        if want_host and site_host and (site_host == want_host
                                        or site_host.endswith("." + want_host)
                                        or want_host.endswith("." + site_host)):
            verification = "website domain"
        elif want_handle and handle_out and handle_out == want_handle:
            verification = "X handle"
        else:
            rejected.append({
                "name": data.get("project_name"),
                "reason": "domain %r and handle %r do not match the known %r / %r"
                          % (site_host or None, handle_out or None, want_host or None, want_handle or None),
            })
            continue

        investors = data.get("investors") or []
        raw_team = data.get("team") or []
        if isinstance(raw_team, dict):
            raw_team = raw_team.get("members") or raw_team.get("data") or []
        team = []
        for person in raw_team if isinstance(raw_team, list) else []:
            if not isinstance(person, dict):
                continue
            name = person.get("name") or person.get("person_name") or person.get("member_name")
            if not name:
                continue
            team.append({
                "name": name,
                "role": person.get("position") or person.get("title") or person.get("role"),
                "linkedin": person.get("linkedin") or person.get("linkedin_url"),
            })
        result = {
            "available": True,
            "matched": {
                "verifiedBy": verification,
                "projectId": data.get("project_id"),
                "name": data.get("project_name"),
                "oneLiner": data.get("one_liner"),
                "tags": [_rootdata_english(t.get("name") if isinstance(t, dict) else t)
                         for t in (data.get("tags") or [])][:6],
                "tokenSymbol": data.get("token_symbol"),
                "established": data.get("establishment_date"),
                "countries": data.get("countries"),
                "totalFundingUsd": data.get("total_funding"),
                "investorCount": len(investors),
                "leadInvestors": [_rootdata_english(i.get("name")) for i in investors
                                  if isinstance(i, dict) and str(i.get("type")) == "1"][:6],
                "investors": [_rootdata_english(i.get("name")) for i in investors if isinstance(i, dict)][:12],
                "team": team[:12],
                "website": social.get("website"),
                "x": social.get("X"),
                "github": social.get("github"),
                "heatIndex": data.get("rd_hot_index"),
                "rdScore": data.get("rd_score"),
                "tvlScore": data.get("tvl_score"),
                "transparency": data.get("transparency"),
                "sourceUrl": data.get("rootdataurl"),
            },
            "rejected": rejected,
        }
        _cache_put(_probe_cache, key, result)
        return result

    result = {"available": True, "matched": None, "rejected": rejected,
              "reason": "candidates were found but none could be verified against the known domain or handle"}
    _cache_put(_probe_cache, key, result)
    return result


# Product-type templates: what to surface once the category is known. DefiLlama's
# own category field is the primary signal, since it is curated rather than guessed.
PRODUCT_TEMPLATES = {
    "Launchpad": {"headline": "tokens launched", "watch": ["tvl", "volume24hUsd", "funding"],
                  "ask": "How many launches, and how much has been raised through it?"},
    "Dexs": {"headline": "trading volume", "watch": ["tvl", "volume24hUsd"], "ask": "Volume against TVL, and depth."},
    "DEX Aggregator": {"headline": "routed volume", "watch": ["volume24hUsd"], "ask": "Routed volume and fee take."},
    "Lending": {"headline": "deposits", "watch": ["tvl"], "ask": "Utilisation and bad-debt history."},
    "Derivatives": {"headline": "open interest", "watch": ["tvl", "volume24hUsd"], "ask": "Open interest and liquidation risk."},
    "Liquid Staking": {"headline": "staked value", "watch": ["tvl"], "ask": "Validator set and slashing history."},
    "Bridge": {"headline": "bridged value", "watch": ["tvl"], "ask": "Bridge design and incident history."},
    "RWA": {"headline": "tokenised assets", "watch": ["tvl"], "ask": "Custody and redemption terms."},
    "Prediction Market": {"headline": "open interest", "watch": ["tvl", "volume24hUsd"], "ask": "Liquidity per market."},
    "Yield": {"headline": "deposits", "watch": ["tvl"], "ask": "Yield source and sustainability."},
    "Farm": {"headline": "deposits", "watch": ["tvl"], "ask": "Emissions schedule."},
}


def product_template(category: str) -> dict:
    if not category:
        return {}
    if category in PRODUCT_TEMPLATES:
        return dict(PRODUCT_TEMPLATES[category], category=category)
    return {"category": category, "headline": "total value locked", "watch": ["tvl"],
            "ask": "What does this category's core metric look like over time?"}


# Numbers a project publishes about itself. Self-reported, never scored, and
# deliberately conservative: a loose regex reported "32.7B users" on a real site,
# and a claim that absurd would discredit every other number on the page.
SELF_REPORTED_PATTERNS = [
    ("users", re.compile(r"\b([0-9][0-9.,]*\s*(?:million|billion|thousand|[mkb])?)\+?\s+(?:active\s+)?(?:users|accounts|wallets|holders|addresses)\b", re.I)),
    ("TVL", re.compile(r"\$\s*([0-9][0-9.,]*\s*(?:million|billion|trillion|[mkbt])?)\+?\s+(?:in\s+)?(?:tvl|total\s+value\s+locked)\b", re.I)),
    ("TVL", re.compile(r"\b(?:tvl|total\s+value\s+locked)\D{0,12}\$?\s*([0-9][0-9.,]*\s*(?:million|billion|trillion|[mkbt])?)\b", re.I)),
    ("volume", re.compile(r"\$\s*([0-9][0-9.,]*\s*(?:million|billion|trillion|[mkbt])?)\+?\s+(?:in\s+)?(?:trading\s+|total\s+)?volume\b", re.I)),
    ("launches", re.compile(r"\b([0-9][0-9.,]*\s*(?:million|billion|thousand|[mkb])?)\+?\s+(?:tokens?|coins?|projects?|assets?|memes?)\s+(?:launched|listed|created|deployed|graduated)\b", re.I)),
    ("transactions", re.compile(r"\b([0-9][0-9.,]*\s*(?:million|billion|thousand|[mkb])?)\+?\s+(?:transactions|swaps|trades)\b", re.I)),
    ("downloads", re.compile(r"\b([0-9][0-9.,]*\s*(?:million|billion|thousand|[mkb])?)\+?\s+(?:downloads|installs)\b", re.I)),
]

# Plausibility bounds per kind. Outside these, the number is almost certainly a
# different metric that happened to sit next to the keyword.
SELF_REPORTED_BOUNDS = {
    "users": (1_000, 1_000_000_000),
    "TVL": (100_000, 5e12),
    "volume": (10_000, 5e13),
    "launches": (50, 5_000_000),
    "transactions": (10_000, 1e13),
    "downloads": (1_000, 1e9),
}
_WORD_SCALE = {"thousand": 1e3, "k": 1e3, "million": 1e6, "m": 1e6, "billion": 1e9, "b": 1e9,
               "trillion": 1e12, "t": 1e12}


def parse_reported_number(raw: str):
    """'32.7B' -> 3.27e10, '24,689,839,532' -> 2.4689839532e10, else None."""
    if not raw:
        return None
    text = raw.strip().lower().replace(",", "")
    scale = 1.0
    match = re.search(r"(thousand|million|billion|trillion|[kmbt])$", text)
    if match:
        scale = _WORD_SCALE.get(match.group(1), 1.0)
        text = text[:match.start()].strip()
    try:
        return float(text) * scale
    except ValueError:
        return None


def extract_self_reported(text: str) -> list:
    """Pull the numbers a page publishes about itself, with the sentence they came from.

    Kept deliberately strict: the number must sit directly before its keyword and
    fall inside a plausible range for that kind of metric. Everything found is a
    claim, shown as a claim, and never scored.
    """
    if not text:
        return []
    plain = re.sub(r"\s+", " ", _TAG_RE.sub(" ", text))
    found, seen = [], set()
    for kind, pattern in SELF_REPORTED_PATTERNS:
        low, high = SELF_REPORTED_BOUNDS[kind]
        for match in pattern.finditer(plain):
            magnitude = parse_reported_number(match.group(1))
            if magnitude is None or not (low <= magnitude <= high):
                continue
            key = (kind, round(magnitude))
            if key in seen:
                continue
            seen.add(key)
            start = max(0, match.start() - 80)
            found.append({
                "kind": kind,
                "value": match.group(1).strip(),
                "quote": plain[start:match.end() + 40].strip()[:200],
            })
            if len(found) >= 6:
                return found
    return found


# --------------------------------------------------------------------------
# Deep report: the seven-module grading frame
# --------------------------------------------------------------------------
# The frame follows the requested V2.0 template. One rule shapes the whole
# implementation: a module is only scored when something was actually measured.
# Modules with no evidence are marked unscored and dropped from the denominator,
# which is the template's own rule for projects that have not launched a token or
# raised money. Nothing here is filled in from a model's impression.

REPORT_DEADLINE_SECONDS = int(os.environ.get("ARC_AI_REPORT_DEADLINE", "285"))
REPORT_MODEL_TIMEOUT = int(os.environ.get("ARC_AI_REPORT_TIMEOUT", "210"))
REPORT_MAX_OUTPUT_TOKENS = int(os.environ.get("ARC_AI_REPORT_TOKENS", "12000"))

GRADE_BANDS = [(70, "S"), (60, "A"), (45, "B"), (30, "C"), (0, "D")]

REPORT_MODULES = [
    {"id": "product", "name": "Product and innovation", "weight": 20},
    {"id": "data", "name": "Data and growth", "weight": 15},
    {"id": "team", "name": "Team", "weight": 15},
    {"id": "funding", "name": "Funding and backers", "weight": 10},
    {"id": "token", "name": "Token economics and valuation", "weight": 15},
    {"id": "position", "name": "Ecosystem position and narrative", "weight": 15},
    {"id": "heat", "name": "Attention and catalysts", "weight": 10},
]

REPORT_GROUPS = [
    {"id": "quality", "name": "Project quality", "modules": ["product", "data", "team", "funding"]},
    {"id": "token", "name": "Token opportunity", "modules": ["token"]},
    {"id": "timing", "name": "Timing and catalysts", "modules": ["position", "heat"]},
]

# Which measurements matter, per product type. Mirrors the template's table.
TYPE_METRICS = {
    "Dexs": ["tvl", "volume", "fees", "activity"],
    "DEX Aggregator": ["volume", "fees"],
    "Derivatives": ["volume", "tvl", "openInterest"],
    "Lending": ["tvl", "borrows", "utilisation"],
    "Launchpad": ["raiseVolume", "launches", "volume", "fees"],
    "Liquid Staking": ["tvl", "validators"],
    "Bridge": ["tvl", "incidents"],
    "RWA": ["tvl"],
    "Prediction Market": ["volume", "openInterest"],
    "AI / Infra": ["usage", "developers", "integrations"],
    "GameFi / Social": ["dau", "mau", "revenue"],
    "Meme": ["attention", "holders", "liquidity", "concentration"],
}


def grade_for(total):
    for threshold, letter in GRADE_BANDS:
        if total >= threshold:
            return letter
    return "D"


def research_level(total):
    if total is None:
        return None
    if total >= 75:
        return "Priority research"
    if total >= 60:
        return "Watch closely"
    if total >= 45:
        return "Early evidence"
    return "Limited evidence"


def _fmt_usd(value):
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    for scale, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= scale:
            return "$%.2f%s" % (value / scale, suffix)
    return "$%.0f" % value


def build_grading_frame(dossier: dict) -> dict:
    """Score each module from measurements, or mark it unscored."""
    prov = dossier.get("_providers") or {}
    llama = prov.get("defillama") or {}
    gecko = prov.get("coingecko") or {}
    arc_chain = prov.get("arcChain") or {}
    rootdata = (prov.get("rootdata") or {}).get("matched") or {}
    metrics = (dossier.get("_metrics") or {}).get("networks") or {}
    explorer = (dossier.get("_explorer") or {}).get("networks") or {}
    probes = dossier.get("_probes") or {}
    claims = dossier.get("_selfReported") or []
    contract = dossier.get("_contract") or {}

    main_explorer = explorer.get("mainnet") or {}
    best_explorer = main_explorer if main_explorer.get("ok") else (explorer.get("testnet") or {})
    deployed_on = contract.get("deployedOn") or []
    best_metrics = None
    for key in ("mainnet", "testnet"):
        entry = metrics.get(key) or {}
        if entry.get("deployed"):
            best_metrics = entry
            break

    category = llama.get("category") or ""
    type_key = category if category in TYPE_METRICS else None
    if not type_key:
        for candidate, keys in TYPE_METRICS.items():
            if candidate.lower() in category.lower() and candidate != category:
                type_key = candidate
                break

    modules, risk_flags = [], []

    def module(mid, score, maximum, evidence, basis="measured", note=""):
        definition = next(item for item in REPORT_MODULES if item["id"] == mid)
        modules.append({
            "id": mid,
            "name": definition["name"],
            "weight": definition["weight"],
            "basis": basis,
            "score": score,               # 0-5, or None when unscored
            "maxScore": maximum,
            "evidence": evidence,
            "note": note,
        })

    # 1. Product and innovation ------------------------------------------
    evidence, points = [], 0.0
    site = probes.get("website") or {}
    docs = probes.get("docs") or {}
    repo = probes.get("github") or {}
    if site.get("ok"):
        points += 1.0; evidence.append("Official website is reachable")
    if docs.get("ok"):
        points += 1.0; evidence.append("Documentation is reachable")
    if site.get("description") or dossier.get("description"):
        points += 1.0; evidence.append("The project publishes its own description")
    if repo.get("ok"):
        points += 0.5; evidence.append("Public repository linked from the site")
    if category:
        points += 1.0; evidence.append("Classified as %s by DefiLlama" % category)
    if evidence:
        module("product", round(min(points, 5.0), 1), 5, evidence,
               note="Scored from what exists and is reachable. Innovation and competitive position "
                    "are described in the narrative, not scored, because no measurement supports a number.")
    else:
        module("product", None, 5, [], basis="unscored",
               note="No product surface could be read.")

    # 2. Data and growth --------------------------------------------------
    evidence, points = [], 0.0
    wanted = TYPE_METRICS.get(type_key) or ["tvl", "volume", "activity"]
    if llama.get("tvlUsd") is not None:
        points += 1.5
        change = llama.get("change7dPct")
        evidence.append("TVL %s%s" % (_fmt_usd(llama["tvlUsd"]),
                                      "" if change is None else " (%+.1f%% over 7 days)" % change))
        if change is not None:
            points += 1.0 if change > 0 else 0.0
            evidence.append("7-day TVL trend is %s" % ("positive" if change > 0 else "negative"))
    if gecko.get("volume24hUsd") is not None:
        points += 1.0
        evidence.append("24h traded volume %s" % _fmt_usd(gecko["volume24hUsd"]))
    fees = llama.get("fees") or {}
    if fees.get("fees24h") is not None:
        points += 0.5
        line = "24h fees %s" % _fmt_usd(fees["fees24h"])
        if fees.get("fees7d") is not None:
            line += ", 7-day %s" % _fmt_usd(fees["fees7d"])
        if fees.get("fees30d") is not None:
            line += ", 30-day %s" % _fmt_usd(fees["fees30d"])
        evidence.append(line)
    if arc_chain.get("tvlUsd") is not None:
        points += 1.5
        evidence.append("Network TVL %s" % _fmt_usd(arc_chain["tvlUsd"]))
    if arc_chain.get("stablecoinSupplyUsd") is not None:
        points += 1.0
        evidence.append("Stablecoin supply %s" % _fmt_usd(arc_chain["stablecoinSupplyUsd"]))
    if arc_chain.get("dexVolume24hUsd") is not None:
        points += 1.0
        evidence.append("24h DEX volume %s" % _fmt_usd(arc_chain["dexVolume24hUsd"]))
    if arc_chain.get("fees24hUsd") is not None:
        points += 0.5
        evidence.append("24h protocol fees %s" % _fmt_usd(arc_chain["fees24hUsd"]))
    activity = (best_metrics or {}).get("activity") or {}
    if activity.get("transfers"):
        points += 1.0
        evidence.append("%s transfers across %s addresses in the scanned window"
                        % (activity.get("transfers"), activity.get("uniqueAddresses")))
    if claims:
        evidence.append("%d self-reported figures are excluded from scoring" % len(claims))
    if evidence and (llama.get("tvlUsd") is not None or gecko.get("volume24hUsd") is not None
                     or arc_chain.get("tvlUsd") is not None
                     or activity.get("transfers")):
        module("data", round(min(points, 5.0), 1), 5, evidence,
               note="Metrics chosen for the %s profile: %s." % (type_key or "unclassified", ", ".join(wanted)))
    else:
        module("data", None, 5, evidence, basis="unscored",
               note="No third-party or on-chain activity figure was available.")

    # 3. Team -------------------------------------------------------------
    team = rootdata.get("team") or []
    if team:
        module("team", min(5.0, 2.0 + len(team) * 0.75), 5,
               ["%s%s" % (person.get("name"), " — " + person.get("role") if person.get("role") else "")
                for person in team[:6]],
               note="Named team members returned by RootData after the entry was verified by domain or X handle.")
    else:
        module("team", None, 5, [], basis="unscored", note="No verified team record was returned.")

    # 4. Funding and backers ---------------------------------------------
    evidence, points = [], 0.0
    total_funding = rootdata.get("totalFundingUsd")
    rounds = llama.get("funding") or []
    if total_funding:
        points += 2.0; evidence.append("Total funding %s" % _fmt_usd(total_funding))
        if rootdata.get("investorCount"):
            points += 1.0; evidence.append("%s investors on record" % rootdata["investorCount"])
        if rootdata.get("leadInvestors"):
            points += 1.0; evidence.append("Lead investors: %s" % ", ".join(rootdata["leadInvestors"][:4]))
        if len(rounds) > 1:
            points += 0.5; evidence.append("%d rounds recorded by DefiLlama" % len(rounds))
        module("funding", round(min(points, 5.0), 1), 5, evidence)
    elif rounds:
        points = 2.0 + (0.5 if len(rounds) > 1 else 0)
        evidence.append("%d funding round(s) recorded by DefiLlama" % len(rounds))
        module("funding", round(min(points, 5.0), 1), 5, evidence)
    else:
        module("funding", None, 5, [], basis="unscored",
               note="No funding round is on record in the free sources. Per the framework, absent funding is "
                    "not scored as a weakness.")

    # 5. Token economics and valuation -----------------------------------
    evidence, points = [], 0.0
    if gecko:
        mcap, fdv = gecko.get("marketCapUsd"), gecko.get("fdvUsd")
        volume = gecko.get("volume24hUsd")
        points += 1.5
        evidence.append("Token %s with market cap %s" % (
            (gecko.get("symbol") or "").upper() or "listed", _fmt_usd(mcap)))
        if mcap and fdv and fdv > 0:
            circulating = 100.0 * mcap / fdv
            evidence.append("Circulating ratio %.1f%% of FDV (%s)" % (circulating, _fmt_usd(fdv)))
            points += 2.0 if circulating >= 60 else 1.0 if circulating >= 30 else 0.0
        if mcap and volume is not None:
            turnover = (volume / mcap) if mcap else 0
            evidence.append("24h turnover %.2f%% of market cap" % (turnover * 100))
            points += 1.0 if turnover >= 0.02 else 0.0
        module("token", round(min(points, 5.0), 1), 5, evidence,
               note="No unlock schedule or vesting source is connected, so that part of the module is not scored.")
    else:
        module("token", None, 5, [], basis="unscored",
               note="No token is listed on CoinGecko, so per the framework this module is dropped and the "
                    "remaining weights are renormalised. Coverage is reported below.")

    # 6. Ecosystem position and narrative --------------------------------
    evidence, points = [], 0.0
    if "mainnet" in deployed_on:
        points += 2.0; evidence.append("Contract proven on Arc mainnet")
    elif "testnet" in deployed_on:
        points += 1.0; evidence.append("Contract proven on Arc testnet only")
    elif dossier.get("curatedAs"):
        points += 2.0; evidence.append("Official Arc surface in the curated catalog")
    if category:
        points += 0.5; evidence.append("Operating in the %s category" % category)
    if llama.get("name"):
        points += 0.5; evidence.append("Listed as %s on DefiLlama" % llama["name"])
    if rootdata.get("tags"):
        points += 0.5; evidence.append("Ecosystem tags: %s" % ", ".join(rootdata["tags"][:4]))
    if not deployed_on and not dossier.get("curatedAs"):
        risk_flags.append({"id": "not-on-arc", "severity": "info",
                           "label": "No Arc deployment proven",
                           "detail": "Nothing in this dossier proves the project is deployed on Arc, so its "
                                     "ecosystem position here cannot be established."})
    if evidence:
        module("position", round(min(points, 5.0), 1), 5, evidence,
               note="Leader-versus-challenger status within the category is not measured; only membership "
                    "and classification are.")
    else:
        module("position", None, 5, [], basis="unscored", note="No ecosystem signal was available.")

    # 7. Attention and catalysts -----------------------------------------
    evidence, points = [], 0.0
    if (best_metrics or {}).get("activity", {}).get("transfers"):
        points += 2.0; evidence.append("On-chain activity observed in the scanned window")
    if evidence:
        module("heat", round(min(points, 5.0), 1), 5, evidence,
               note="Catalyst events (listings, launches, upgrades) are not tracked by any connected source "
                    "and are left to the narrative.")
    else:
        module("heat", None, 5, [], basis="unscored", note="No attention signal was available.")

    # --- risk flags, deliberately outside the total ----------------------
    verification = (best_explorer.get("verification") or {})
    if verification and not verification.get("verified"):
        risk_flags.append({"id": "unverified-source", "severity": "watch",
                           "label": "Source not published to the explorer",
                           "detail": "The explorer holds no verified source for this address."})
    incidents = llama.get("incidents") or []
    for incident in incidents[-2:]:
        risk_flags.append({"id": "exploit", "severity": "risk",
                           "label": "Recorded security incident: %s" % (incident.get("classification") or "unclassified"),
                           "detail": "%s%s" % (incident.get("date") or "",
                                               ", about %s lost" % _fmt_usd(incident.get("amountUsd")) if incident.get("amountUsd") else "")})
    structure = {probe.get("name"): probe for probe in (best_metrics or {}).get("structure") or []}
    if (structure.get("implementation") or {}).get("value"):
        risk_flags.append({"id": "proxy", "severity": "watch", "label": "Upgradeable proxy",
                           "detail": "implementation() returns %s, so logic can be replaced."
                                     % structure["implementation"]["value"]})
    migration = (structure.get("owner") or {}).get("value")
    if migration:
        risk_flags.append({"id": "owner", "severity": "watch", "label": "Owner role present",
                           "detail": "owner() returns %s." % migration})
    if (best_metrics or {}).get("activity", {}).get("mints"):
        risk_flags.append({"id": "mint", "severity": "risk", "label": "Minting observed in window",
                           "detail": "%s transfers came from the zero address."
                                     % (best_metrics or {}).get("activity", {}).get("mints")})
    distribution = best_explorer.get("distribution") or {}
    if distribution.get("top10Pct") is not None and distribution["top10Pct"] >= 70:
        risk_flags.append({"id": "concentration", "severity": "risk", "label": "Concentrated supply",
                           "detail": "Top 10 holders control %.2f%% of supply." % distribution["top10Pct"]})
    if gecko.get("marketCapUsd") and (gecko.get("volume24hUsd") or 0) >= 0:
        turnover = (gecko.get("volume24hUsd") or 0) / gecko["marketCapUsd"]
        if gecko["marketCapUsd"] > 1_000_000 and turnover < 0.001:
            risk_flags.append({"id": "illiquid", "severity": "risk", "label": "Market cap without turnover",
                               "detail": "24h volume is %.4f%% of market cap (%s against %s)."
                                         % (turnover * 100, _fmt_usd(gecko.get("volume24hUsd")),
                                            _fmt_usd(gecko["marketCapUsd"]))})

    # --- weighted total over scored modules only -------------------------
    scored = [item for item in modules if item["score"] is not None]
    weight_total = sum(item["weight"] for item in scored)
    weighted = sum(item["score"] / item["maxScore"] * item["weight"] for item in scored)
    total = round(100.0 * weighted / weight_total, 1) if weight_total else None
    groups = []
    for definition in REPORT_GROUPS:
        members = [item for item in scored if item["id"] in definition["modules"]]
        measured_weight = sum(item["weight"] for item in members)
        possible_weight = sum(item["weight"] for item in REPORT_MODULES
                              if item["id"] in definition["modules"])
        earned_weight = sum(item["score"] / item["maxScore"] * item["weight"] for item in members)
        highlights = []
        for item in members:
            highlights.extend(item.get("evidence") or [])
        groups.append({
            "id": definition["id"],
            "name": definition["name"],
            "score": round(100.0 * earned_weight / measured_weight, 1) if measured_weight else None,
            "measuredWeight": measured_weight,
            "possibleWeight": possible_weight,
            "summary": ". ".join(highlights[:5]) + ("." if highlights else ""),
        })

    rootdata_tags = rootdata.get("tags") or []
    rootdata_type = next((tag for tag in rootdata_tags if "layer" in str(tag).lower()),
                         rootdata_tags[0] if rootdata_tags else None)
    return {
        "framework": "New-chain ecosystem research and scoring framework v2.0",
        "productType": type_key or category or rootdata_type or "unclassified",
        "metricsForType": TYPE_METRICS.get(type_key or "", []),
        "modules": modules,
        "riskFlags": risk_flags,
        "scoredWeight": weight_total,
        "totalWeight": sum(item["weight"] for item in REPORT_MODULES),
        "coveragePct": round(100.0 * weight_total / sum(item["weight"] for item in REPORT_MODULES), 1),
        "total": total,
        "grade": grade_for(total) if total is not None else None,
        "researchLevel": research_level(total),
        "groups": groups,
        "basisNote": "The total covers only the %d%% of weight that could be measured. Modules without "
                     "evidence are excluded rather than scored zero. It is a research-priority score, not "
                     "a buy signal." % round(100.0 * weight_total
                     / sum(item["weight"] for item in REPORT_MODULES), 1),
    }


# --------------------------------------------------------------------------
# Multi-dimensional scorecard
# --------------------------------------------------------------------------
# Deliberately not one blended number. Each dimension reports whether it was
# actually measured: a dimension with no data source is marked unmeasured and
# excluded from the total, because scoring "no data" as zero would punish a
# project for our blind spots.

def build_scorecard(dossier: dict) -> dict:
    target = dossier.get("target") or {}
    contract = dossier.get("_contract") or {}
    metrics = (dossier.get("_metrics") or {}).get("networks") or {}
    explorer = (dossier.get("_explorer") or {}).get("networks") or {}
    probes = dossier.get("_probes") or {}
    discovery = dossier.get("_discovery") or {}

    def network_metrics(key):
        entry = metrics.get(key) or {}
        return entry if entry.get("deployed") else None

    mainnet = network_metrics("mainnet")
    testnet = network_metrics("testnet")
    main_explorer = explorer.get("mainnet") or {}
    test_explorer = explorer.get("testnet") or {}
    best_metrics = mainnet or testnet
    best_explorer = main_explorer if main_explorer.get("ok") else test_explorer
    # Read every provider result once, before any dimension needs them. Adding a
    # provider later and reading it mid-function caused two crashes already.
    _prov = dossier.get("_providers") or {}
    llama = _prov.get("defillama") or {}
    gecko = _prov.get("coingecko") or {}
    arc_chain = _prov.get("arcChain") or {}
    rd = (_prov.get("rootdata") or {}).get("matched") or {}

    dimensions = []

    def dimension(key, label, maximum, state, items, note=""):
        measured = [item for item in items]
        earned = sum(item["earned"] for item in measured) if state == "measured" else None
        dimensions.append({
            "key": key,
            "label": label,
            "state": state,
            "max": maximum,
            "earned": earned,
            "items": measured,
            "note": note,
        })

    # 1. Arc membership ----------------------------------------------------
    deployed_on = contract.get("deployedOn") or []
    items = []
    if "mainnet" in deployed_on:
        items.append({"label": "Contract found on Arc mainnet", "earned": 20, "max": 20,
                      "reason": "%s bytes of bytecode at block %s" % (
                          (contract.get("networks", {}).get("mainnet") or {}).get("bytecodeBytes"),
                          (contract.get("networks", {}).get("mainnet") or {}).get("checkedAtBlock"))})
    elif "testnet" in deployed_on:
        items.append({"label": "Testnet deployment only", "earned": 12, "max": 20,
                      "reason": "Nothing at this address on Arc mainnet"})
    elif dossier.get("curatedAs"):
        items.append({"label": "Curated official Arc surface", "earned": 16, "max": 20,
                      "reason": "Matched the curated catalog and resolved live"})
    if items:
        dimension("arc_membership", "Arc membership", 20, "measured", items)
    else:
        dimension("arc_membership", "Arc membership", 20, "unmeasured", [],
                  "No contract address was supplied, so nothing could be read from the chain.")

    # 2. Contract safety ---------------------------------------------------
    safety_items = []
    verification = (main_explorer.get("verification") or test_explorer.get("verification") or {})
    if verification:
        if verification.get("verified"):
            safety_items.append({"label": "Source published to the explorer", "earned": 6, "max": 6,
                                 "reason": "Verified as %s, compiled with %s" % (
                                     verification.get("contractName"), verification.get("compiler"))})
        else:
            safety_items.append({"label": "Source not published", "earned": 0, "max": 6,
                                 "reason": "The explorer holds no verified source for this address"})
    if best_metrics:
        structure = {probe.get("name"): probe for probe in best_metrics.get("structure") or []}
        activity = best_metrics.get("activity") or {}
        safety_items.append({"label": "No upgradeable proxy detected", "earned": 0 if (structure.get("implementation") or {}).get("value") else 4, "max": 4,
                             "reason": "implementation() returns %s" % ((structure.get("implementation") or {}).get("value") or "nothing")})
        safety_items.append({"label": "No owner role detected", "earned": 0 if (structure.get("owner") or {}).get("value") else 3, "max": 3,
                             "reason": "owner() returns %s" % ((structure.get("owner") or {}).get("value") or "nothing")})
        safety_items.append({"label": "No separate admin detected", "earned": 0 if (structure.get("admin") or {}).get("value") else 2, "max": 2,
                             "reason": "admin() returns %s" % ((structure.get("admin") or {}).get("value") or "nothing")})
        safety_items.append({"label": "Transfers not pausable", "earned": 0 if (structure.get("paused") or {}).get("callable") else 2, "max": 2,
                             "reason": "paused() is %s" % ("callable" if (structure.get("paused") or {}).get("callable") else "not callable")})
        safety_items.append({"label": "No minting observed in the window", "earned": 0 if activity.get("mints") else 3, "max": 3,
                             "reason": "%s transfers came from the zero address" % activity.get("mints")})
    incidents = ((dossier.get("_providers") or {}).get("defillama") or {}).get("incidents") or []
    if incidents:
        loss = sum(item.get("amountUsd") or 0 for item in incidents)
        safety_items.append({
            "label": "No recorded security incidents", "earned": 0, "max": 4,
            "reason": "%d incident(s) on record%s, most recent %s (%s)" % (
                len(incidents),
                ", about $%s lost in total" % "{:,.0f}".format(loss) if loss else "",
                incidents[-1].get("date") or "date unknown",
                incidents[-1].get("classification") or "unclassified"),
        })
    elif llama:
        safety_items.append({"label": "No recorded security incidents", "earned": 4, "max": 4,
                             "reason": "DefiLlama records no exploit against this protocol"})
    # The dimension only counts as measured when a contract was actually inspected.
    # A third-party incident record alone cannot stand in for that.
    inspected = bool(best_metrics) or bool(verification)
    if safety_items and inspected:
        dimension("contract_safety", "Contract safety", 20, "measured", safety_items)
    else:
        dimension("contract_safety", "Contract safety", 20, "unmeasured", [],
                  "No contract address was supplied, so no contract could be inspected."
                  + (" A third-party incident record exists but cannot substitute for reading the contract."
                     if safety_items else ""))

    # 3. Distribution ------------------------------------------------------
    distribution = best_explorer.get("distribution") or {}
    holders_count = best_explorer.get("holdersCount")
    if distribution.get("top10Pct") is not None:
        top10 = distribution["top10Pct"]
        top1 = distribution.get("top1Pct")
        if top10 < 30:
            earned, reason = 15, "Top 10 holders control %.2f%% of supply" % top10
        elif top10 < 50:
            earned, reason = 11, "Top 10 holders control %.2f%% of supply" % top10
        elif top10 < 70:
            earned, reason = 7, "Top 10 holders control %.2f%% of supply" % top10
        else:
            earned, reason = 3, "Top 10 holders control %.2f%% of supply" % top10
        items = [{"label": "Supply concentration", "earned": earned, "max": 15, "reason": reason}]
        if holders_count:
            items.append({"label": "Holder base", "earned": 0, "max": 0,
                          "reason": "%s holders reported by the explorer" % "{:,}".format(holders_count)})
        if top1 is not None:
            items.append({"label": "Largest single holder", "earned": 0, "max": 0,
                          "reason": "%.2f%% of supply" % top1})
        source_label = best_explorer.get("label") or "an Arc network"
        caveat = distribution.get("caveat", "")
        if not main_explorer.get("ok") and test_explorer.get("ok"):
            caveat += (" Holder data came from the %s explorer because the mainnet explorer did not answer; "
                       "the same token address was used on both." % source_label)
        dimension("distribution", "Distribution", 15, "measured", items, caveat)
    else:
        dimension("distribution", "Distribution", 15, "unmeasured", [],
                  "The explorer returned no holder data for this address, so concentration could not be computed.")

    # 4. Market activity ---------------------------------------------------
    if best_metrics:
        activity = best_metrics.get("activity") or {}
        window = activity.get("window") or {}
        transfers = activity.get("transfers") or 0
        unique = activity.get("uniqueAddresses") or 0
        per_minute = activity.get("transfersPerMinute") or 0
        breadth = (transfers / unique) if unique else None
        if transfers == 0:
            earned, reason = 0, "No transfers in the scanned window of %s blocks" % window.get("blocksCovered")
        elif per_minute >= 20:
            earned, reason = 15, "%.1f transfers per minute across %s addresses" % (per_minute, "{:,}".format(unique))
        elif per_minute >= 5:
            earned, reason = 11, "%.1f transfers per minute across %s addresses" % (per_minute, "{:,}".format(unique))
        elif per_minute >= 1:
            earned, reason = 7, "%.1f transfers per minute across %s addresses" % (per_minute, "{:,}".format(unique))
        else:
            earned, reason = 3, "%.2f transfers per minute across %s addresses" % (per_minute, "{:,}".format(unique))
        items = [{"label": "Transfer activity", "earned": earned, "max": 15, "reason": reason}]
        if breadth is not None:
            items.append({"label": "Activity breadth", "earned": 0, "max": 0,
                          "reason": "%.1f transfers per distinct address%s" % (
                              breadth, " — concentrated, consistent with bots" if breadth >= 20 else "")})
        dimension("market_activity", "Market activity", 15, "measured", items,
                  "Measured over blocks %s-%s only (~%s minutes). This is a window, not a full history." % (
                      window.get("fromBlock"), window.get("toBlock"), window.get("estimatedMinutes")))
    else:
        dimension("market_activity", "Market activity", 15, "unmeasured", [],
                  "Activity is read from transfer logs, which requires a contract address.")

    # 5. Source verifiability ---------------------------------------------
    site = probes.get("website") or {}
    docs = probes.get("docs") or {}
    repo = probes.get("github") or {}
    social = probes.get("social") or {}
    source_items = []
    for key, label, probe, weight in (
        ("website", "Official website resolves", site, 5),
        ("docs", "Documentation resolves", docs, 5),
        ("github", "Source repository resolves", repo, 3),
        ("social", "Social profile resolves", social, 2),
    ):
        if probe:
            ok = bool(probe.get("ok"))
            source_items.append({"label": label, "earned": weight if ok else 0, "max": weight,
                                 "reason": "HTTP %s" % probe.get("httpStatus") if ok else probe.get("error", "not reachable")})
    if discovery.get("crossLinked"):
        source_items.append({"label": "Discovered surfaces agree on one domain", "earned": 3, "max": 3,
                             "reason": "The X profile links to %s" % discovery.get("linkedDomain")})
    elif discovery.get("note"):
        # This is a limitation of the query shape, not a finding about the project.
        source_items.append({"label": "Cross-source agreement", "earned": 0, "max": 0, "reason": discovery["note"]})
    scored_sources = [item for item in source_items if item["max"] > 0]
    if scored_sources:
        dimension("source_verifiability", "Source verifiability", 18, "measured", source_items)
    else:
        # A contract-only screen has no web surface to verify. Counting that as 0/18
        # would penalise the project for the shape of the query.
        dimension("source_verifiability", "Source verifiability", 18, "unmeasured", [],
                  "No website, documentation or social surface was supplied or discovered, so there was "
                  "nothing to verify. Screen the project's website or X profile to measure this dimension.")

    # 6. Narrative and documentation --------------------------------------
    described = bool(site.get("description")) or bool(dossier.get("description"))
    has_docs = bool(docs.get("ok"))
    if site or docs:
        items = [
            {"label": "Project describes itself", "earned": 6 if described else 0, "max": 6,
             "reason": (site.get("description") or dossier.get("description") or "No description published")[:200]},
            {"label": "Long-form documentation exists", "earned": 4 if has_docs else 0, "max": 4,
             "reason": "Documentation surface resolved" if has_docs else "No documentation surface resolved"},
        ]
        dimension("narrative", "Narrative and documentation", 10, "measured", items,
                  "This scores whether a project documents itself, not whether the story is convincing.")
    else:
        dimension("narrative", "Narrative and documentation", 10, "unmeasured", [],
                  "No website or documentation surface was available to read.")

    # 7. Protocol metrics (DefiLlama / CoinGecko) -------------------------
    metric_items = []
    if arc_chain:
        if arc_chain.get("tvlUsd") is not None:
            metric_items.append({"label": "Network TVL", "earned": 5, "max": 5,
                                 "reason": "$%s" % "{:,.0f}".format(arc_chain["tvlUsd"])})
        if arc_chain.get("stablecoinSupplyUsd") is not None:
            metric_items.append({"label": "Stablecoin supply", "earned": 4, "max": 4,
                                 "reason": "$%s circulating on Arc" % "{:,.0f}".format(arc_chain["stablecoinSupplyUsd"])})
        if arc_chain.get("dexVolume24hUsd") is not None:
            metric_items.append({"label": "DEX volume", "earned": 3, "max": 3,
                                 "reason": "$%s over 24h" % "{:,.0f}".format(arc_chain["dexVolume24hUsd"])})
        if arc_chain.get("fees24hUsd") is not None:
            metric_items.append({"label": "Protocol fees", "earned": 3, "max": 3,
                                 "reason": "$%s over 24h" % "{:,.0f}".format(arc_chain["fees24hUsd"])})
    elif llama.get("tvlUsd") is not None:
        change = llama.get("change7dPct")
        metric_items.append({
            "label": "Total value locked", "earned": 8, "max": 8,
            "reason": "$%s%s (%s), matched by %s" % (
                "{:,.0f}".format(llama["tvlUsd"]),
                "" if change is None else ", %+.1f%% over 7 days" % change,
                llama.get("category") or "uncategorised", llama.get("matchedBy")),
        })
    if not arc_chain and gecko.get("marketCapUsd") is not None:
        metric_items.append({
            "label": "Token market data", "earned": 4, "max": 4,
            "reason": "market cap $%s, 24h volume $%s" % (
                "{:,.0f}".format(gecko["marketCapUsd"]),
                "{:,.0f}".format(gecko.get("volume24hUsd") or 0)),
        })
    if not arc_chain and llama.get("category"):
        metric_items.append({
            "label": "Product category identified", "earned": 3, "max": 3,
            "reason": "Classified as %s by DefiLlama, which selects what this dossier highlights" % llama["category"],
        })
    commits = None if arc_chain else gecko.get("githubCommits4w")
    if commits is not None:
        metric_items.append({
            "label": "Repository activity", "earned": 3 if commits >= 10 else (1 if commits > 0 else 0), "max": 3,
            "reason": "%s commits in the last 4 weeks across public repositories (CoinGecko)" % commits,
        })
    if metric_items:
        dimension("protocol_metrics", "Protocol metrics", 15, "measured", metric_items,
                  "Third-party figures from DefiLlama and CoinGecko, not self-reported.")
    else:
        dimension("protocol_metrics", "Protocol metrics", 15, "unmeasured", [],
                  "No DefiLlama or CoinGecko entry matched this project's domain or handle, so TVL and "
                  "market data could not be read from a third party.")

    # 8. Funding ----------------------------------------------------------
    rounds = llama.get("funding") or []
    if rd.get("totalFundingUsd"):
        disclosed = sum(r["amountUsdM"] * 1e6 for r in rounds if r.get("amountUsdM"))
        items = [{
            "label": "Total funding on record", "earned": 10, "max": 10,
            "reason": "$%s across %s investors (RootData)%s" % (
                "{:,.0f}".format(rd["totalFundingUsd"]), rd.get("investorCount") or 0,
                "" if not disclosed else
                "; DefiLlama's disclosed rounds sum to about $%s" % "{:,.0f}".format(disclosed)),
        }]
        if rd.get("leadInvestors"):
            items.append({"label": "Lead investors", "earned": 0, "max": 0,
                          "reason": ", ".join(rd["leadInvestors"])})
        if rd.get("established"):
            items.append({"label": "Established", "earned": 0, "max": 0, "reason": str(rd["established"])})
        dimension("funding", "Funding", 10, "measured", items,
                  "Totals from RootData; DefiLlama's per-round figures are shown alongside rather than "
                  "reconciled, because the two count different things.")
    elif rounds:
        total = sum(r["amountUsdM"] for r in rounds if r.get("amountUsdM"))
        items = [{
            "label": "Funding rounds on record", "earned": 10, "max": 10,
            "reason": "%d round(s)%s, most recent %s" % (
                len(rounds),
                ", about $%.1fM disclosed in total" % total if total else "",
                rounds[-1].get("date") or "date unknown"),
        }]
        for round_item in rounds[-3:]:
            items.append({
                "label": round_item.get("round") or "Round", "earned": 0, "max": 0,
                "reason": "%s%s%s" % (
                    round_item.get("date") or "",
                    " — $%sM" % round_item["amountUsdM"] if round_item.get("amountUsdM") else "",
                    " — " + ", ".join(round_item.get("leadInvestors") or []) if round_item.get("leadInvestors") else ""),
            })
        dimension("funding", "Funding", 10, "measured", items,
                  "Historic rounds recorded by DefiLlama. Past fundraising is not evidence of current traction.")
    else:
        dimension("funding", "Funding", 10, "unmeasured", [],
                  "No funding round is on record for this project in the free sources. Absence of a record "
                  "is not evidence that no round happened.")

    # 9. Attention ---------------------------------------------------------
    # RootData is used for structured team and funding records only. Its heat
    # index is not treated as a project-quality signal.
    dimension("attention", "Attention", 8, "unmeasured", [],
              "No independent audience or social activity feed is connected.")

    # 10. Team ------------------------------------------------------------
    team = rd.get("team") or []
    if team:
        items = [{"label": person.get("name"), "earned": 0, "max": 0,
                  "reason": person.get("role") or "Role not listed"} for person in team[:8]]
        items.insert(0, {"label": "Named team record", "earned": 10, "max": 10,
                         "reason": "%d team member(s) returned by RootData" % len(team)})
        dimension("team", "Team", 10, "measured", items)
    else:
        dimension("team", "Team", 10, "unmeasured", [], "No verified team record was returned.")

    measured = [d for d in dimensions if d["state"] == "measured"]
    earned = sum(d["earned"] or 0 for d in measured)
    possible = sum(d["max"] for d in measured)
    return {
        "dimensions": dimensions,
        "earned": earned,
        "possible": possible,
        "measuredCount": len(measured),
        "unmeasuredCount": len(dimensions) - len(measured),
        "note": "Provisional: %d of %d dimensions could be measured. Unmeasured dimensions are excluded "
                "from the total rather than scored zero." % (len(measured), len(dimensions)),
    }


# --------------------------------------------------------------------------
# Dossier assembly
# --------------------------------------------------------------------------

CONTRACT_RE = re.compile(r"^0x[a-f0-9]{40}$", re.I)
X_HOSTS = ("x.com", "twitter.com")


def classify_input(raw: str) -> dict:
    query = raw.strip()
    lowered = query.lower()
    bare = re.sub(r"^https?://", "", lowered)
    bare = re.sub(r"^www\.", "", bare).rstrip("/")

    if CONTRACT_RE.match(query):
        return {"kind": "contract", "value": query}
    if bare.startswith(X_HOSTS) or query.startswith("@"):
        handle = query.lstrip("@")
        if bare.startswith(X_HOSTS):
            handle = bare.split("/", 1)[1].split("/")[0].split("?")[0]
        return {"kind": "x", "value": handle, "url": "https://x.com/%s" % handle}
    if re.match(r"^[a-z0-9.-]+\.[a-z]{2,}(/.*)?$", bare):
        return {"kind": "website", "value": bare, "url": "https://" + bare}
    return {"kind": "unknown", "value": query}


def build_dossier(raw_query: str, fresh: bool = False, profile: str = "deep") -> dict:
    target = classify_input(raw_query)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    chains = chain_snapshot(fresh=fresh)
    dossier = {
        "query": raw_query.strip(),
        "target": target,
        "checkedAt": now,
        "chains": chains,
        "receipts": {
            "generatedAt": now,
            "networks": [
                {
                    "key": entry["key"],
                    "label": entry["label"],
                    "rpc": entry["rpc"],
                    "chainId": entry.get("chainId"),
                    "headBlock": entry.get("blockNumber"),
                    "ok": entry.get("ok"),
                }
                for entry in chains["networks"]
            ],
            "rule": "No score is issued until Arc membership is proven by RPC or explicitly left unverified.",
        },
    }

    # --- ecosystem gate: documented non-Arc surfaces -----------------------
    if target["kind"] in ("website", "x"):
        bare = target["value"]
        if any(bare == marker or bare.startswith(marker + "/") for marker in NON_ARC_MARKERS):
            dossier.update(
                {
                    "status": "not-arc",
                    "statusLabel": "Not in the Arc ecosystem",
                    "title": raw_query.strip(),
                    "description": "This identifier matches a known non-Arc surface. ArcDossier stopped before assembling an Arc dossier.",
                    "sources": [],
                    "gaps": [],
                    "score": None,
                    "scoreBreakdown": [],
                    "mode": "Ecosystem gate",
                }
            )
            return dossier

    sources = []
    probes = {}
    discovery = {}
    explorer_record = {"networks": {}}

    # --- website / docs / repository surfaces ------------------------------
    if target["kind"] == "website":
        base = "https://" + target["value"]
        catalogued = OFFICIAL_SURFACES.get(target["value"].rstrip("/")) or {}
        probe = probe_url(base, fresh=fresh)
        probes["website"] = probe
        sources.append(
            {
                "id": "website",
                "label": "Official website",
                "target": base,
                "state": "fetched" if probe.get("ok") else "failed",
                "evidence": probe,
                "note": "Fetched live by this server" if probe.get("ok") else probe.get("error", "not reachable"),
            }
        )

        # One input should lead to the project's other surfaces.
        surfaces = probe.get("surfaces") or {}
        if surfaces.get("social"):
            handle = surfaces["social"][0]
            social_probe = probe_url("https://x.com/%s" % handle, fresh=fresh)
            probes["social"] = social_probe
            sources.append(
                {
                    "id": "social",
                    "label": "X profile (discovered)",
                    "target": "https://x.com/%s" % handle,
                    "state": "fetched" if social_probe.get("ok") else "failed",
                    "evidence": social_probe,
                    "note": "Linked from the official page. Presence is confirmed; ownership is not.",
                }
            )
            discovery["social"] = handle
            back = {domain.lower() for domain in ((social_probe.get("surfaces") or {}).get("domains") or [])}
            own = target["value"].lower().lstrip("www.")
            if any(domain == own or domain.endswith("." + own) or own.endswith("." + domain) for domain in back):
                discovery["crossLinked"] = True
                discovery["linkedDomain"] = target["value"]
        if surfaces.get("addresses"):
            discovery["addresses"] = surfaces["addresses"]

        discovered = probe.get("discovered") or {}
        docs_url = catalogued.get("docs") or discovered.get("docs")
        docs_origin = "listed in the curated catalog" if catalogued.get("docs") else "discovered on the official page"
        if docs_url:
            docs_probe = probe_url(docs_url, fresh=fresh)
            probes["docs"] = docs_probe
            sources.append(
                {
                    "id": "docs",
                    "label": "Documentation",
                    "target": docs_url,
                    "state": "fetched" if docs_probe.get("ok") else "failed",
                    "evidence": docs_probe,
                    "note": docs_origin if docs_probe.get("ok") else docs_probe.get("error", "not reachable"),
                }
            )
        else:
            sources.append(
                {
                    "id": "docs",
                    "label": "Documentation",
                    "target": None,
                    "state": "gap",
                    "evidence": {},
                    "note": "No documentation link was published on the official page.",
                }
            )

        repo_url = discovered.get("github")
        if repo_url:
            repo_probe = probe_url(repo_url, fresh=fresh)
            probes["github"] = repo_probe
            sources.append(
                {
                    "id": "github",
                    "label": "Source repository",
                    "target": repo_url,
                    "state": "fetched" if repo_probe.get("ok") else "failed",
                    "evidence": repo_probe,
                    "note": "discovered on the official page" if repo_probe.get("ok") else repo_probe.get("error", "not reachable"),
                }
            )
        else:
            sources.append(
                {
                    "id": "github",
                    "label": "Source repository",
                    "target": None,
                    "state": "gap",
                    "evidence": {},
                    "note": "No public repository link was published on the official page.",
                }
            )

    if target["kind"] == "x":
        probe = probe_url(target["url"], fresh=fresh)
        probes["social"] = probe
        sources.append(
            {
                "id": "social",
                "label": "X profile",
                "target": target["url"],
                "state": "fetched" if probe.get("ok") else "failed",
                "evidence": probe,
                "note": "Profile shells are login-walled: presence is confirmed, ownership is not.",
            }
        )
        # Route from an X handle to a website. A candidate only counts as the
        # project's site when the page links back to the same handle: one-way
        # links from a profile are routinely tweets, mirrors or unrelated CDNs.
        surfaces = probe.get("surfaces") or {}
        handle = str(target.get("value") or "").lower()
        candidates = [domain for domain in (surfaces.get("domains") or []) if is_project_host(domain)][:3]
        chosen, cross_linked, rejected = None, False, []
        for domain in candidates:
            site_probe = probe_url("https://" + domain, fresh=fresh)
            back_links = {(value or "").lower() for value in ((site_probe.get("surfaces") or {}).get("social") or [])}
            if site_probe.get("ok") and handle and handle in back_links:
                chosen, cross_linked, probes["website"] = domain, True, site_probe
                break
            if site_probe.get("ok") and chosen is None and not cross_linked:
                chosen, probes["website"] = domain, site_probe
            else:
                rejected.append({"domain": domain, "reason": site_probe.get("error", "does not link back to the profile")})

        if chosen:
            site_probe = probes["website"]
            sources.append(
                {
                    "id": "website",
                    "label": "Website (discovered from the X profile)",
                    "target": "https://" + chosen,
                    "state": "fetched" if site_probe.get("ok") else "failed",
                    "evidence": site_probe,
                    "note": ("Mutually linked: the profile points here and this page links back to x.com/%s" % handle)
                            if cross_linked else
                            ("Linked from the profile, but the page does not link back to x.com/%s — treat as unconfirmed" % handle),
                }
            )
            discovery.update({"website": chosen, "linkedDomain": chosen, "crossLinked": cross_linked})
        if rejected:
            discovery["rejectedCandidates"] = rejected
        if surfaces.get("addresses"):
            discovery["addresses"] = surfaces["addresses"]

    # --- contract proof on both networks ----------------------------------
    contract_record = None
    metrics_record = None
    if target["kind"] == "contract":
        contract_record = contract_evidence(target["value"], fresh=fresh)
        per_network = contract_record.get("networks", {})
        for network in NETWORK_ORDER:
            entry = per_network.get(network, {})
            deployed = bool(entry.get("deployed"))
            sources.append(
                {
                    "id": "contract-" + network,
                    "label": "Arc deployment · %s" % entry.get("label", network),
                    "target": target["value"],
                    "state": "proven" if deployed else ("gap" if entry.get("ok") else "failed"),
                    "evidence": entry,
                    "note": (
                        "%s bytes of bytecode at block %s" % (entry.get("bytecodeBytes"), entry.get("checkedAtBlock"))
                        if deployed
                        else ("No bytecode at this address" if entry.get("ok") else entry.get("error", "check failed"))
                    ),
                }
            )
        # Deterministic trader-facing metrics, only where bytecode exists.
        if any(item.get("deployed") for item in per_network.values()):
            try:
                metrics_record = token_metrics(target["value"], fresh=fresh, profile=profile)
            except Exception:
                metrics_record = None
            explorer_nets = {}
            for network in NETWORK_ORDER:
                explorer_nets[network] = explorer_token_facts(network, target["value"], fresh=fresh)
            explorer_record = {"networks": explorer_nets}
        # A contract address cannot be reverse-resolved to a website or an X account:
        # the chain holds no such registry and the explorer publishes token metadata,
        # not the project's home page. State that rather than guessing.
        discovery["note"] = ("A contract address cannot be reverse-resolved to a website or an X account. "
                             "The explorer reports token metadata for this address, not a project home page.")

    # --- third-party providers -------------------------------------------
    # Matched on the domain and handle the project itself publishes, so this does
    # not depend on guessing from a name.
    domain = target.get("value") if target.get("kind") == "website" else discovery.get("website")
    handle = target.get("value") if target.get("kind") == "x" else discovery.get("social")
    lookup_name = clean_project_name(
        dossier.get("curatedAs") or (probes.get("website") or {}).get("title") or domain or "")
    providers = {}
    match = llama_match(domain=domain or "", handle=handle or "", name=lookup_name)
    if match:
        row = match["row"]
        detail = llama_detail(row.get("slug") or "")
        providers["defillama"] = {
            "matchedBy": match["matchedBy"],
            "name": row.get("name"),
            "slug": row.get("slug"),
            "category": row.get("category"),
            "chains": row.get("chains"),
            "tvlUsd": row.get("tvl"),
            "mcapUsd": row.get("mcap"),
            "change1dPct": row.get("change1d"),
            "change7dPct": row.get("change7d"),
            "url": row.get("url"),
            "twitter": row.get("twitter"),
            "funding": detail.get("funding") or [],
            "incidents": detail.get("incidents") or [],
            "fees": llama_fees(row.get("slug") or ""),
            "auditLinks": detail.get("auditLinks"),
            "sourceUrl": "https://defillama.com/protocol/" + str(row.get("slug") or ""),
            "template": product_template(row.get("category") or ""),
        }
    llama_symbol = ((providers.get("defillama") or {}).get("name") and None) or None
    llama_symbol = (match.get("row") or {}).get("symbol") if match else None
    gecko = gecko_lookup(lookup_name, llama_symbol or "")
    if not gecko and llama_symbol:
        gecko = gecko_lookup(llama_symbol, "")
    if gecko:
        providers["coingecko"] = dict(gecko, sourceUrl="https://www.coingecko.com/en/coins/" + str(gecko.get("id")))

    catalog_entry = OFFICIAL_SURFACES.get((domain or "").rstrip("/"))
    if ((catalog_entry or {}).get("name") == "Arc Network" or str(handle or "").lower() == "arc"):
        chain_metrics = llama_arc_chain_metrics(fresh=fresh)
        if chain_metrics:
            providers["arcChain"] = chain_metrics

    # RootData is the structured team and funding source. Calls remain cached and
    # budgeted, but it must not be skipped merely because market data was found.
    if rootdata_enabled():
        # RootData searches by project name, so the name matters. A site that
        # blocks fetching leaves no title, but DefiLlama has usually already given
        # us the project's real name, and the domain itself is the last resort.
        rootdata_name = lookup_name
        if match and (match.get("row") or {}).get("name"):
            rootdata_name = (match["row"]["name"] or "").strip()
        if not rootdata_name or len(rootdata_name) < 3:
            rootdata_name = re.sub(r"\.(com|io|fi|org|net|xyz|finance|app|money|exchange)$", "", (domain or ""))
        rootdata = rootdata_lookup(rootdata_name, domain or "", handle or "")
        if rootdata.get("matched") or rootdata.get("reason") or rootdata.get("rejected"):
            providers["rootdata"] = rootdata
            providers["rootdata"]["callsToday"] = rootdata_calls_today()
            providers["rootdata"]["dailyBudget"] = ROOTDATA_DAILY_CALLS

    self_reported = []
    for source_id in ("website", "docs", "social"):
        probe = probes.get(source_id) or {}
        for claim in probe.get("selfReported") or []:
            self_reported.append(dict(claim, source=source_id, target=probe.get("url")))
    seen_claims = set()
    self_reported = [c for c in self_reported
                     if not ((c["kind"], c["value"].lower()) in seen_claims or seen_claims.add((c["kind"], c["value"].lower())))][:10]

    # --- curated official surfaces ----------------------------------------
    curated = None
    if target["kind"] == "website":
        curated = OFFICIAL_SURFACES.get(target["value"].rstrip("/"))
    elif target["kind"] == "x":
        curated_name = OFFICIAL_SOCIAL.get(target["value"].lower())
        if curated_name:
            curated = {"name": curated_name, "description": OFFICIAL_SURFACES["arc.network"]["description"]}
    if curated:
        dossier["curatedAs"] = curated["name"]

    # --- title / description ----------------------------------------------
    site_probe = probes.get("website") or probes.get("docs") or {}
    title = ""
    description = ""
    if curated:
        title, description = curated["name"], curated["description"]
    elif site_probe.get("ok"):
        title = site_probe.get("title") or target["value"]
        description = site_probe.get("description") or ""
    elif contract_record:
        title = target["value"][:10] + "…" + target["value"][-8:]
        if contract_record.get("knownAs"):
            title = contract_record["knownAs"]
            description = "Known Arc deployment from the curated catalog. Address confirmed by live RPC on: %s." % (
                ", ".join(contract_record.get("deployedOn") or ["no network"])
            )
        else:
            description = ""
    else:
        title = target["value"]
        description = ""

    # --- transparent score ------------------------------------------------
    breakdown = []

    def add(label, earned, maximum, reason):
        breakdown.append({"label": label, "earned": earned, "max": maximum, "reason": reason})

    deployed_on = contract_record.get("deployedOn") if contract_record else None
    if contract_record and "mainnet" in (deployed_on or []):
        mainnet_entry = contract_record["networks"]["mainnet"]
        add("Arc deployment proven by RPC", 30, 30,
            "%s bytes of mainnet bytecode at block %s" % (mainnet_entry["bytecodeBytes"], mainnet_entry["checkedAtBlock"]))
    elif contract_record and "testnet" in (deployed_on or []):
        testnet_entry = contract_record["networks"]["testnet"]
        add("Arc deployment proven by RPC", 20, 30,
            "Testnet only: %s bytes at block %s, nothing on mainnet" % (testnet_entry["bytecodeBytes"], testnet_entry["checkedAtBlock"]))
    elif contract_record:
        add("Arc deployment proven by RPC", 0, 30, contract_record.get("verdict", "not proven"))
    else:
        add("Arc deployment proven by RPC", 0, 30, "No contract address supplied for this search")

    website_probe = probes.get("website")
    if website_probe and website_probe.get("ok"):
        add("Official website reachable", 14, 14, "HTTP %s, %s bytes" % (website_probe.get("httpStatus"), website_probe.get("bytes")))
    elif website_probe:
        add("Official website reachable", 0, 14, website_probe.get("error", "not reachable"))
    elif target["kind"] == "contract":
        add("Official website reachable", 0, 14, "No official website supplied with this search")

    docs_probe = probes.get("docs")
    if docs_probe and docs_probe.get("ok"):
        add("Documentation reachable", 14, 14, "HTTP %s" % docs_probe.get("httpStatus"))
    elif docs_probe:
        add("Documentation reachable", 0, 14, docs_probe.get("error", "not reachable"))
    elif target["kind"] == "website":
        add("Documentation reachable", 0, 14, "The official page published no documentation link")
    elif target["kind"] == "contract":
        add("Documentation reachable", 0, 14, "No documentation surface supplied with this search")

    repo_probe = probes.get("github")
    if repo_probe and repo_probe.get("ok"):
        add("Source repository reachable", 16, 16, repo_probe.get("finalUrl", ""))
    elif repo_probe:
        add("Source repository reachable", 0, 16, repo_probe.get("error", "not reachable"))
    elif target["kind"] == "website":
        add("Source repository reachable", 0, 16, "The official page published no repository link")
    elif target["kind"] == "contract":
        add("Source repository reachable", 0, 16, "No repository supplied with this search")

    social_probe = probes.get("social")
    if social_probe and social_probe.get("ok"):
        add("Social profile present", 8, 8, "Profile shell loaded; ownership not verified")
    elif target["kind"] == "contract":
        add("Social profile present", 0, 8, "No social profile supplied with this search")

    mentions = set()
    for probe in probes.values():
        if probe.get("ok"):
            mentions.update(probe.get("ecosystemMentions") or [])
    if mentions:
        add("Arc references found in fetched pages", 12, 12, "Found: " + ", ".join(sorted(mentions)))
    elif probes:
        add("Arc references found in fetched pages", 0, 12, "No Arc reference in the pages this server could read")
    elif target["kind"] == "contract":
        add("Arc references found in fetched pages", 0, 12, "A contract-only search fetches no pages")

    if description:
        add("Self-described summary available", 6, 6, "Taken from the source page or the curated catalog")
    else:
        add("Self-described summary available", 0, 6, "The source published no usable description")

    score = min(100, sum(item["earned"] for item in breakdown))

    # --- status -----------------------------------------------------------
    status = "unverified"
    status_label = "Arc membership not verified"
    mode = "Live verification required"

    proven_mainnet = "mainnet" in (deployed_on or [])
    proven_testnet = "testnet" in (deployed_on or [])
    any_surface = any(probe.get("ok") for probe in probes.values())

    if curated:
        status, status_label, mode = "verified", "Confirmed Arc surface", "Curated catalog + live probe"
    elif proven_mainnet:
        status, status_label, mode = "verified", "Deployed on Arc mainnet", "RPC proof + live probe" if any_surface else "RPC proof"
    elif proven_testnet:
        status, status_label = "candidate", "Arc testnet deployment only"
        mode = "RPC proof + live probe" if any_surface else "RPC proof"
    elif any_surface:
        status, status_label, mode = "candidate", "Surface live, Arc membership unproven", "Live probe only"
    elif contract_record:
        status, status_label, mode = "unverified", "No Arc bytecode at this address", "RPC checked, nothing found"

    if status == "unverified":
        # No score is issued, but the full breakdown stays visible so the zeros
        # are explained rather than hidden.
        score = None

    # --- gaps -------------------------------------------------------------
    gaps = []
    if contract_record and not deployed_on:
        gaps.append("No bytecode on Arc mainnet or testnet. If this project claims an Arc deployment, the published address is wrong or lives on another chain.")
    if contract_record and proven_testnet and not proven_mainnet:
        gaps.append("Testnet deployment only. A testnet contract is cheap to deploy and does not prove a project is live on Arc mainnet.")
    if contract_record is None and not curated:
        gaps.append("No contract address supplied, so Arc membership cannot be proven by RPC. Find the project's Arc contract address.")
    for probe in probes.values():
        if not probe.get("ok"):
            gaps.append("Could not read %s: %s" % (probe.get("url"), probe.get("error", "unknown error")))
    if social_probe and social_probe.get("ok") and not discovery.get("crossLinked"):
        gaps.append("X profile presence is not ownership. Confirm a link from the account to the same domain.")
    if contract_record and deployed_on:
        gaps.append("Deployment is proven, ownership is not. Nothing here links this address to a website, an X account, or a named team.")
    if not gaps:
        gaps.append("Every check this prototype can run passed. Filters, alerts and ranking still require the shared data service.")

    dossier.update(
        {
            "status": status,
            "statusLabel": status_label,
            "mode": mode,
            "title": title,
            "description": description or "No source-supplied description was readable.",
            "sources": sources,
            "gaps": gaps,
            "score": score,
            "scoreBreakdown": breakdown,
            "erc20": (contract_record or {}).get("erc20"),
            "tokenMetrics": metrics_record,
            "explorerFacts": explorer_record,
            "discovery": discovery,
            "providers": providers,
            "selfReported": self_reported,
        }
    )
    dossier["_contract"] = contract_record or {}
    dossier["_metrics"] = metrics_record or {}
    dossier["_explorer"] = explorer_record or {}
    dossier["_probes"] = probes
    dossier["_discovery"] = discovery
    dossier["_providers"] = providers
    dossier["_selfReported"] = self_reported
    dossier["scorecard"] = build_scorecard(dossier)
    dossier["gradingFrame"] = build_grading_frame(dossier)
    for key in ("_contract", "_metrics", "_explorer", "_probes", "_discovery", "_providers", "_selfReported"):
        dossier.pop(key, None)
    return dossier


# --------------------------------------------------------------------------
# AI analysis layer
# --------------------------------------------------------------------------
# Division of labour, enforced structurally rather than by discipline:
#
#   deterministic code  -> numbers, scoring, risk signals, data freshness
#   the model           -> narrative, cross-source comparison, explanation
#
# The model's output schema contains no score field at all, so a model cannot
# influence a score even if it tries. Every claim it makes must cite a fact id
# from the evidence packet; citations that do not resolve are moved into
# `unknowns` instead of being displayed as if they were sourced.

AI_PROVIDER = os.environ.get("ARC_AI_PROVIDER", "minimax").strip().lower()
AI_MODEL = os.environ.get("ARC_AI_MODEL", "MiniMax-M3.1-Flash-Preview")
AI_BASE_URL = os.environ.get("ARC_AI_BASE_URL", "https://api.minimax.cn/anthropic").rstrip("/")
AI_PROTOCOL = os.environ.get("ARC_AI_PROTOCOL", "anthropic").strip().lower()
AI_API_KEY = os.environ.get("ARC_AI_API_KEY") or os.environ.get("MINIMAX_API_KEY") or ""

# The public product has one report path: a high-throughput model, no explicit
# reasoning effort, a bounded evidence packet, and one model request. The legacy
# deep plan remains available to old API clients but is no longer exposed by the
# interface and has a strict output cap.
AI_MODES = {
    "quick": {
        "model": os.environ.get("ARC_AI_MODEL_QUICK", "MiniMax-M2.7-highspeed"),
        "effort": os.environ.get("ARC_AI_EFFORT_QUICK", "low"),
        "scan": "quick",
        "supportsEffort": False,
        "timeout": int(os.environ.get("ARC_AI_TIMEOUT_QUICK", "22")),
        "maxOutputTokens": int(os.environ.get("ARC_AI_MAX_TOKENS_QUICK", "2200")),
        "packetChars": int(os.environ.get("ARC_AI_PACKET_CHARS_QUICK", "16000")),
        "allowRetry": False,
    },
    "deep": {
        "model": os.environ.get("ARC_AI_MODEL_DEEP", AI_MODEL),
        "effort": os.environ.get("ARC_AI_EFFORT_DEEP", "medium"),
        "scan": "deep",
        "supportsEffort": True,
        "timeout": int(os.environ.get("ARC_AI_TIMEOUT_DEEP", str(REPORT_MODEL_TIMEOUT))),
        "maxOutputTokens": int(os.environ.get("ARC_AI_MAX_TOKENS_DEEP", "3200")),
        "packetChars": int(os.environ.get("ARC_AI_PACKET_CHARS_DEEP", "36000")),
        "allowRetry": True,
    },
}
AI_EFFORTS = ("low", "medium", "high", "xhigh", "max")
AI_DAILY_CALL_BUDGET = int(os.environ.get("ARC_AI_DAILY_CALLS", "50"))
AI_DEEP_DAILY_CALL_BUDGET = int(os.environ.get("ARC_AI_DEEP_DAILY_CALLS", "10"))
AI_PACKET_CHAR_BUDGET = 36000
# Chain head blocks advance on every request, so they are excluded from the cache
# key but still included in the packet and in its provenance hash.
VOLATILE_FACT_TYPE = "chain"
REPORT_DIR = os.path.join(STATIC_DIR, "reports")
REPORT_LOG = os.path.join(REPORT_DIR, "analyses.jsonl")

ANALYSIS_SCHEMA = {
    "narrative": {
        "overview": "str", "product": "str", "traction": "str", "backing": "str",
        "tokenOpportunity": "str", "timing": "str", "overallAnalysis": "str",
    },
    "team": {"summary": "str", "verificationStatus": "str", "sourceIds": ["str"]},
    "funding": "list of {summary, sourceIds}",
    "risks": "list of {summary, severity, sourceIds}",
    "unknowns": ["str"],
    "contradictions": "list of {summary, sourceIds}",
}

# Any of these appearing in a model response are stripped and recorded.
FORBIDDEN_OUTPUT_KEYS = ("score", "rating", "grade", "confidence", "rank", "recommendation", "verdict")


def ai_status() -> dict:
    reports = load_reports()
    today = time.strftime("%Y-%m-%d", time.gmtime())
    used_today = sum(1 for report in reports
                     if str(report.get("generatedAt", "")).startswith(today)
                     and not report.get("mock"))
    return {
        "configured": bool(AI_API_KEY) or AI_PROVIDER == "mock",
        "provider": AI_PROVIDER,
        "model": AI_MODES["quick"]["model"],
        "protocol": AI_PROTOCOL,
        "baseUrl": AI_BASE_URL,
        "endpointHost": urllib.parse.urlparse(AI_BASE_URL).netloc,
        "keyPresent": bool(AI_API_KEY),
        "mock": AI_PROVIDER == "mock",
        "efforts": [],
        "defaultEffort": None,
        "dailyCallBudget": AI_DAILY_CALL_BUDGET,
        "callsUsedToday": used_today,
        "cachedAnalyses": len(reports),
        "schema": ANALYSIS_SCHEMA,
    }


def public_ai_status() -> dict:
    """What the interface is allowed to know. The model, provider and protocol are
    deliberately withheld: the operator can read them from the report log or from
    /api/ai/status?admin=1, but they are not shown to whoever is screening."""
    status = ai_status()
    return {
        "configured": status["configured"],
        "mockMode": status["mock"],
        "modes": [
            {"id": "quick", "label": "Research report",
             "detail": "A detailed report from a bounded evidence set, without deep reasoning."},
        ],
        "dailyCallBudget": status["dailyCallBudget"],
        "callsUsedToday": status["callsUsedToday"],
        "cachedAnalyses": status["cachedAnalyses"],
    }


def load_reports() -> list:
    if not os.path.exists(REPORT_LOG):
        return []
    reports = []
    try:
        with open(REPORT_LOG, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    reports.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        return []
    return reports


def append_report(record: dict) -> dict:
    """Append to the report hash chain without spending gas on every report."""
    os.makedirs(REPORT_DIR, exist_ok=True)
    previous = load_reports()
    record["prevHash"] = previous[-1]["hash"] if previous else None
    body = json.dumps({key: value for key, value in record.items() if key != "hash"},
                      sort_keys=True, separators=(",", ":"))
    record["hash"] = "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()
    with open(REPORT_LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def _truncate(text: str, limit: int) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def build_evidence_packet(dossier: dict, char_budget: int = AI_PACKET_CHAR_BUDGET) -> dict:
    """Compress a dossier into citable facts. IDs are stable and server-assigned."""
    facts = []
    counter = 0

    def add_fact(kind: str, text: str):
        nonlocal counter
        counter += 1
        facts.append({"id": "fact-%d" % counter, "type": kind, "text": _truncate(text, 1200)})

    for source in dossier.get("sources", []):
        evidence = source.get("evidence") or {}
        descriptor = "%s — %s" % (source.get("label"), source.get("state"))
        if source.get("target"):
            descriptor += " — %s" % source["target"]
        if evidence.get("title"):
            descriptor += " — title: %s" % evidence["title"]
        if evidence.get("description"):
            descriptor += " — description: %s" % evidence["description"]
        if evidence.get("httpStatus"):
            descriptor += " — HTTP %s, %s bytes" % (evidence.get("httpStatus"), evidence.get("bytes"))
        if evidence.get("bytecodeBytes"):
            descriptor += " — %s bytes of bytecode at block %s" % (evidence.get("bytecodeBytes"), evidence.get("checkedAtBlock"))
        add_fact("source:" + str(source.get("id")), descriptor + " — " + str(source.get("note", "")))

    metrics = dossier.get("tokenMetrics") or {}
    for network, entry in (metrics.get("networks") or {}).items():
        if not entry.get("deployed"):
            continue
        label = entry.get("label", network)
        identity = entry.get("identity") or {}
        add_fact("metrics:identity",
                 "On %s the contract reports symbol=%s name=%s decimals=%s totalSupply=%s."
                 % (label, identity.get("symbol"), identity.get("name"), identity.get("decimals"), identity.get("totalSupply")))
        for probe in entry.get("structure") or []:
            if probe.get("callable"):
                add_fact("metrics:structure", "On %s, %s() is callable and returns %s."
                         % (label, probe.get("name"), probe.get("value")))
        activity = entry.get("activity") or {}
        window = activity.get("window") or {}
        add_fact("metrics:activity",
                 "On %s, across blocks %s-%s (~%s minutes) the server counted %s transfers from %s unique addresses, "
                 "%s mints, %s burns and %s transfers of at least 1%% of supply."
                 % (label, window.get("fromBlock"), window.get("toBlock"), window.get("estimatedMinutes"),
                    activity.get("transfers"), activity.get("uniqueAddresses"),
                    activity.get("mints"), activity.get("burns"), activity.get("largeTransfers")))
        for signal in entry.get("signals") or []:
            add_fact("metrics:signal", "Deterministic signal on %s [%s]: %s — %s"
                     % (label, signal.get("severity"), signal.get("label"), signal.get("detail")))

    for gap in dossier.get("gaps", []):
        add_fact("gap", gap)

    scorecard = dossier.get("scorecard") or {}
    for dimension in scorecard.get("dimensions") or []:
        if dimension.get("state") != "measured":
            continue
        for item in dimension.get("items") or []:
            add_fact("scorecard:" + str(dimension.get("key")),
                     "%s — %s: %s (%s/%s)" % (dimension.get("label"), item.get("label"),
                                              item.get("reason"), item.get("earned"), item.get("max")))

    explorer_facts = dossier.get("explorerFacts") or {}
    for network, entry in (explorer_facts.get("networks") or {}).items():
        if not entry.get("ok"):
            continue
        verification = entry.get("verification") or {}
        add_fact("explorer",
                 "The explorer reports %s (%s) on %s with %s holders. Source verified: %s. Proxy: %s."
                 % (entry.get("name"), entry.get("symbol"), entry.get("label"),
                    entry.get("holdersCount"), verification.get("verified"),
                    verification.get("isProxy")))
        distribution = entry.get("distribution") or {}
        if distribution.get("top10Pct") is not None:
            add_fact("explorer:distribution",
                     "On %s the top holder controls %s%% and the top 10 control %s%% of total supply."
                     % (entry.get("label"), distribution.get("top1Pct"), distribution.get("top10Pct")))

    discovery_notes = dossier.get("discovery") or {}
    if discovery_notes.get("website"):
        add_fact("discovery", "The X profile links out to %s." % discovery_notes["website"])
    if discovery_notes.get("social"):
        add_fact("discovery", "The official page links out to the X profile @%s." % discovery_notes["social"])
    if discovery_notes.get("addresses"):
        add_fact("discovery", "Contract addresses published on the supplied surface: %s"
                 % ", ".join(discovery_notes["addresses"]))
    if discovery_notes.get("note"):
        add_fact("discovery:limit", discovery_notes["note"])

    breakdown = dossier.get("scoreBreakdown") or []
    if breakdown:
        add_fact("score:breakdown",
                 "Deterministic Arc membership score %s out of 100. Breakdown: %s"
                 % (dossier.get("score"),
                    "; ".join("%s %s/%s (%s)" % (item["label"], item["earned"], item["max"], item.get("reason", ""))
                              for item in breakdown)))

    for chain in ((dossier.get("chains") or {}).get("networks") or []):
        if chain.get("ok"):
            add_fact("chain", "%s reports chainId %s at head block %s."
                     % (chain.get("label"), chain.get("chainId"), chain.get("blockNumber")))

    # Respect a fixed input budget instead of filling the 1M-token window.
    kept, used = [], 0
    for fact in facts:
        cost = len(fact["text"]) + 40
        if used + cost > char_budget:
            break
        kept.append(fact)
        used += cost

    packet = {
        "version": 2,
        "query": dossier.get("query"),
        "title": dossier.get("title"),
        "target": dossier.get("target"),
        "status": dossier.get("status"),
        "statusLabel": dossier.get("statusLabel"),
        "score": dossier.get("score"),
        "facts": kept,
        "factsOmittedForBudget": max(0, len(facts) - len(kept)),
        "checkedAt": dossier.get("checkedAt"),
        "gradingFrame": dossier.get("gradingFrame") or {},
    }
    canonical = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    packet["packetHash"] = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    # A strict hash of everything is useless as a cache key: the timestamp and the
    # chain head block change on every request, so every call would look new and
    # burn quota. cacheKey covers the substantive evidence only. The drift it
    # tolerates is visible to the reader in the provenance panel.
    stable = {
        "query": packet["query"],
        "target": packet["target"],
        "status": packet["status"],
        "score": packet["score"],
        "promptVersion": AI_PROMPT_VERSION,
        "facts": [fact for fact in kept if fact["type"] != VOLATILE_FACT_TYPE],
    }
    stable_canonical = json.dumps(stable, sort_keys=True, separators=(",", ":"))
    packet["cacheKey"] = "sha256:" + hashlib.sha256(stable_canonical.encode("utf-8")).hexdigest()
    packet["cacheKeyExcludes"] = [VOLATILE_FACT_TYPE]
    return packet


SYSTEM_PROMPT = (
    "You are writing one detailed but efficient Arc ecosystem research report. You will receive a compact "
    "JSON packet whose facts each carry an id. The report must help a normal reader understand what is "
    "known without enabling deep reasoning or inventing missing information.\n\n"
    "Hard rules:\n"
    "1. Use only the supplied facts. You have no other knowledge of this project and no internet access.\n"
    "2. In narrative text, support factual sentences with inline markers such as [fact-2]. For structured "
    "team, funding, risk and contradiction items, use sourceIds. Never invent a fact id.\n"
    "3. Leave an unsupported narrative field empty. Do not add a paragraph whose only purpose is to say "
    "that data is missing. Mention a missing measurement only when it materially limits interpretation.\n"
    "4. Do not produce any score, rating, grade, confidence value, ranking or buy/sell recommendation, and "
    "never discuss expected return or price direction. Deterministic code owns every number, and the reader "
    "makes the trading decision without you.\n"
    "5. If two facts disagree, report the disagreement in contradictions rather than choosing one.\n"
    "6. Distinguish what is proven from what is merely claimed. A deployed contract proves deployment, "
    "never ownership, intent or quality.\n"
    "7. Fill the narrative fields directly: overview gives the identity and strongest findings; product "
    "explains what exists and how usable or differentiated it appears; traction explains real usage and "
    "growth; backing combines verified team and funding information; tokenOpportunity explains token use "
    "and valuation evidence; timing combines Arc ecosystem position, attention and dated catalysts; "
    "overallAnalysis connects project quality, token opportunity and timing without giving a verdict.\n"
    "8. Write two to four substantial sentences for each supported field and four to six for "
    "overallAnalysis. Use measured figures where available and explain why they matter. Do not repeat the "
    "same fact in more than two fields, and do not pad thin sections with generic commentary.\n"
    "9. Do not name data providers, transport details, HTTP status codes, or internal collection "
    "mechanics in the prose.\n"
    "10. Write for a reader who understands investing but not blockchain engineering. Prefer short "
    "sentences and everyday words. Say live contract code instead of bytecode, administrator instead "
    "of owner role, recent period checked instead of scanned window, and available data instead of "
    "evidence packet. Explain why each number matters. Avoid unexplained terms such as canonical, "
    "attribution, fully diluted valuation, liquidity, holder concentration, or value capture. If one "
    "of these ideas matters, explain it in ordinary language.\n"
    "11. Reply with a single JSON object and nothing else. No markdown fences or commentary.\n\n"
    "Required JSON shape:\n" + json.dumps(ANALYSIS_SCHEMA, indent=2)
)

# Bump this whenever SYSTEM_PROMPT changes. It is part of the cache key, so an
# analysis produced under an older prompt is never served as if it were current.
AI_PROMPT_VERSION = 8


REPORT_SCHEMA = {
    "moduleRationale": {
        "product": "str", "data": "str", "team": "str", "funding": "str",
        "token": "str", "position": "str", "heat": "str",
    },
    "keyData": [{"label": "str", "value": "str", "date": "str", "sourceIds": ["str"]}],
    "opportunities": {
        "ecosystemPosition": "str", "tokenValueCapture": "str",
        "currentValuation": "str", "catalysts": ["str"], "risks": ["str"],
    },
    "overallAnalysis": {
        "summary": "str",
        "narrative": "str",
        "attention": "str",
        "activity": "str",
        "watchItems": ["str"],
    },
}

REPORT_SYSTEM_PROMPT = (
    "You are writing the narrative sections of a research report for a curious investor screening projects in the "
    "Arc ecosystem. The report follows a fixed seven-module framework. The numeric scores for each module "
    "have ALREADY been computed from measurements by deterministic code and are given to you; you must not "
    "produce, adjust or contradict any number, and you must not invent a score for a module that was left "
    "unscored. Where a module was unscored, explain in plain words what is missing and what would have to "
    "be measured.\n\n"
    "You will receive the evidence packet (facts with ids) and the computed grading frame.\n\n"
    "Hard rules:\n"
    "1. Every factual statement must cite the ids of the facts that support it, in a sourceIds array.\n"
    "2. Never invent a fact id. If nothing supports a statement, say so plainly instead.\n"
    "3. No buy or sell recommendation, no price target, no expected return, and no binary yes-or-no verdict.\n"
    "4. Distinguish measured figures from what a project claims about itself. Self-reported numbers are "
    "claims, never evidence.\n"
    "5. Omit unsupported modules from the narrative rather than filling the gap.\n"
    "6. Keep keyData to the three to five figures that matter most for this product type, each with the "
    "date and the source id.\n"
    "7. The final section must connect project quality, token opportunity, and timing into an overall "
    "analysis. Do not answer whether the project is worth researching with yes or no.\n"
    "8. Write for someone who understands investing but not blockchain engineering. Use short sentences "
    "and familiar words. Say live contract code instead of bytecode, administrator instead of owner role, "
    "recent period checked instead of scanned window, and available data instead of evidence packet. "
    "Explain why each number matters. Do not use specialist terms such as canonical, attribution, fully "
    "diluted valuation, liquidity, holder concentration, value capture, or unlock schedule without a plain "
    "English explanation.\n"
    "9. Make the report useful, not merely cautious. Each scored module needs two to four short sentences: "
    "what is known, why it matters, and the limit of the measurement. The overall analysis must stand alone "
    "and answer three questions in plain language: what the project appears to be, whether the token has a "
    "clear reason to gain value, and what could improve or weaken the case now. Missing data should be "
    "mentioned only when it changes one of those judgments.\n"
    "10. Reply with a single JSON object and nothing else.\n\n"
    "Required JSON shape:\n" + json.dumps(REPORT_SCHEMA, indent=2)
)

REPORT_PROMPT_VERSION = 6


def _extract_json(text: str):
    """Pull the first balanced JSON object out of a model response."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    if start < 0:
        return None
    depth, in_string, escaped = 0, False, False
    for index in range(start, len(cleaned)):
        character = cleaned[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(cleaned[start:index + 1])
                except ValueError:
                    return None
    return None


def _strip_forbidden(payload: dict) -> list:
    """Remove any score-like field the model produced. Structural, not advisory."""
    removed = []

    def walk(node, path=""):
        if isinstance(node, dict):
            for key in list(node.keys()):
                if key.lower() in FORBIDDEN_OUTPUT_KEYS:
                    removed.append((path + "/" + key).lstrip("/"))
                    node.pop(key, None)
                else:
                    walk(node[key], path + "/" + key)
        elif isinstance(node, list):
            for position, item in enumerate(node):
                walk(item, "%s/%d" % (path, position))

    walk(payload)
    return removed


def _collect_source_ids(node, found=None) -> list:
    if found is None:
        found = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "sourceIds" and isinstance(value, list):
                found.extend(str(item) for item in value)
            else:
                _collect_source_ids(value, found)
    elif isinstance(node, list):
        for item in node:
            _collect_source_ids(item, found)
    return found


def validate_analysis(payload: dict, packet: dict) -> dict:
    """Shape check plus citation check. Unresolvable citations are demoted."""
    validation = {"ok": True, "problems": [], "demoted": [], "strippedFields": []}
    if not isinstance(payload, dict):
        return {"ok": False, "problems": ["response was not a JSON object"], "demoted": [], "strippedFields": []}

    validation["strippedFields"] = _strip_forbidden(payload)
    valid_ids = {fact["id"] for fact in packet.get("facts", [])}

    unknowns = payload.get("unknowns")
    if not isinstance(unknowns, list):
        unknowns = []
        validation["problems"].append("unknowns was missing or not a list; an empty one was created")

    def citation_ok(item) -> bool:
        if not isinstance(item, dict):
            return False
        ids = [str(value) for value in (item.get("sourceIds") or [])]
        return bool(ids) and all(value in valid_ids for value in ids)

    def demote(bucket: str, item, reason: str):
        summary = item.get("summary") if isinstance(item, dict) else str(item)
        unknowns.append("[%s kept out of the report: %s] %s" % (bucket, reason, summary))
        validation["demoted"].append({"bucket": bucket, "reason": reason, "summary": summary})

    for bucket in ("funding", "risks", "contradictions"):
        items = payload.get(bucket)
        if items is None:
            payload[bucket] = []
            continue
        if not isinstance(items, list):
            payload[bucket] = []
            validation["problems"].append("%s was not a list; discarded" % bucket)
            continue
        kept = []
        for item in items:
            if citation_ok(item):
                kept.append(item)
            else:
                demote(bucket, item, "no resolvable sourceIds")
        payload[bucket] = kept

    team = payload.get("team")
    if isinstance(team, dict) and not citation_ok(team):
        if team.get("summary"):
            demote("team", {"summary": team.get("summary")}, "no resolvable sourceIds")
        payload["team"] = {"summary": "", "verificationStatus": "unverified", "sourceIds": []}

    narrative = payload.get("narrative")
    if not isinstance(narrative, dict):
        payload["narrative"] = {key: "" for key in ANALYSIS_SCHEMA["narrative"]}
        validation["problems"].append("narrative was missing; an empty one was inserted")

    payload["unknowns"] = unknowns
    cited = set(_collect_source_ids(payload))
    validation["uncitedFacts"] = [fact["id"] for fact in packet.get("facts", []) if fact["id"] not in cited]
    validation["ok"] = not validation["problems"]
    return validation


def call_model(packet: dict, effort: str, shortened: bool = False, mode: str = "quick") -> dict:
    """Provider adapter. Returns text plus usage metadata; never logs the key."""
    plan = AI_MODES.get(mode) or AI_MODES["quick"]
    model = plan["model"]
    if AI_PROVIDER == "mock":
        return mock_model(packet, effort, shortened)

    if not AI_API_KEY:
        raise RpcError("AI layer is not configured: set MINIMAX_API_KEY in the server environment")

    payload_packet = dict(packet)
    if shortened:
        payload_packet["facts"] = packet["facts"][:12]
        payload_packet["note"] = "Shortened retry: a previous response could not be validated."

    user_content = (
        "Evidence packet:\n" + json.dumps(payload_packet, sort_keys=True, separators=(",", ":")) +
        "\n\nProduce the JSON object now, using inline fact markers in narrative text and sourceIds arrays "
        "for structured items."
    )

    if AI_PROTOCOL == "openai":
        url = AI_BASE_URL + "/chat/completions"
        body = {
            "model": model,
            "max_tokens": plan["maxOutputTokens"],
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        }
        if effort and plan.get("supportsEffort"):
            body["reasoning_effort"] = effort
    else:
        # Anthropic-compatible is the documented recommended path for this model.
        url = AI_BASE_URL + "/v1/messages"
        body = {
            "model": model,
            "max_tokens": plan["maxOutputTokens"],
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_content}],
        }
        # Only the M3.x family documents effort levels; the highspeed models used
        # for quick screens reject or ignore the field, so it is sent only where
        # the mode says the model supports it.
        if effort and plan.get("supportsEffort"):
            body["output_config"] = {"effort": effort}

    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "authorization": "Bearer " + AI_API_KEY,
            "user-agent": USER_AGENT,
        },
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=plan["timeout"]) as response:
            raw = response.read(8 * 1024 * 1024)
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read(600).decode("utf-8", "replace")
        except Exception:
            pass
        raise RpcError("model endpoint returned HTTP %s %s" % (exc.code, detail[:300]))
    except Exception as exc:
        raise RpcError("model endpoint unreachable: %s" % exc.__class__.__name__)

    latency = round((time.time() - started) * 1000)
    try:
        decoded = json.loads(raw.decode("utf-8", "replace"))
    except ValueError:
        raise RpcError("model endpoint returned a non-JSON body")

    text = ""
    if isinstance(decoded.get("content"), list):
        text = "\n".join(block.get("text", "") for block in decoded["content"]
                         if isinstance(block, dict) and block.get("type") == "text")
    elif decoded.get("choices"):
        text = (decoded["choices"][0].get("message") or {}).get("content", "")

    return {
        "text": text,
        "usage": decoded.get("usage") or {},
        "model": decoded.get("model", model),
        "mode": mode,
        "latencyMs": latency,
        "protocol": AI_PROTOCOL,
        "shortenedRetry": shortened,
    }


def mock_model(packet: dict, effort: str, shortened: bool = False) -> dict:
    """Deterministic evidence-only report built from the verified packet."""
    facts = packet.get("facts", [])
    by_type = {}
    for fact in facts:
        by_type.setdefault(fact["type"], []).append(fact)

    def ids_for(*types):
        collected = []
        for kind in types:
            collected.extend(fact["id"] for fact in by_type.get(kind, []))
        return collected[:4]

    source_ids = ids_for("source:website", "source:docs", "source:social")
    website = (by_type.get("source:website") or [{}])[0].get("text", "")
    description = ""
    match = re.search(r" — description: (.*?)(?: — HTTP| — [^—]+$)", website)
    if match:
        description = match.group(1).strip()
    if not description:
        description = "The connected sources establish a live project surface, but do not provide a concise product description."

    frame = packet.get("gradingFrame") or {}
    modules = {item.get("id"): item for item in (frame.get("modules") or [])}

    def module_text(*ids, limit=5):
        lines = []
        for module_id in ids:
            item = modules.get(module_id) or {}
            if item.get("score") is not None:
                lines.extend(item.get("evidence") or [])
        return ". ".join(lines[:limit]) + ("." if lines else "")

    measured_groups = [group for group in (frame.get("groups") or []) if group.get("score") is not None]
    strongest = max(measured_groups, key=lambda item: item.get("score") or 0) if measured_groups else None
    overall = ""
    if strongest:
        overall = ("The strongest measured area is %s. Evidence coverage is %s percent, so the result should "
                   "guide research priority rather than serve as an investment decision.") \
                  % (strongest.get("name", "the measured framework").lower(), frame.get("coveragePct") or 0)

    gaps = [fact for fact in facts
            if fact.get("type") == "gap"
            and not fact.get("text", "").startswith("Every check this prototype can run passed")][:3]
    risks = [{"summary": fact["text"], "severity": "watch", "sourceIds": [fact["id"]]}
             for fact in gaps]

    payload = {
        "narrative": {
            "overview": "%s is screened as %s." % (packet.get("title") or packet.get("query"),
                                                       packet.get("statusLabel") or "an unverified project"),
            "product": description,
            "traction": module_text("data"),
            "backing": module_text("team", "funding"),
            "tokenOpportunity": module_text("token"),
            "timing": module_text("position", "heat"),
            "overallAnalysis": overall,
        },
        "team": {
            "summary": "",
            "verificationStatus": "unverified",
            "sourceIds": source_ids,
        },
        "funding": [],
        "risks": risks,
        "unknowns": [],
        "contradictions": [],
    }
    encoded = json.dumps(payload)
    return {
        "text": json.dumps(payload, indent=2),
        "usage": {
            "input_tokens": sum(len(fact["text"]) // 4 for fact in facts),
            "output_tokens": len(encoded) // 4,
        },
        "model": "mock-provider",
        "latencyMs": 12,
        "protocol": "mock",
        "shortenedRetry": shortened,
        "mock": True,
    }


def analyze(dossier: dict, effort: str = None, fresh: bool = False, mode: str = "quick") -> dict:
    """One analysis: cache -> budget -> one bounded call -> validate -> store."""
    mode = mode if mode in AI_MODES else "quick"
    plan = AI_MODES[mode]
    effort = effort or plan["effort"]
    if effort not in AI_EFFORTS:
        effort = plan["effort"]

    packet = build_evidence_packet(dossier, char_budget=plan["packetChars"])
    reports = load_reports()

    if not fresh:
        want_model = "mock-provider" if AI_PROVIDER == "mock" else plan["model"]
        for report in reversed(reports):
            if (report.get("cacheKey") == packet["cacheKey"]
                    and report.get("mode", "deep") == mode
                    and report.get("model") == want_model
                    and report.get("status") == "ok"):
                return {"status": "cached", "packet": packet, "report": report,
                        "message": "Served from the report cache. The evidence is unchanged since this "
                                   "analysis was generated, so no model call was made."}

    status = ai_status()
    if not status["configured"]:
        return {
            "status": "not-configured",
            "packet": packet,
            "message": "No AI credential is present in the server environment. Set MINIMAX_API_KEY "
                       "(or ARC_AI_API_KEY) and restart the server. Nothing was sent anywhere.",
        }

    today = time.strftime("%Y-%m-%d", time.gmtime())
    used_today = sum(1 for report in reports
                     if str(report.get("generatedAt", "")).startswith(today)
                     and not report.get("mock"))
    if used_today >= AI_DAILY_CALL_BUDGET:
        return {
            "status": "budget-exhausted",
            "packet": packet,
            "message": "Daily AI call budget reached (%d). Deterministic metrics stay available and cached "
                       "analyses are still served." % AI_DAILY_CALL_BUDGET,
        }

    attempts = []
    result = None
    last_call = None
    attempts_allowed = (False, True) if plan.get("allowRetry") else (False,)
    for shortened in attempts_allowed:
        try:
            call = call_model(packet, effort, shortened=shortened, mode=mode)
        except RpcError as exc:
            attempts.append({"shortenedRetry": shortened, "error": str(exc)})
            break
        last_call = call
        parsed = _extract_json(call.get("text", ""))
        if parsed is None:
            attempts.append({"shortenedRetry": shortened, "error": "response contained no parseable JSON object"})
            continue
        validation = validate_analysis(parsed, packet)
        result = {"call": call, "analysis": parsed, "validation": validation}
        break

    if result is None:
        # Do not spend a second request just to repair formatting. Build a useful
        # report from the same verified packet, then cache it under the requested
        # model so repeated clicks do not trigger another paid call.
        fallback_call = mock_model(packet, effort, shortened=True)
        fallback_analysis = _extract_json(fallback_call.get("text", "")) or {}
        call_meta = dict(last_call or {})
        call_meta.update({
            "model": plan["model"],
            "mode": mode,
            "mock": AI_PROVIDER == "mock",
            "protocol": call_meta.get("protocol") or AI_PROTOCOL,
            "shortenedRetry": False,
        })
        result = {
            "call": call_meta,
            "analysis": fallback_analysis,
            "validation": validate_analysis(fallback_analysis, packet),
            "evidenceFallback": True,
        }

    record = {
        "status": "ok",
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "query": dossier.get("query"),
        "title": dossier.get("title"),
        "model": result["call"].get("model", plan["model"]),
        "mode": mode,
        "provider": AI_PROVIDER,
        "mock": bool(result["call"].get("mock")),
        "protocol": result["call"].get("protocol"),
        "effort": effort,
        "usage": result["call"].get("usage") or {},
        "latencyMs": result["call"].get("latencyMs"),
        "shortenedRetry": bool(result["call"].get("shortenedRetry")),
        "evidenceFallback": bool(result.get("evidenceFallback")),
        "packetHash": packet["packetHash"],
        "cacheKey": packet["cacheKey"],
        "factCount": len(packet["facts"]),
        "analysis": result["analysis"],
        "validation": result["validation"],
        "attempts": attempts,
    }
    stored = append_report(record)
    response = {"status": "ok", "packet": packet, "report": stored}
    if record["evidenceFallback"]:
        response["message"] = ("The model response could not be used, so ArcDossier completed an evidence-only report "
                               "from the verified evidence packet without making another model call.")
    return response


def build_report(query: str, fresh: bool = False, deadline_seconds: int = REPORT_DEADLINE_SECONDS) -> dict:
    """Deep report: measurements first, narrative second, inside a hard deadline.

    Every stage checks the clock. If the model cannot finish inside the budget the
    report is returned with its measured sections complete and the narrative marked
    pending, rather than the request hanging or the whole report failing.
    """
    started = time.time()

    def elapsed_ms():
        return int((time.time() - started) * 1000)

    def remaining():
        return deadline_seconds - (time.time() - started)

    dossier = build_dossier(query, fresh=fresh, profile="deep")
    frame = dossier.get("gradingFrame") or {}
    evidence_ms = elapsed_ms()

    report = {
        "query": dossier.get("query"),
        "title": dossier.get("title"),
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "deadlineSeconds": deadline_seconds,
        "timings": {"evidenceMs": evidence_ms},
        "frame": frame,
        "sources": [
            {
                "id": source.get("id"),
                "label": source.get("label"),
                "target": source.get("target"),
                "state": source.get("state"),
                "note": source.get("note"),
            }
            for source in dossier.get("sources", [])
        ],
        "providers": dossier.get("providers") or {},
        "selfReported": dossier.get("selfReported") or [],
        "discovery": dossier.get("discovery") or {},
        "tokenMetrics": dossier.get("tokenMetrics"),
        "explorerFacts": dossier.get("explorerFacts"),
        "risks": dossier.get("gaps") or [],
    }

    status = ai_status()
    if not status["configured"]:
        report.update({"narrativeStatus": "not-configured",
                       "narrativeMessage": "The narrative layer is not configured on this server. "
                                           "The measured sections above are complete without it.",
                       "timings": {"evidenceMs": evidence_ms, "totalMs": elapsed_ms()}})
        return report

    if remaining() < 75:
        report.update({"narrativeStatus": "pending",
                       "narrativeMessage": "Evidence gathering used the time budget, so the narrative was "
                                           "skipped to stay inside the deadline.",
                       "timings": {"evidenceMs": evidence_ms, "totalMs": elapsed_ms()}})
        return report

    plan = AI_MODES["deep"]
    packet = build_evidence_packet(dossier, char_budget=plan["packetChars"])
    packet["gradingFrame"] = frame
    packet["productType"] = frame.get("productType")
    packet["measuredTotal"] = frame.get("total")
    packet["coveragePct"] = frame.get("coveragePct")
    canonical = json.dumps({"q": packet.get("query"), "f": frame,
                            "reportVersion": REPORT_PROMPT_VERSION},
                           sort_keys=True, separators=(",", ":"))
    cache_key = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    cached = _cache_get(_probe_cache, "report:" + cache_key, PROBE_CACHE_TTL)
    if cached and not fresh:
        cached = dict(cached)
        cached["timings"] = {"evidenceMs": evidence_ms, "totalMs": elapsed_ms(), "cached": True}
        cached["narrativeStatus"] = "cached"
        return cached

    reports = load_reports()
    wanted_model = "mock-provider" if AI_PROVIDER == "mock" else plan["model"]
    if not fresh:
        for prior in reversed(reports):
            if (prior.get("kind") == "report" and prior.get("status") == "ok"
                    and prior.get("cacheKey") == cache_key and prior.get("model") == wanted_model):
                report.update({
                    "narrativeStatus": "cached",
                    "narrative": prior.get("analysis") or {},
                    "mockMode": bool(prior.get("mock")),
                    "packet": packet,
                    "validation": prior.get("validation") or {},
                    "timings": {"evidenceMs": evidence_ms, "totalMs": elapsed_ms(), "cached": True},
                })
                return report

    today = time.strftime("%Y-%m-%d", time.gmtime())
    deep_used_today = sum(1 for item in reports
                          if item.get("kind") == "report"
                          and not item.get("mock")
                          and str(item.get("generatedAt", "")).startswith(today))
    if AI_PROVIDER != "mock" and deep_used_today >= AI_DEEP_DAILY_CALL_BUDGET:
        report.update({"narrativeStatus": "budget-exhausted",
                       "narrativeMessage": "The daily deep-research allowance has been used. "
                                           "The measured sections remain available.",
                       "timings": {"evidenceMs": evidence_ms, "totalMs": elapsed_ms()}})
        return report

    budget = max(45, min(REPORT_MODEL_TIMEOUT, int(remaining()) - 25))
    body_packet = dict(packet)
    body_packet.pop("packetHash", None)
    user_content = ("Evidence packet:\n" + json.dumps(body_packet, indent=2, sort_keys=True) +
                    "\n\nWrite the narrative sections now, citing fact ids in every sourceIds array.")

    call_started = time.time()
    try:
        model_result = call_report_model(user_content, budget, packet=packet)
    except RpcError as exc:
        report.update({"narrativeStatus": "pending",
                       "narrativeMessage": "The narrative step failed: %s. The measured sections are unaffected."
                                           % exc,
                       "timings": {"evidenceMs": evidence_ms, "modelMs": int((time.time() - call_started) * 1000),
                                   "totalMs": elapsed_ms()}})
        return report

    parsed = _extract_json(model_result.get("text", ""))
    if parsed is None:
        report.update({"narrativeStatus": "pending",
                       "narrativeMessage": "The narrative step returned no parseable JSON object.",
                       "timings": {"evidenceMs": evidence_ms, "modelMs": int((time.time() - call_started) * 1000),
                                   "totalMs": elapsed_ms()}})
        return report

    validation = validate_analysis(parsed, packet)
    report.update({
        "narrativeStatus": "ok",
        "narrative": parsed,
        "mockMode": bool(model_result.get("mock")),
        "packet": packet,
        "validation": validation,
        "timings": {"evidenceMs": evidence_ms, "modelMs": int((time.time() - call_started) * 1000),
                    "totalMs": elapsed_ms()},
    })
    stored = append_report({
        "kind": "report",
        "status": "ok",
        "generatedAt": report["generatedAt"],
        "query": dossier.get("query"),
        "title": dossier.get("title"),
        "model": model_result.get("model"),
        "provider": AI_PROVIDER,
        "mock": bool(model_result.get("mock")),
        "mode": "deep-report",
        "usage": model_result.get("usage") or {},
        "latencyMs": model_result.get("latencyMs"),
        "packetHash": packet.get("packetHash"),
        "cacheKey": cache_key,
        "factCount": len(packet.get("facts", [])),
        "measuredTotal": frame.get("total"),
        "grade": frame.get("grade"),
        "coveragePct": frame.get("coveragePct"),
        "analysis": parsed,
        "validation": validation,
    })
    report["reportHash"] = stored.get("hash")
    _cache_put(_probe_cache, "report:" + cache_key, report)
    return report


def call_report_model(user_content: str, timeout: int, packet: dict = None) -> dict:
    """One model call for the long-form report, with its own timeout."""
    plan = AI_MODES["deep"]
    if AI_PROVIDER == "mock":
        frame = (packet or {}).get("gradingFrame") or {}
        modules = frame.get("modules") or []
        scored = [item for item in modules if item.get("score") is not None]
        by_id = {item.get("id"): item for item in modules}

        rationale = {}
        for item in scored:
            evidence = item.get("evidence") or []
            if evidence:
                facts = ". ".join(evidence[:3]) + "."
                explanation = {
                    "product": "This confirms that something usable exists, but it does not yet show how useful or different the product is.",
                    "data": "This shows real activity during the recent period checked. One period cannot show whether use is growing or lasting.",
                    "team": "This helps establish who is responsible for execution, but it does not by itself prove future delivery.",
                    "funding": "Financial backing can extend the project's runway, but it does not prove product demand.",
                    "token": "These figures help judge whether the token has a clear role and whether its price is supported by actual use.",
                    "position": "This confirms a place in the Arc ecosystem, but not leadership within its category.",
                    "heat": "This is a current activity signal, not proof of broad or lasting market attention.",
                }.get(item.get("id"), "This is useful evidence, but it should be read together with the rest of the report.")
                rationale[item["id"]] = "%s %s" % (facts, explanation)

        position = by_id.get("position") or {}
        token = by_id.get("token") or {}
        heat = by_id.get("heat") or {}
        ecosystem_position = ""
        if position.get("score") is not None and position.get("evidence"):
            ecosystem_position = "%s. This confirms that it is present on Arc, but does not show that it leads its category." % \
                                 "; ".join(position["evidence"][:3])
        token_value = ""
        if token.get("score") is not None and token.get("evidence"):
            token_value = "%s. These facts matter only if token use is clearly connected to product demand." % \
                          "; ".join(token["evidence"][:3])
        catalysts = []
        if heat.get("score") is not None and heat.get("evidence"):
            catalysts = ["Continued activity across more users and a longer period would strengthen the case for real demand."]
        risks = []
        for item in (frame.get("riskFlags") or []):
            detail = item.get("detail") or ""
            match = re.search(r"owner\(\) returns (0x[a-fA-F0-9]+)", detail)
            if match:
                detail = ("An administrator address is set: %s. The available data does not show exactly "
                          "what this address can change.") % match.group(1)
            if detail:
                risks.append(detail)
        risks = risks[:4]
        coverage = frame.get("coveragePct")
        measured_groups = [group for group in (frame.get("groups") or []) if group.get("score") is not None]
        group_analysis = " ".join(group.get("summary") or "" for group in measured_groups).strip()
        data = by_id.get("data") or {}
        data_facts = ". ".join((data.get("evidence") or [])[:2])
        has_live_contract = any("Contract proven on Arc" in evidence
                                for item in scored for evidence in (item.get("evidence") or []))
        if has_live_contract:
            summary = ("This is a live contract on Arc with measurable recent activity. %s"
                       "The contract is active, but the available data does not yet connect it to a clearly "
                       "identified product, team, or reason for the token to gain value.") % \
                      ((data_facts + ". ") if data_facts else "")
            story = ("The strongest fact is simple: the contract exists and is being used. The weaker part is "
                     "the project story, because the address is not yet tied to an official product page, "
                     "documentation, or named team.")
            attention = ("Transfer activity shows that people or automated systems are using the contract. "
                         "It does not tell us whether the wider market is paying attention, because no verified "
                         "audience growth or dated event information is available.")
            activity_text = ("%s This is enough to show use during the recent period checked, but not enough "
                             "to prove sustained growth. A longer history would show whether activity is rising, "
                             "stable, or fading.") % (data_facts + "." if data_facts else "Recent transfers were recorded.")
            watch_items = [
                "Connect the contract address to an official project website and documentation.",
                "Confirm what the administrator address can change and whether those powers are limited.",
                "Compare transfers and active addresses across several longer periods.",
                "Check token supply, ownership concentration, trading depth, and the schedule for future token releases.",
            ]
        else:
            summary = ("%s Evidence coverage is %s percent. The report shows what can be checked today and "
                       "keeps unsupported areas out of the score.") % (group_analysis, coverage or 0)
            story = "The measured sections above show the project's current position without treating missing early-stage data as failure."
            attention = "Only measured activity and dated events should be treated as attention; project claims are not enough on their own."
            activity_text = data_facts or "No reliable usage figure is available yet."
            watch_items = []
        payload = {
            "moduleRationale": rationale,
            "keyData": [],
            "opportunities": {"ecosystemPosition": ecosystem_position,
                              "tokenValueCapture": token_value,
                              "currentValuation": "", "catalysts": catalysts, "risks": risks},
            "overallAnalysis": {
                "summary": summary,
                "narrative": story,
                "attention": attention,
                "activity": activity_text,
                "watchItems": watch_items,
            },
        }
        return {"text": json.dumps(payload), "usage": {}, "model": "mock-provider",
                "latencyMs": 5, "protocol": "mock", "mock": True}

    if not AI_API_KEY:
        raise RpcError("no AI credential configured")

    if AI_PROTOCOL == "openai":
        url = AI_BASE_URL + "/chat/completions"
        body = {"model": plan["model"], "max_tokens": plan["maxOutputTokens"],
                "messages": [{"role": "system", "content": REPORT_SYSTEM_PROMPT},
                             {"role": "user", "content": user_content}]}
        if plan.get("supportsEffort"):
            body["reasoning_effort"] = plan["effort"]
    else:
        url = AI_BASE_URL + "/v1/messages"
        body = {"model": plan["model"], "max_tokens": plan["maxOutputTokens"],
                "system": REPORT_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_content}]}
        if plan.get("supportsEffort"):
            body["output_config"] = {"effort": plan["effort"]}

    request = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"content-type": "application/json", "authorization": "Bearer " + AI_API_KEY,
                 "user-agent": USER_AGENT}, method="POST")
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(8 * 1024 * 1024)
    except urllib.error.HTTPError as exc:
        raise RpcError("model endpoint returned HTTP %s" % exc.code)
    except Exception as exc:
        raise RpcError("model endpoint unreachable or timed out (%s)" % exc.__class__.__name__)

    decoded = json.loads(raw.decode("utf-8", "replace"))
    text = ""
    if isinstance(decoded.get("content"), list):
        text = "\n".join(block.get("text", "") for block in decoded["content"]
                         if isinstance(block, dict) and block.get("type") == "text")
    elif decoded.get("choices"):
        text = (decoded["choices"][0].get("message") or {}).get("content", "")
    return {"text": text, "usage": decoded.get("usage") or {},
            "model": decoded.get("model", plan["model"]),
            "latencyMs": int((time.time() - started) * 1000), "protocol": AI_PROTOCOL}


# --------------------------------------------------------------------------
# HTTP layer
# --------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "ArcDossier/" + VERSION

    def log_message(self, fmt, *args):
        sys.stderr.write("%s — %s\n" % (self.log_date_time_string(), fmt % args))

    def _send(self, status, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(body)))
        self.send_header("cache-control", "no-store")
        self.send_header("x-content-type-options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, payload, status=200):
        self._send(status, json.dumps(payload).encode("utf-8"), "application/json; charset=utf-8")

    def _static(self, path):
        if path.startswith("/fonts/"):
            name = path[len("/fonts/"):]
            if FONT_FILE_RE.match(name) and ".." not in name:
                full = os.path.join(STATIC_DIR, FONT_DIR, name)
                extension = os.path.splitext(name)[1].lower()
                try:
                    with open(full, "rb") as handle:
                        body = handle.read()
                except OSError:
                    self._json({"ok": False, "error": "missing font asset"}, 404)
                    return
                self._send(200, body, FONT_MIME.get(extension, "application/octet-stream"))
                return
            self._json({"ok": False, "error": "not found"}, 404)
            return

        entry = STATIC_FILES.get(path)
        if not entry:
            self._json({"ok": False, "error": "not found"}, 404)
            return
        filename, content_type = entry
        try:
            with open(os.path.join(STATIC_DIR, filename), "rb") as handle:
                body = handle.read()
        except OSError:
            self._json({"ok": False, "error": "missing static asset: %s" % filename}, 500)
            return
        self._send(200, body, content_type)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        fresh = params.get("fresh", ["0"])[0] == "1"

        if path == "/api/health":
            self._json({
                "ok": True,
                "version": VERSION,
                "uptimeSeconds": round(time.time() - STARTED),
                "startedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(STARTED)),
                "code": code_fingerprint(),
                "keysLoaded": {
                    "minimax": bool(AI_API_KEY),
                    "rootdata": bool(ROOTDATA_API_KEY),
                },
                "dotenvEntriesLoaded": DOTENV_LOADED,
                "knowledgeBase": KNOWLEDGE.stats(),
            })
        elif path == "/api/knowledge/stats":
            self._json({"ok": True, "data": KNOWLEDGE.stats()})
        elif path == "/api/knowledge":
            query = params.get("q", [""])[0].strip()
            if not query:
                self._json({"ok": False, "error": "pass ?q="}, 400)
                return
            self._json({"ok": True, "data": KNOWLEDGE.resolve(query)})
        elif path == "/api/market":
            project_id = params.get("project_id", [""])[0].strip()
            if not project_id:
                self._json({"ok": False, "error": "pass ?project_id="}, 400)
                return
            self._json({"ok": True, "data": KNOWLEDGE.market(project_id, fresh=fresh)})
        elif path == "/api/chain":
            self._json({"ok": True, "data": chain_snapshot(fresh=fresh)})
        elif path == "/api/probe":
            target = params.get("url", [""])[0]
            if not target:
                self._json({"ok": False, "error": "pass ?url="}, 400)
                return
            result = probe_url(target, fresh=fresh)
            self._json({"ok": bool(result.get("ok")), "data": result}, 200 if result.get("ok") else 502)
        elif path == "/api/contract":
            address = params.get("address", [""])[0].strip()
            if not CONTRACT_RE.match(address):
                self._json({"ok": False, "error": "pass a 0x-prefixed 20-byte address"}, 400)
                return
            self._json({"ok": True, "data": contract_evidence(address, fresh=fresh)})
        elif path == "/api/token":
            address = params.get("address", [""])[0].strip()
            if not CONTRACT_RE.match(address):
                self._json({"ok": False, "error": "pass a 0x-prefixed 20-byte address"}, 400)
                return
            self._json({"ok": True, "data": token_metrics(address, fresh=fresh)})
        elif path == "/api/ai/status":
            admin = params.get("admin", ["0"])[0] == "1"
            self._json({"ok": True, "data": ai_status() if admin else public_ai_status()})
        elif path == "/api/report":
            self._json({"ok": False, "error": "Deep research has been removed; use /api/analyze."}, 410)
        elif path == "/api/analyze":
            query = params.get("q", [""])[0]
            if not query.strip():
                self._json({"ok": False, "error": "pass ?q="}, 400)
                return
            mode = "quick"
            plan = AI_MODES[mode]
            dossier = build_dossier(query, fresh=fresh, profile=plan["scan"])
            self._json({"ok": True, "data": analyze(dossier, fresh=fresh, mode=mode)})
        elif path == "/api/dossier":
            query = params.get("q", [""])[0]
            if not query.strip():
                self._json({"ok": False, "error": "pass ?q="}, 400)
                return
            profile = params.get("profile", ["quick"])[0]
            self._json({"ok": True, "data": build_dossier(query, fresh=fresh, profile=profile)})
        elif path.startswith("/api/"):
            self._json({"ok": False, "error": "unknown endpoint"}, 404)
        else:
            self._static(path)

    do_HEAD = do_GET

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except ValueError:
            self._json({"ok": False, "error": "invalid JSON body"}, 400)
            return
        if parsed.path == "/api/dossier":
            query = str(payload.get("query", "")).strip()
            if not query:
                self._json({"ok": False, "error": "body needs {\"query\": \"...\"}"}, 400)
                return
            # Returns the dossier itself. The narrative analysis is a separate call,
            # so a failed or slow model never blocks the deterministic evidence.
            profile = str(payload.get("profile") or "deep")
            self._json({"ok": True, "data": build_dossier(query, fresh=bool(payload.get("fresh")), profile=profile)})
        elif parsed.path == "/api/report":
            self._json({"ok": False, "error": "Deep research has been removed; use /api/analyze."}, 410)
        elif parsed.path == "/api/analyze":
            query = str(payload.get("query", "")).strip()
            if not query:
                self._json({"ok": False, "error": "body needs {\"query\": \"...\"}"}, 400)
                return
            mode = "quick"
            plan = AI_MODES[mode]
            dossier = build_dossier(query, fresh=bool(payload.get("fresh")), profile=plan["scan"])
            self._json({"ok": True, "data": analyze(dossier,
                                                    fresh=bool(payload.get("fresh")), mode=mode)})
        elif parsed.path == "/api/probe":
            target = str(payload.get("url", "")).strip()
            if not target:
                self._json({"ok": False, "error": "body needs {\"url\": \"...\"}"}, 400)
                return
            result = probe_url(target, fresh=bool(payload.get("fresh")))
            self._json({"ok": bool(result.get("ok")), "data": result}, 200 if result.get("ok") else 502)
        else:
            self._json({"ok": False, "error": "unknown endpoint"}, 404)


def _hash_sources() -> dict:
    """Hash the served sources so a running process can be proven to match disk.

    This exists because a stale server silently served old code three times during
    development: static files are read per request, but server.py is only reloaded
    on restart, so a long-running process can lag the files with no visible sign.
    """
    files, digest = {}, hashlib.sha256()
    for name in ("server.py", "knowledge_base.py", "app.js", "styles.css", "index.html"):
        path = os.path.join(STATIC_DIR, name)
        try:
            with open(path, "rb") as handle:
                blob = handle.read()
        except OSError:
            blob = b""
        files[name] = {"bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()[:16]}
        digest.update(name.encode())
        digest.update(blob)
    return {"build": digest.hexdigest()[:16], "files": files}


# Captured once, when the module is imported. Comparing a per-request re-read of
# the files against the files themselves is circular and can never detect a stale
# process — which is the only thing this is for. The first version of this feature
# did exactly that and reported "matches disk" unconditionally.
STARTUP_SOURCES = _hash_sources()


def code_fingerprint() -> dict:
    """Startup hashes next to the current on-disk hashes, plus a staleness verdict.

    Only server.py is imported once and cached, so only server.py drifting from disk
    actually needs a restart. The three static assets are re-read on every request,
    so an edit to them is already live in the browser. Both are reported, but they
    are not the same condition and the verdict says which one applies.
    """
    disk = _hash_sources()
    changed = sorted(name for name, meta in disk["files"].items()
                     if (STARTUP_SOURCES["files"].get(name) or {}).get("sha256") != meta["sha256"])
    needs_restart = any(name in changed for name in ("server.py", "knowledge_base.py"))
    static_only = [name for name in changed if name not in ("server.py", "knowledge_base.py")]
    if needs_restart:
        verdict = "server.py changed after startup — restart required to pick it up"
    elif static_only:
        verdict = ("static assets changed after startup (%s); they are served fresh on every "
                   "request, so this is already live and no restart is needed" % ", ".join(static_only))
    else:
        verdict = "the running process matches the files on disk"
    return {
        "build": STARTUP_SOURCES["build"],
        "files": STARTUP_SOURCES["files"],
        "diskBuild": disk["build"],
        "diskFiles": disk["files"],
        "stale": needs_restart,
        "staleFiles": changed,
        "restartRequired": needs_restart,
        "staticChanged": static_only,
        "verdict": verdict,
    }


STARTED = time.time()


def main():
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("usage: python3 server.py [port]", file=sys.stderr)
            return 2
    server = ThreadingHTTPServer((DEFAULT_HOST, port), Handler)
    print("ArcDossier v%s serving on %s:%d" % (VERSION, DEFAULT_HOST, port))
    for key in NETWORK_ORDER:
        print("  %-8s %s" % (NETWORKS[key]["label"], NETWORKS[key]["rpc"]))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
