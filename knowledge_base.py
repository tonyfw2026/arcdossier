#!/usr/bin/env python3
"""Persistent ArcDossier project identities, research, and market snapshots."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import urllib.parse
import urllib.request


CHAIN_ID = 5042
CONTRACT_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
MARKET_TTL = int(os.environ.get("ARC_MARKET_CACHE_TTL", "300"))
USER_AGENT = "ArcDossier/0.5 (+https://arcdossier.site)"


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS projects (
  project_id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  name TEXT NOT NULL,
  category TEXT,
  website TEXT,
  x_handle TEXT,
  summary_zh TEXT,
  summary_en TEXT,
  rpc_verified INTEGER NOT NULL DEFAULT 0,
  rpc_status TEXT,
  research_date TEXT,
  raw_json TEXT NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS tokens (
  token_id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  chain_id INTEGER NOT NULL,
  contract_address TEXT NOT NULL,
  symbol TEXT,
  address_status TEXT,
  UNIQUE(chain_id, contract_address)
);

CREATE TABLE IF NOT EXISTS pools (
  pair_address TEXT PRIMARY KEY,
  token_id INTEGER NOT NULL REFERENCES tokens(token_id),
  source_url TEXT,
  dex_id TEXT,
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS identity_aliases (
  alias_type TEXT NOT NULL,
  normalized_value TEXT NOT NULL,
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  verified INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY(alias_type, normalized_value, project_id)
);

CREATE INDEX IF NOT EXISTS identity_alias_lookup
  ON identity_aliases(alias_type, normalized_value);

CREATE TABLE IF NOT EXISTS research_reports (
  report_id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  version TEXT NOT NULL,
  researched_on TEXT,
  content_json TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  UNIQUE(project_id, version)
);

CREATE TABLE IF NOT EXISTS research_sources (
  source_id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  url TEXT NOT NULL,
  source_class TEXT,
  access_note TEXT,
  UNIQUE(project_id, url)
);

CREATE TABLE IF NOT EXISTS market_snapshots (
  snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
  token_id INTEGER NOT NULL REFERENCES tokens(token_id),
  fetched_at INTEGER NOT NULL,
  source TEXT NOT NULL,
  status TEXT NOT NULL,
  data_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS market_latest
  ON market_snapshots(token_id, fetched_at DESC);

CREATE TABLE IF NOT EXISTS import_runs (
  package_version TEXT PRIMARY KEY,
  imported_at INTEGER NOT NULL,
  project_count INTEGER NOT NULL,
  token_count INTEGER NOT NULL,
  source_count INTEGER NOT NULL
);
"""


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_name(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", value)
    return " ".join(value.split())


def normalize_handle(value):
    value = str(value or "").strip()
    if not value:
        return ""
    if "://" in value:
        parsed = urllib.parse.urlparse(value)
        if (parsed.hostname or "").lower() not in ("x.com", "www.x.com", "twitter.com", "www.twitter.com"):
            return ""
        value = parsed.path.strip("/").split("/")[0]
    return value.lstrip("@").strip().lower()


def normalize_host(value):
    value = str(value or "").strip()
    if not value:
        return ""
    candidate = value if "://" in value else "https://" + value
    try:
        host = (urllib.parse.urlparse(candidate).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def query_type(value):
    value = str(value or "").strip()
    if CONTRACT_RE.match(value):
        return "contract", value.lower()
    if value.startswith("@"):
        return "x", normalize_handle(value)
    host = normalize_host(value)
    if host in ("x.com", "twitter.com"):
        return "x", normalize_handle(value)
    if "://" in value or ("." in value and " " not in value):
        return "website", host
    return "name", normalize_name(value)


def _request_json(url, timeout=12):
    request = urllib.request.Request(url, headers={"user-agent": USER_AGENT, "accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read(4 * 1024 * 1024).decode("utf-8", "replace"))


def _number(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _dexscreener_market(address):
    url = "https://api.dexscreener.com/token-pairs/v1/arc/" + urllib.parse.quote(address)
    payload = _request_json(url)
    if not isinstance(payload, list):
        return None
    address_lower = address.lower()
    pairs = [item for item in payload if str((item.get("baseToken") or {}).get("address") or "").lower() == address_lower]
    if not pairs:
        return None
    pairs.sort(key=lambda item: _number((item.get("liquidity") or {}).get("usd")) or 0, reverse=True)
    primary = pairs[0]
    transactions = primary.get("txns") or {}
    h24_txns = transactions.get("h24") or {}
    result = {
        "priceUsd": _number(primary.get("priceUsd")),
        "marketCapUsd": _number(primary.get("marketCap")),
        "fdvUsd": _number(primary.get("fdv")),
        "volume24hUsd": _number((primary.get("volume") or {}).get("h24")),
        "liquidityUsd": _number((primary.get("liquidity") or {}).get("usd")),
        "txns24h": int(h24_txns.get("buys") or 0) + int(h24_txns.get("sells") or 0),
        "priceChange1hPct": _number((primary.get("priceChange") or {}).get("h1")),
        "priceChange6hPct": _number((primary.get("priceChange") or {}).get("h6")),
        "priceChange24hPct": _number((primary.get("priceChange") or {}).get("h24")),
        "pairAddress": primary.get("pairAddress"),
        "pairUrl": primary.get("url"),
        "dexId": primary.get("dexId"),
        "holders": None,
        "dataSource": "DexScreener",
        "sourceUrl": url,
        "updatedAt": _now_iso(),
        "pairs": [
            {
                "pairAddress": item.get("pairAddress"),
                "dexId": item.get("dexId"),
                "liquidityUsd": _number((item.get("liquidity") or {}).get("usd")),
                "volume24hUsd": _number((item.get("volume") or {}).get("h24")),
                "url": item.get("url"),
            }
            for item in pairs[:5]
        ],
    }
    return result if any(result.get(key) is not None for key in ("priceUsd", "volume24hUsd", "liquidityUsd")) else None


def _geckoterminal_market(address):
    url = "https://api.geckoterminal.com/api/v2/networks/arc/tokens/%s/pools?page=1" % urllib.parse.quote(address)
    payload = _request_json(url)
    pools = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(pools, list) or not pools:
        return None
    pools.sort(key=lambda item: _number((item.get("attributes") or {}).get("reserve_in_usd")) or 0, reverse=True)
    attrs = pools[0].get("attributes") or {}
    transactions = (attrs.get("transactions") or {}).get("h24") or {}
    pair = attrs.get("address")
    result = {
        "priceUsd": _number(attrs.get("token_price_usd") or attrs.get("base_token_price_usd")),
        "marketCapUsd": _number(attrs.get("market_cap_usd")),
        "fdvUsd": _number(attrs.get("fdv_usd")),
        "volume24hUsd": _number((attrs.get("volume_usd") or {}).get("h24")),
        "liquidityUsd": _number(attrs.get("reserve_in_usd")),
        "txns24h": int(transactions.get("buys") or 0) + int(transactions.get("sells") or 0),
        "priceChange1hPct": _number((attrs.get("price_change_percentage") or {}).get("h1")),
        "priceChange6hPct": _number((attrs.get("price_change_percentage") or {}).get("h6")),
        "priceChange24hPct": _number((attrs.get("price_change_percentage") or {}).get("h24")),
        "pairAddress": pair,
        "pairUrl": "https://www.geckoterminal.com/arc/pools/%s" % pair if pair else None,
        "dexId": None,
        "holders": None,
        "dataSource": "GeckoTerminal",
        "sourceUrl": url,
        "updatedAt": _now_iso(),
        "pairs": [
            {
                "pairAddress": (item.get("attributes") or {}).get("address"),
                "dexId": None,
                "liquidityUsd": _number((item.get("attributes") or {}).get("reserve_in_usd")),
                "volume24hUsd": _number(((item.get("attributes") or {}).get("volume_usd") or {}).get("h24")),
                "url": "https://www.geckoterminal.com/arc/pools/%s" % ((item.get("attributes") or {}).get("address") or ""),
            }
            for item in pools[:5]
        ],
    }
    return result if any(result.get(key) is not None for key in ("priceUsd", "volume24hUsd", "liquidityUsd")) else None


def fetch_market_data(address):
    errors = []
    for source in (_dexscreener_market, _geckoterminal_market):
        try:
            result = source(address)
            if result:
                return result, errors
        except Exception as exc:
            errors.append("%s: %s" % (source.__name__.replace("_market", "").lstrip("_"), str(exc)[:160]))
    return None, errors


class KnowledgeBase:
    def __init__(self, path, package_dir=None):
        self.path = path
        self.package_dir = package_dir
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with self.connect() as db:
            db.executescript(SCHEMA)
        if package_dir and self.stats()["projects"] == 0:
            self.import_package(package_dir)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def import_package(self, package_dir):
        projects_doc = _read_json(os.path.join(package_dir, "arc_projects.json"))
        sources_doc = _read_json(os.path.join(package_dir, "arc_project_sources.json"))
        market_doc = _read_json(os.path.join(package_dir, "arc_market_snapshot.json"))
        version = str(projects_doc.get("schema_version") or "unknown")
        source_map = {item.get("project_id"): item for item in sources_doc.get("projects") or []}
        market_map = {item.get("project_id"): item for item in market_doc.get("market_snapshots") or []}
        now = int(time.time())
        with self.connect() as db:
            for project in projects_doc.get("projects") or []:
                project_id = str(project.get("project_id") or "").strip()
                if not project_id:
                    continue
                website = project.get("official_website") or project.get("website")
                db.execute("""
                    INSERT INTO projects(project_id, entity_type, name, category, website, x_handle,
                      summary_zh, summary_en, rpc_verified, rpc_status, research_date, raw_json, updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(project_id) DO UPDATE SET
                      entity_type=excluded.entity_type, name=excluded.name, category=excluded.category,
                      website=excluded.website, x_handle=excluded.x_handle, summary_zh=excluded.summary_zh,
                      summary_en=excluded.summary_en, rpc_verified=excluded.rpc_verified,
                      rpc_status=excluded.rpc_status, research_date=excluded.research_date,
                      raw_json=excluded.raw_json, updated_at=excluded.updated_at
                """, (
                    project_id, project.get("entity_type") or "token_project", project.get("name") or project_id,
                    project.get("category"), website, project.get("x_handle"), project.get("summary_zh"),
                    project.get("summary_en"), 1 if project.get("rpc_verified") else 0,
                    project.get("rpc_status"), project.get("last_researched_on"),
                    json.dumps(project, ensure_ascii=False), now,
                ))
                address = project.get("contract_address")
                if address and CONTRACT_RE.match(address):
                    db.execute("""
                        INSERT INTO tokens(project_id, chain_id, contract_address, symbol, address_status)
                        VALUES(?,?,?,?,?)
                        ON CONFLICT(chain_id, contract_address) DO UPDATE SET
                          project_id=excluded.project_id, symbol=excluded.symbol, address_status=excluded.address_status
                    """, (project_id, int(project.get("chain_id") or CHAIN_ID), address.lower(),
                          project.get("symbol"), project.get("contract_address_status")))
                verified_identity = 1 if project_id == "arc-network" else 0
                aliases = [("name", normalize_name(project.get("name"))), ("symbol", normalize_name(project.get("symbol"))),
                           ("website", normalize_host(website)), ("x", normalize_handle(project.get("x_handle")))]
                for alias_type, value in aliases:
                    if value:
                        db.execute("INSERT OR IGNORE INTO identity_aliases VALUES(?,?,?,?)",
                                   (alias_type, value, project_id, verified_identity))
                for part in re.split(r"\s*/\s*|\s+·\s+", str(project.get("name") or "")):
                    value = normalize_name(part)
                    if value:
                        db.execute("INSERT OR IGNORE INTO identity_aliases VALUES(?,?,?,?)",
                                   ("name", value, project_id, verified_identity))
                db.execute("""
                    INSERT OR IGNORE INTO research_reports(project_id, version, researched_on, content_json, created_at)
                    VALUES(?,?,?,?,?)
                """, (project_id, version, project.get("last_researched_on"),
                      json.dumps(project, ensure_ascii=False), now))
                source_entry = source_map.get(project_id) or {}
                detailed_sources = source_entry.get("sources") or []
                if not detailed_sources:
                    detailed_sources = [{"url": url} for url in project.get("sources") or []]
                for source in detailed_sources:
                    url = source.get("url") if isinstance(source, dict) else str(source)
                    if url:
                        db.execute("""
                            INSERT OR IGNORE INTO research_sources(project_id, url, source_class, access_note)
                            VALUES(?,?,?,?)
                        """, (project_id, url, source.get("source_class") if isinstance(source, dict) else None,
                              source.get("access_note") if isinstance(source, dict) else None))
                market = market_map.get(project_id) or {}
                venue = market.get("trading_venue_url")
                if venue and address:
                    pair_address = urllib.parse.urlparse(venue).path.rstrip("/").split("/")[-1].lower()
                    token = db.execute("SELECT token_id FROM tokens WHERE chain_id=? AND contract_address=?",
                                       (CHAIN_ID, address.lower())).fetchone()
                    if token and pair_address:
                        db.execute("""
                            INSERT OR IGNORE INTO pools(pair_address, token_id, source_url, dex_id, updated_at)
                            VALUES(?,?,?,?,?)
                        """, (pair_address, token["token_id"], venue, None, now))
            counts = {
                "projects": db.execute("SELECT COUNT(*) FROM projects").fetchone()[0],
                "tokens": db.execute("SELECT COUNT(*) FROM tokens").fetchone()[0],
                "sources": db.execute("SELECT COUNT(*) FROM research_sources").fetchone()[0],
            }
            db.execute("""
                INSERT INTO import_runs(package_version, imported_at, project_count, token_count, source_count)
                VALUES(?,?,?,?,?) ON CONFLICT(package_version) DO UPDATE SET
                  imported_at=excluded.imported_at, project_count=excluded.project_count,
                  token_count=excluded.token_count, source_count=excluded.source_count
            """, (version, now, counts["projects"], counts["tokens"], counts["sources"]))
        return dict(counts, version=version)

    def stats(self):
        with self.connect() as db:
            return {
                "projects": db.execute("SELECT COUNT(*) FROM projects").fetchone()[0],
                "tokens": db.execute("SELECT COUNT(*) FROM tokens").fetchone()[0],
                "pools": db.execute("SELECT COUNT(*) FROM pools").fetchone()[0],
                "aliases": db.execute("SELECT COUNT(*) FROM identity_aliases").fetchone()[0],
                "reports": db.execute("SELECT COUNT(*) FROM research_reports").fetchone()[0],
                "sources": db.execute("SELECT COUNT(*) FROM research_sources").fetchone()[0],
                "marketSnapshots": db.execute("SELECT COUNT(*) FROM market_snapshots").fetchone()[0],
            }

    def _summary(self, row):
        raw = json.loads(row["raw_json"])
        return {
            "projectId": row["project_id"], "name": row["name"], "symbol": raw.get("symbol"),
            "category": row["category"], "website": row["website"], "xHandle": row["x_handle"],
            "contractAddress": raw.get("contract_address"), "chainId": raw.get("chain_id"),
        }

    def _profile(self, db, project_id):
        row = db.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()
        if not row:
            return None
        raw = json.loads(row["raw_json"])
        tokens = [dict(item) for item in db.execute(
            "SELECT token_id,chain_id,contract_address,symbol,address_status FROM tokens WHERE project_id=? ORDER BY token_id",
            (project_id,)).fetchall()]
        pools = [dict(item) for item in db.execute("""
            SELECT p.pair_address,p.source_url,p.dex_id,t.contract_address
            FROM pools p JOIN tokens t ON t.token_id=p.token_id WHERE t.project_id=? ORDER BY p.pair_address
        """, (project_id,)).fetchall()]
        sources = [dict(item) for item in db.execute("""
            SELECT url,source_class,access_note FROM research_sources WHERE project_id=? ORDER BY source_id
        """, (project_id,)).fetchall()]
        return {
            "projectId": project_id,
            "entityType": row["entity_type"],
            "name": row["name"],
            "symbol": raw.get("symbol"),
            "category": row["category"],
            "website": row["website"],
            "xHandle": row["x_handle"],
            "summaryZh": row["summary_zh"],
            "summaryEn": row["summary_en"],
            "rpcVerified": bool(row["rpc_verified"]),
            "rpcStatus": row["rpc_status"],
            "researchDate": row["research_date"],
            "modules": raw.get("seven_modules") or {},
            "risks": raw.get("risks") or [],
            "unknownFields": raw.get("missing_or_unknown_fields") or [],
            "tokens": tokens,
            "pools": pools,
            "sources": sources,
        }

    def resolve(self, query):
        started = time.time()
        kind, normalized = query_type(query)
        if not normalized:
            return {"match": None, "candidates": [], "queryType": kind, "latencyMs": 0}
        with self.connect() as db:
            if kind == "contract":
                rows = db.execute("""
                    SELECT p.* FROM projects p JOIN tokens t ON t.project_id=p.project_id
                    WHERE t.chain_id=? AND t.contract_address=?
                """, (CHAIN_ID, normalized)).fetchall()
            else:
                alias_types = [kind] if kind in ("website", "x") else ["name", "symbol"]
                marks = ",".join("?" for _ in alias_types)
                rows = db.execute("""
                    SELECT DISTINCT p.* FROM projects p JOIN identity_aliases a ON a.project_id=p.project_id
                    WHERE a.alias_type IN (%s) AND a.normalized_value=? ORDER BY p.name
                """ % marks, tuple(alias_types) + (normalized,)).fetchall()
            candidates = [self._summary(row) for row in rows]
            match = self._profile(db, rows[0]["project_id"]) if len(rows) == 1 else None
        return {
            "match": match,
            "candidates": candidates,
            "queryType": kind,
            "normalizedQuery": normalized,
            "latencyMs": int((time.time() - started) * 1000),
        }

    def market(self, project_id, fresh=False, fetcher=fetch_market_data):
        with self.connect() as db:
            tokens = db.execute("SELECT * FROM tokens WHERE project_id=? ORDER BY token_id", (project_id,)).fetchall()
            if not tokens:
                return {"status": "unavailable", "tokens": [], "message": "No tradable token is recorded for this project."}
            output = []
            for token in tokens:
                latest = db.execute("""
                    SELECT * FROM market_snapshots WHERE token_id=? ORDER BY fetched_at DESC LIMIT 1
                """, (token["token_id"],)).fetchone()
                age = int(time.time()) - int(latest["fetched_at"]) if latest else None
                if latest and not fresh and age <= MARKET_TTL:
                    data = json.loads(latest["data_json"])
                    data.update({"status": "cached", "ageSeconds": age, "symbol": token["symbol"],
                                 "contractAddress": token["contract_address"]})
                    output.append(data)
                    continue
                data, errors = fetcher(token["contract_address"])
                if data:
                    fetched_at = int(time.time())
                    db.execute("""
                        INSERT INTO market_snapshots(token_id,fetched_at,source,status,data_json) VALUES(?,?,?,?,?)
                    """, (token["token_id"], fetched_at, data.get("dataSource") or "market_api", "live",
                          json.dumps(data, ensure_ascii=False)))
                    for pair in data.get("pairs") or []:
                        pair_address = str(pair.get("pairAddress") or "").lower()
                        if pair_address:
                            db.execute("""
                                INSERT INTO pools(pair_address,token_id,source_url,dex_id,updated_at) VALUES(?,?,?,?,?)
                                ON CONFLICT(pair_address) DO UPDATE SET source_url=excluded.source_url,
                                  dex_id=excluded.dex_id,updated_at=excluded.updated_at
                            """, (pair_address, token["token_id"], pair.get("url"), pair.get("dexId"), fetched_at))
                    data.update({"status": "live", "ageSeconds": 0, "symbol": token["symbol"],
                                 "contractAddress": token["contract_address"]})
                    output.append(data)
                elif latest:
                    data = json.loads(latest["data_json"])
                    data.update({"status": "stale", "ageSeconds": age, "symbol": token["symbol"],
                                 "contractAddress": token["contract_address"], "refreshErrors": errors})
                    output.append(data)
                else:
                    output.append({"status": "unavailable", "symbol": token["symbol"],
                                   "contractAddress": token["contract_address"], "refreshErrors": errors})
            db.commit()
        statuses = [item.get("status") for item in output]
        overall = "live" if "live" in statuses else ("cached" if "cached" in statuses else ("stale" if "stale" in statuses else "unavailable"))
        return {"status": overall, "tokens": output, "cacheTtlSeconds": MARKET_TTL}
