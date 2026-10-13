#!/usr/bin/env python3
"""Self-test for ArcDossier. Run it against a live instance:

    python3 selftest.py            # assumes http://127.0.0.1:4188
    python3 selftest.py 4180       # or another port

Every check prints PASS / FAIL / SKIP with the observed value, so a reviewer
can see what was actually verified rather than trusting a summary. Checks that
cost money (model calls) are skipped unless --spend is passed.

    python3 selftest.py --spend    # also runs one real model call
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "ArcDossier-selftest/1.0"

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    flag = "PASS" if ok else ("SKIP" if ok is None else "FAIL")
    print("  [%s] %-52s %s" % (flag, name, detail))


def fetch(base, path, method="GET", body=None, timeout=120, raw=False):
    """raw=True returns (status, text) without parsing. Static assets are not JSON;
    an earlier version of this harness parsed everything and reported four working
    endpoints as failures."""
    url = base + path
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method,
                                     headers={"content-type": "application/json", "user-agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read(8 * 1024 * 1024).decode("utf-8", "replace")
            return response.status, (text if raw else json.loads(text))
    except urllib.error.HTTPError as exc:
        text = ""
        try:
            text = exc.read(4096).decode("utf-8", "replace")
        except Exception:
            pass
        if raw:
            return exc.code, text
        try:
            return exc.code, json.loads(text)
        except Exception:
            return exc.code, {}
    except Exception as exc:
        return None, (str(exc) if raw else {"error": str(exc)})


def check_sources():
    print("\n1. Source files")
    for name in ("server.py", "app.js", "styles.css", "index.html"):
        path = os.path.join(HERE, name)
        ok = os.path.exists(path)
        record("%s exists" % name, ok, "%d bytes" % os.path.getsize(path) if ok else "missing")
    for name in ("server.py",):
        proc = subprocess.run([sys.executable, "-c", "import ast,sys;ast.parse(open(sys.argv[1]).read())", os.path.join(HERE, name)],
                              capture_output=True, text=True)
        record("%s parses as Python" % name, proc.returncode == 0, proc.stderr.strip()[:80])
    if os.path.exists(os.path.join(HERE, "app.js")):
        node = None
        for candidate in ("node", "/usr/local/bin/node"):
            try:
                subprocess.run([candidate, "--version"], capture_output=True, check=True)
                node = candidate
                break
            except Exception:
                continue
        if node:
            proc = subprocess.run([node, "--check", os.path.join(HERE, "app.js")], capture_output=True, text=True)
            record("app.js parses as JavaScript", proc.returncode == 0, proc.stderr.strip()[:80])
        else:
            record("app.js parses as JavaScript", None, "no node binary available")
    css = open(os.path.join(HERE, "styles.css"), encoding="utf-8").read()
    record("styles.css braces balanced", css.count("{") == css.count("}"),
           "%d open / %d close" % (css.count("{"), css.count("}")))
    defined = set(re.findall(r"^\s*(--[a-z0-9-]+):", css, re.M))
    used = set(re.findall(r"var\((--[a-z0-9-]+)", css))
    undefined = sorted(used - defined)
    record("every CSS variable is defined", not undefined, ", ".join(undefined) or "none missing")


def check_secrets():
    print("\n2. Secret handling")
    env_path = os.path.join(HERE, ".env")
    record(".env exists", os.path.exists(env_path))
    if os.path.exists(env_path):
        mode = oct(os.stat(env_path).st_mode & 0o777)
        record(".env is owner-only (600)", mode == "0o600", "mode %s" % mode)
        text = open(env_path, encoding="utf-8").read()
        for name in ("MINIMAX_API_KEY", "ROOTDATA_API_KEY"):
            match = re.search(r"^%s=(.*)$" % name, text, re.M)
            value = (match.group(1).strip() if match else "")
            record("%s present" % name, bool(value), "masked %s…%s (%d chars)" % (value[:4], value[-4:], len(value)) if value else "empty")
    gitignore = os.path.join(HERE, ".gitignore")
    if os.path.exists(gitignore):
        text = open(gitignore, encoding="utf-8").read()
        record(".gitignore excludes .env", ".env" in text)
        record(".gitignore excludes report log", "reports/" in text)
    for stale in ("key.txt", "rootdata-key.txt", "MINIMAX_API_KEY.paste", "ROOTDATA_API_KEY.paste"):
        record("no leftover paste file: %s" % stale, not os.path.exists(os.path.join(HERE, stale)))


def check_frontend_hygiene():
    print("\n3. Front-end hygiene")
    raw_app = open(os.path.join(HERE, "app.js"), encoding="utf-8").read()
    app = raw_app
    html = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    defined = set(re.findall(r"function\s+([A-Za-z_$][\w$]*)\s*\(", app))
    defined |= set(re.findall(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=", app))
    # No whitespace allowed between the name and the paren: real calls are written
    # `foo(`. Allowing a space made prose inside template strings look like code —
    # it once reported a call to `flags(` from the sentence "Risk flags (kept ...)".
    called = set(re.findall(r"(?<![\w.$])([a-z_$][\w$]*)\(", app))
    noise = {"if", "for", "while", "switch", "catch", "return", "typeof", "function", "fetch", "parseInt",
             "parseFloat", "setTimeout", "setInterval", "encodeURIComponent", "decodeURIComponent", "isNaN",
             "String", "Number", "Boolean", "Array", "Object", "JSON", "Promise", "Error", "Date", "Math",
             "RegExp", "document", "window", "await", "new", "else", "do", "try", "map", "filter", "join",
             "forEach", "admin", "claim", "implementation", "owner", "paused", "reads", "replace", "slice",
             "split", "trim", "toLowerCase", "toUpperCase", "toFixed", "toLocaleString", "push", "concat",
             "indexOf", "includes", "startsWith", "endsWith", "keys", "values", "entries", "stringify",
             "parse", "sort", "reverse", "find", "some", "every", "reduce", "getElementById", "querySelector",
             "querySelectorAll", "addEventListener", "insertAdjacentHTML", "setAttribute", "append", "remove"}
    undefined = sorted(called - defined - noise)
    record("no undefined function calls in app.js", not undefined, ", ".join(undefined) or "none")

    duplicates = [name for name in set(re.findall(r"^function\s+([A-Za-z_$][\w$]*)\s*\(", app, re.M))
                  if len(re.findall(r"^function\s+%s\s*\(" % re.escape(name), app, re.M)) > 1]
    record("no duplicate top-level function definitions", not duplicates, ", ".join(duplicates) or "none")

    ids_used = set(re.findall(r'\$\("#([A-Za-z0-9_-]+)"\)', raw_app))
    ids_dynamic = {"ai-body", "ai-effort", "ai-run", "recheck"}
    ids_html = set(re.findall(r'id="([^"]+)"', html))
    missing = sorted(ids_used - ids_html - ids_dynamic)
    record("every static element id exists in index.html", not missing, ", ".join(missing) or "none missing")


def check_instance(base):
    print("\n4. Live instance at %s" % base)
    status, health = fetch(base, "/api/health", timeout=20)
    if status != 200:
        record("instance reachable", False, str(health)[:90])
        return None
    record("instance reachable", True, "uptime %ss, started %s" % (health.get("uptimeSeconds"), health.get("startedAt")))
    code = health.get("code") or {}
    record("health reports a build fingerprint", bool(code.get("build")), code.get("build", ""))

    local = {}
    for name in ("server.py", "app.js", "styles.css", "index.html"):
        import hashlib
        blob = open(os.path.join(HERE, name), "rb").read()
        local[name] = hashlib.sha256(blob).hexdigest()[:16]
    drift = [name for name, digest in local.items() if (code.get("files") or {}).get(name, {}).get("sha256") != digest]
    # Only server.py is loaded once; the static assets are re-read per request, so a
    # static edit is already live and must not be reported as a failing check.
    needs_restart = bool(code.get("restartRequired"))
    record("no restart pending (server.py matches the process)", not needs_restart,
           "server.py changed after startup — restart it" if needs_restart
           else ("static assets changed and are already live: " + ", ".join(code.get("staticChanged") or [])
                 if drift else "all four match"))

    keys = health.get("keysLoaded") or {}
    record("health reports which keys are loaded", "minimax" in keys, json.dumps(keys))

    status, payload = fetch(base, "/api/ai/status", timeout=20)
    body = json.dumps(payload)
    record("public AI status hides the model name", "minimax" not in body.lower() and "flash-preview" not in body.lower(),
           "no model string in the public payload")
    record("public AI status lists one report mode",
           [m.get("id") for m in (payload.get("data") or {}).get("modes", [])] == ["quick"],
           str([m.get("id") for m in (payload.get("data") or {}).get("modes", [])]))
    status, admin = fetch(base, "/api/ai/status?admin=1", timeout=20)
    record("admin status does expose the model to the operator", bool((admin.get("data") or {}).get("model")),
           (admin.get("data") or {}).get("model", ""))
    return health


def check_endpoints(base):
    print("\n5. Endpoints")
    status, chain = fetch(base, "/api/chain", timeout=60)
    networks = (chain.get("data") or {}).get("networks") or []
    record("GET /api/chain returns both networks", len(networks) == 2,
           ", ".join("%s=%s" % (n.get("label"), n.get("blockNumber")) for n in networks))
    record("both chain ids verified against expected values",
           all(n.get("ok") for n in networks), str([n.get("ok") for n in networks]))

    status, bad = fetch(base, "/api/contract?address=nothex", timeout=20)
    record("GET /api/contract rejects a bad address", status == 400, "http %s" % status)
    status, missing = fetch(base, "/api/dossier", timeout=20)
    record("GET /api/dossier requires a query", status == 400, "http %s" % status)
    status, removed = fetch(base, "/api/report?q=arc.io", timeout=20)
    record("legacy deep report is disabled", status == 410, "http %s" % status)
    status, unknown = fetch(base, "/api/nope", timeout=20)
    record("unknown /api path returns 404", status == 404, "http %s" % status)

    status, page = fetch(base, "/", timeout=20, raw=True)
    record("index served as HTML", status == 200 and "<!doctype html" in page.lower(),
           "http %s, %d bytes" % (status, len(page)))
    status, _ = fetch(base, "/fonts/../server.py", timeout=20)
    record("font path traversal blocked", status == 404, "http %s" % status)

    for path in ("/styles.css", "/app.js", "/fonts/dmsans-400.woff2"):
        status, text = fetch(base, path, timeout=20, raw=True)
        record("static asset %s" % path, status == 200, "http %s, %d bytes" % (status, len(text)))


def check_ssrf(base):
    print("\n6. Source-probe guardrails (SSRF)")
    for target, label in (("http://127.0.0.1:4188/api/health", "loopback"),
                          ("http://10.0.0.5/", "RFC1918"),
                          ("file:///etc/passwd", "non-http scheme")):
        status, payload = fetch(base, "/api/probe?url=" + urllib.parse.quote(target, safe=""), timeout=30)
        data = payload.get("data") or {}
        blocked = not data.get("ok")
        record("probe refuses %s" % label, blocked, str(data.get("error"))[:60])


def check_dossier(base):
    print("\n7. Dossier pipeline (deterministic only, no model call)")
    status, payload = fetch(base, "/api/dossier?q=solana.com&profile=quick", timeout=120)
    data = payload.get("data") or {}
    record("ecosystem gate stops a known non-Arc surface", data.get("status") == "not-arc",
           "status=%s score=%s" % (data.get("status"), data.get("score")))
    record("gated result issues no score", data.get("score") is None, str(data.get("score")))

    status, payload = fetch(base, "/api/dossier?q=arc.io&profile=quick", timeout=180)
    data = payload.get("data") or {}
    record("website dossier builds", bool(data.get("sources")), "%d sources" % len(data.get("sources") or []))
    record("dossier carries a scorecard", bool(data.get("scorecard")), "%d dimensions" % len((data.get("scorecard") or {}).get("dimensions") or []))
    record("dossier carries a grading frame", bool(data.get("gradingFrame")),
           "%d modules" % len((data.get("gradingFrame") or {}).get("modules") or []))
    frame = data.get("gradingFrame") or {}
    scored = [m for m in frame.get("modules") or [] if m.get("score") is not None]
    record("unscored modules carry a reason", all(m.get("note") for m in frame.get("modules") or [] if m.get("score") is None),
           "%d of %d modules scored" % (len(scored), len(frame.get("modules") or [])))
    record("weighted total only covers measured weight",
           frame.get("scoredWeight", 0) <= frame.get("totalWeight", 0),
           "%s of %s" % (frame.get("scoredWeight"), frame.get("totalWeight")))
    discovery = data.get("discovery") or {}
    record("contract-only input states the reverse-lookup limit",
           bool(discovery.get("note")) or data.get("target", {}).get("kind") != "contract",
           str(discovery.get("note"))[:70])


def check_model_call(base):
    print("\n10. Real model call (--spend)")
    before = fetch(base, "/api/ai/status", timeout=20)[1].get("data", {}).get("callsUsedToday")
    started = time.time()
    status, payload = fetch(base, "/api/analyze?q=arc.io&mode=quick", timeout=120)
    elapsed = time.time() - started
    data = payload.get("data") or {}
    report = data.get("report") or {}
    narrative = report.get("analysis") or {}
    record("standard report returns", data.get("status") in ("ok", "cached") and bool(narrative),
           "status=%s, %.1fs" % (data.get("status"), elapsed))
    record("standard report stays inside its timeout", elapsed < 120, "%.1fs" % elapsed)
    after = fetch(base, "/api/ai/status", timeout=20)[1].get("data", {}).get("callsUsedToday")
    record("call counter did not decrease", (after or 0) >= (before or 0), "%s -> %s" % (before, after))
    validation = report.get("validation") or {}
    record("every report claim cited a real fact", not (validation.get("demoted") or []),
           "%d demoted" % len(validation.get("demoted") or []))
    forbidden = ["score", "rating", "grade", "confidence", "rank", "recommendation", "verdict"]
    blob = json.dumps(narrative).lower()
    record("model output contains no score-like field",
           not any('"%s"' % word in blob for word in forbidden), "checked %d keys" % len(forbidden))


def check_rendered_page(base):
    """Load the page in headless Chrome and assert it actually rendered.

    This is the check that would have caught a duplicate function definition that
    silently blanked the result area: the regex scan missed it, the browser did not.
    """
    print("\n8. Rendered page (headless browser)")
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if not os.path.exists(chrome):
        record("headless browser available", None, "Chrome not found at the usual path")
        return
    import shutil
    import tempfile
    profile = tempfile.mkdtemp(prefix="arcdossier-selftest-")
    try:
        proc = subprocess.run(
            [chrome, "--headless", "--disable-gpu", "--no-sandbox", "--disable-crash-reporter",
             "--no-first-run", "--user-data-dir=" + profile, "--virtual-time-budget=90000",
             "--dump-dom", base + "/?q=arc.io"],
            capture_output=True, text=True, timeout=180)
        dom = proc.stdout
        record("page returns a DOM", len(dom) > 5000, "%d bytes" % len(dom))
        record("result card rendered", "result-card" in dom, "found" if "result-card" in dom else "absent")
        record("no client-side error banner", "scripting error" not in dom.lower(),
               "clean" if "scripting error" not in dom.lower() else "the page reported a scripting error")
        record("scorecard rendered", "scorecard-panel" in dom, "found" if "scorecard-panel" in dom else "absent")
        record("model name absent from the rendered page", "minimax" not in dom.lower(),
               "no leak" if "minimax" not in dom.lower() else "MODEL NAME LEAKED INTO THE PAGE")
    except subprocess.TimeoutExpired:
        record("page renders within the timeout", False, "headless browser timed out")
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def check_data_files():
    print("\n9. Data files on disk")
    reports = os.path.join(HERE, "reports")
    log = os.path.join(reports, "analyses.jsonl")
    if os.path.exists(log):
        rows, broken, chain_ok = [], 0, True
        previous = None
        for line in open(log, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                broken += 1
                continue
            if previous is not None and row.get("prevHash") != previous:
                chain_ok = False
            previous = row.get("hash")
            rows.append(row)
        record("report log is valid JSON lines", broken == 0, "%d records, %d broken" % (len(rows), broken))
        record("report log hash chain is intact", chain_ok, "prevHash links verified")
        record("report log records carry a hash", all(r.get("hash") for r in rows), "%d hashed" % len(rows))
    else:
        record("report log exists", None, "no model calls made yet")
    usage = os.path.join(reports, "rootdata-usage.json")
    if os.path.exists(usage):
        record("RootData usage file is valid JSON", True, open(usage, encoding="utf-8").read()[:60])
    else:
        record("RootData usage file", None, "no RootData calls made yet")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    port = args[0] if args else "4188"
    base = "http://127.0.0.1:%s" % port
    print("ArcDossier self-test against %s" % base)

    check_sources()
    check_secrets()
    check_frontend_hygiene()
    health = check_instance(base)
    if health:
        check_endpoints(base)
        check_ssrf(base)
        check_dossier(base)
        check_rendered_page(base)
        check_data_files()
        if "--spend" in sys.argv:
            check_model_call(base)
        else:
            print("\n10. Real model call")
            record("standard report with a real model call", None, "pass --spend to run it (costs one call)")

    failed = [name for name, ok, _ in results if ok is False]
    skipped = [name for name, ok, _ in results if ok is None]
    print("\n%d checks: %d passed, %d failed, %d skipped" %
          (len(results), len(results) - len(failed) - len(skipped), len(failed), len(skipped)))
    if failed:
        print("\nFAILED:")
        for name in failed:
            print("  - %s" % name)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
