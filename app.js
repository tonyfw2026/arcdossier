/* ArcDossier v0.5 — front-end.
   Results combine saved, source-linked Arc research with live Arc RPC reads,
   market APIs, and server-side source probes. */

const ACTIVITY_KEY = "arcdossier.activity.v3";
const AI_EFFORTS = ["low", "medium", "high", "xhigh", "max"];
// Counts start from a preview baseline so the session panel is not an empty row of
// zeros. The disclosure under the heading states this plainly.
const BASE_SCREEN_COUNT = 100;
const CHAIN_REFRESH_MS = 20000;

const VIEW_TITLES = {
  dashboard: "Arc projects, scored on evidence.",
  search: "Screen an Arc project.",
  roadmap: "Where ArcDossier goes next.",
};

const STATE_TEXT = {
  proven: "proven",
  fetched: "fetched",
  gap: "gap",
  failed: "failed",
};

const RECEIPT_FIELDS = [
  ["url", "Requested URL"],
  ["finalUrl", "Final URL"],
  ["httpStatus", "HTTP status"],
  ["contentType", "Content type"],
  ["bytes", "Bytes read"],
  ["truncated", "Truncated"],
  ["title", "Page title"],
  ["description", "Page description"],
  ["ecosystemMentions", "Arc references"],
  ["bodySha256", "Body SHA-256"],
  ["fetchedAt", "Fetched at"],
  ["elapsedMs", "Elapsed ms"],
  ["deployed", "Deployed"],
  ["bytecodeBytes", "Bytecode bytes"],
  ["checkedAtBlock", "Read at block"],
  ["bytecodeHash", "Bytecode SHA-256"],
  ["latencyMs", "RPC latency ms"],
  ["error", "Error"],
];

const state = {
  activity: loadActivity(),
  chains: null,
  serverOk: null,
  aiStatus: null,
  lastQuery: "",
  busy: false,
};

const $ = (selector) => document.querySelector(selector);

/* ------------------------------------------------------------- helpers -- */

function escapeHtml(value = "") {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[character]));
}

function readerText(value = "") {
  return String(value)
    // Citation markers are provenance, not prose: the reader does not need
    // [fact-7] or ["fact-3", "fact-12"] in a sentence. Handles both the bare and
    // the quoted-list form, since the model emits either.
    .replace(/\[\s*"?fact-\d+"?(?:\s*,\s*"?fact-\d+"?)*\s*\]/gi, "")
    .replace(/\s*[（(][^（）()]*[）)]/g, "")
    .replace(/\bRootData\s*(?:tags?)?\s*:?/gi, "")
    .replace(/\bDefiLlama\s*:?/gi, "")
    .replace(/owner(?:\(\))?\s+returns\s+(0x[a-f0-9]+)/gi, "An administrator address is set: $1")
    .replace(/\bowner role\b/gi, "administrator access")
    .replace(/\bbytecode\b/gi, "live contract code")
    .replace(/\bscanned window\b/gi, "recent period checked")
    .replace(/\bevidence packet\b/gi, "available data")
    .replace(/\bon-chain\b/gi, "blockchain")
    .replace(/\bProduct and innovation\b/gi, "Product")
    .replace(/\bData and growth\b/gi, "Usage and growth")
    .replace(/\bFunding and backers\b/gi, "Funding")
    .replace(/\bToken economics and valuation\b/gi, "Token and valuation")
    .replace(/\bEcosystem position and narrative\b/gi, "Place in the Arc ecosystem")
    .replace(/\bAttention and catalysts\b/gi, "Market attention and upcoming events")
    .replace(/\bTiming and catalysts\b/gi, "Timing and upcoming events")
    .replace(/\bNo minting in window\b/gi, "No new token creation observed")
    .replace(/No transfer originated from the zero address in the recent period checked/gi, "No new token creation was recorded in the recent period checked")
    .replace(/This does not prove the supply cannot be minted/gi, "This does not prove that more tokens can never be created")
    .replace(/owner-restricted power/gi, "administrator-only control")
    .replace(/Window-based activity from a bounded log scan\. This is not a holder snapshot and not a full history\./gi, "Activity covers only the recent period checked. It is not a full list of token holders or a full history.")
    .replace(/\s+([.,;:!?])/g, "$1")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function fmtInt(value) {
  return typeof value === "number" && Number.isFinite(value) ? value.toLocaleString("en-US") : "—";
}

function fmtValue(key, value) {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "none found";
  if (typeof value === "boolean") return value ? "yes" : "no";
  return String(value);
}

function formatUsd(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "—";
  if (Math.abs(value) < 0.01) return "$" + value.toLocaleString("en-US", { maximumSignificantDigits: 5 });
  return "$" + value.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

function formatPercent(value) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) + "%" : "—";
}

function safeHttpUrl(value) {
  try {
    const parsed = new URL(String(value || ""));
    return parsed.protocol === "http:" || parsed.protocol === "https:" ? parsed.href : "";
  } catch {
    return "";
  }
}

function loadActivity() {
  const fallback = { searches: 0, probes: 0, proofs: 0, stopped: 0, recent: [] };
  try {
    const saved = JSON.parse(localStorage.getItem(ACTIVITY_KEY));
    return saved && typeof saved === "object" ? { ...fallback, ...saved } : fallback;
  } catch {
    return fallback;
  }
}

function saveActivity() {
  try {
    localStorage.setItem(ACTIVITY_KEY, JSON.stringify(state.activity));
  } catch {
    /* storage disabled: the session simply does not persist */
  }
}

async function api(path, options) {
  const response = await fetch(path, options);
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch {
    throw new Error("the ArcDossier service returned non-JSON (HTTP " + response.status + ")");
  }
}

/* --------------------------------------------------------------- views -- */

function showView(name) {
  document.querySelectorAll("[data-view]").forEach((view) => {
    view.classList.toggle("is-active", view.dataset.view === name);
  });
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.viewLink === name);
  });
  $("#page-title").textContent = VIEW_TITLES[name] || "ArcDossier";
  if (name === "search") window.setTimeout(() => $("#project-query").focus(), 80);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.setTimeout(() => toast.classList.remove("is-visible"), 2600);
}

function setSearchStatus(message, kind) {
  const box = $("#search-status");
  if (!message) {
    box.hidden = true;
    box.textContent = "";
    return;
  }
  box.hidden = false;
  box.textContent = message;
  box.className = "search-status" + (kind ? " is-" + kind : "");
}

/* ------------------------------------------------- live chain readout -- */

function renderChains(snapshot) {
  const container = $("#chain-rows");
  container.innerHTML = "";
  snapshot.networks.forEach((network) => {
    const ok = Boolean(network.ok);
    const row = document.createElement("div");
    row.className = "chain-row" + (ok ? "" : " is-down");
    row.innerHTML = `
      <div class="chain-row-top">
        <span class="source-state ${ok ? "proven" : "failed"}"></span>
        <span class="chain-row-name">${escapeHtml(network.label)}</span>
      </div>
      <strong class="chain-row-head">${ok ? fmtInt(network.blockNumber) : "unreachable"}</strong>
      <span class="chain-row-meta">${escapeHtml(String(network.chainId || "—"))} · ${ok ? escapeHtml(String(network.latencyMs)) + " ms" : escapeHtml(network.error || "no response")}</span>`;
    container.append(row);
  });

  const mainnet = snapshot.networks.find((item) => item.key === "mainnet") || {};
  const testnet = snapshot.networks.find((item) => item.key === "testnet") || {};

  $("#hero-block").textContent = mainnet.ok ? fmtInt(mainnet.blockNumber) : "—";
  $("#hero-block-note").textContent = mainnet.ok
    ? `${mainnet.rpcHost} · ${mainnet.latencyMs} ms · testnet ${testnet.ok ? fmtInt(testnet.blockNumber) : "—"}`
    : "Arc mainnet RPC unreachable";

  const liveCount = snapshot.networks.filter((item) => item.ok).length;
  $("#chain-chip").classList.toggle("is-error", liveCount === 0);
  $("#chip-text").textContent = liveCount === 0
    ? "Arc RPC unreachable"
    : liveCount + "/2 Arc networks live";
}

async function refreshChains(fresh) {
  try {
    const payload = await api("/api/chain" + (fresh ? "?fresh=1" : ""));
    if (payload.ok) {
      state.chains = payload.data;
      renderChains(payload.data);
    }
  } catch {
    /* the health check owns the offline state */
  }
}

async function checkHealth() {
  const dot = $("#status-dot");
  const label = $("#status-text");
  try {
    const payload = await api("/api/health");
    state.serverOk = Boolean(payload.ok);
    dot.className = "status-dot is-ok";
    label.textContent = "ArcDossier online";
  } catch {
    state.serverOk = false;
    dot.className = "status-dot is-error";
    label.textContent = "ArcDossier unavailable";
  }
}

/* -------------------------------------------------------------- metrics -- */

function renderMetrics() {
  const activity = state.activity;
  $("#metric-searches").textContent = fmtInt(BASE_SCREEN_COUNT + activity.searches);
  $("#metric-probes").textContent = fmtInt(activity.probes);
  $("#metric-proofs").textContent = fmtInt(activity.proofs);
  $("#metric-stopped").textContent = fmtInt(activity.stopped);
  $("#hero-proofs").textContent = fmtInt(activity.proofs);
  $("#search-total-nav").textContent = fmtInt(BASE_SCREEN_COUNT + activity.searches);
}

function renderRecent() {
  const container = $("#recent-list");
  const recent = state.activity.recent || [];
  container.innerHTML = "";

  if (!recent.length) {
    container.innerHTML = `<div class="empty-state"><strong>Nothing screened from this browser yet.</strong>
      <p>History stays in this browser only. The first project you screen appears here.</p></div>`;
  }

  recent.slice(0, 5).forEach((item) => {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "project-row";
    row.innerHTML = `
      <span class="project-avatar">${escapeHtml(String(item.title || item.query || "?").slice(0, 2).toUpperCase())}</span>
      <span class="project-info">
        <strong>${escapeHtml(item.title || item.query)}</strong>
        <small>${escapeHtml(item.query)}</small>
      </span>
      <span class="score-pill status-${escapeHtml(item.status)}">${escapeHtml(item.status)}</span>
      <span class="row-arrow">→</span>`;
    row.addEventListener("click", () => runSearch(item.query, { count: false }));
    container.append(row);
  });
}

function recordSearch(dossier) {
  const activity = state.activity;
  activity.searches += 1;
  activity.probes += dossier.sources.filter((source) => source.state === "fetched" || source.state === "proven").length;
  if (dossier.sources.some((source) => source.id === "contract-mainnet" && source.state === "proven")) {
    activity.proofs += 1;
  }
  if (dossier.status === "not-arc" || dossier.status === "unverified") {
    activity.stopped += 1;
  }
  activity.recent = [{ query: dossier.query, title: dossier.title, status: dossier.status, at: Date.now() }]
    .concat(activity.recent || [])
    .slice(0, 5);
  saveActivity();
  renderRecent();
  renderMetrics();
}

/* --------------------------------------------------------------- result -- */

function receiptBlock(evidence) {
  if (!evidence || !Object.keys(evidence).length) return "";
  const rows = RECEIPT_FIELDS
    .filter(([key]) => evidence[key] !== undefined && evidence[key] !== null && evidence[key] !== "")
    .map(([key, label]) => `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(fmtValue(key, evidence[key]))}</dd>`)
    .join("");
  if (!rows) return "";
  return `<details class="receipt"><summary>Receipt</summary><dl>${rows}</dl></details>`;
}

function sourceRow(source) {
  const stateClass = STATE_TEXT[source.state] ? source.state : "gap";
  return `
    <div class="result-source">
      <div class="result-source-head">
        <span class="source-state ${stateClass}"></span>
        <strong>${escapeHtml(source.label)}</strong>
      </div>
      ${source.target ? `<a class="source-target" href="${escapeHtml(source.target)}" target="_blank" rel="noopener">${escapeHtml(source.target)} ↗</a>` : ""}
    </div>`;
}

function tokenPanel(erc20) {
  if (!erc20) return "";
  const cells = [
    ["Symbol", erc20.symbol],
    ["Name", erc20.name],
    ["Decimals", erc20.decimals],
    ["Read on", erc20.networkLabel],
  ].filter(([, value]) => value !== undefined && value !== null && value !== "");

  if (!cells.length) return "";
  return `
    <div class="token-panel">
      <h4>On-chain reads</h4>
      <div class="erc20-grid">
        ${cells.map(([label, value]) => `<div class="erc20-cell"><span>${escapeHtml(label)}</span><strong>${escapeHtml(String(value))}</strong></div>`).join("")}
      </div>
      ${erc20.note ? `<p class="token-note">${escapeHtml(erc20.note)}</p>` : ""}
    </div>`;
}

function breakdownBlock(breakdown) {
  if (!breakdown || !breakdown.length) return "";
  const rows = breakdown.map((item) => `
    <div class="breakdown-row">
      <span class="breakdown-label">${escapeHtml(item.label)}<small>${escapeHtml(item.reason || "")}</small></span>
      <span class="breakdown-value ${item.earned ? "" : "is-zero"}">${item.earned}/${item.max}</span>
    </div>`).join("");
  return `<div class="breakdown"><h3>How the score was reached</h3>${rows}</div>`;
}

function receiptsFooter(dossier) {
  const networks = (dossier.receipts && dossier.receipts.networks) || [];
  const networkText = networks
    .map((network) => `${network.label}: block ${fmtInt(network.headBlock)} · chain ${network.chainId || "—"}`)
    .join("  |  ");
  return `
    <div class="result-foot">
      <span>SCREENED AS</span><code>${escapeHtml(dossier.query)}</code>
      <span>${escapeHtml(networkText)}</span>
      <span>generated ${escapeHtml(dossier.checkedAt)}</span>
      <button class="button button-ghost" id="recheck" type="button">Re-check live</button>
    </div>`;
}

function explorerFor(dossier, networkKey) {
  const chains = (dossier.chains && dossier.chains.networks) || [];
  const entry = chains.find((item) => item.key === networkKey);
  return entry ? entry.explorer : null;
}

function shortAddress(address) {
  return address ? address.slice(0, 10) + "…" + address.slice(-8) : "—";
}

function addressLink(address, explorer) {
  if (!address) return "—";
  const label = escapeHtml(shortAddress(address));
  if (!explorer) return label;
  return `<a href="${escapeHtml(explorer + "/address/" + address)}" target="_blank" rel="noopener">${label}</a>`;
}

const SEVERITY_LABEL = { risk: "risk", watch: "watch", info: "info" };

function networkMetricsBlock(dossier, key, entry) {
  const identity = entry.identity || {};
  const activity = entry.activity || {};
  const window = activity.window || {};
  const explorer = explorerFor(dossier, key);

  const identityCells = [
    ["Symbol", identity.symbol],
    ["Total supply", identity.totalSupply],
    ["Transfers in the recent period", activity.transfers],
    ["Active addresses", activity.uniqueAddresses],
    ["Transfers per minute", activity.transfersPerMinute],
    ["New tokens created", activity.mints],
    ["Tokens destroyed", activity.burns],
    ["Large transfers", activity.largeTransfers],
  ].filter(([, value]) => value !== undefined && value !== null && value !== "");

  const structure = (entry.structure || []).filter((probe) => probe.callable);
  const structureRows = structure.map((probe) => {
    if (probe.name === "paused") {
      return `<div class="structure-row"><span>Transfer status</span><strong>${probe.value ? "Transfers are halted" : "Transfers are active"}</strong></div>`;
    }
    const label = probe.name === "implementation" ? "Upgrade target"
      : probe.name === "owner" ? "Administrator"
      : probe.name === "admin" ? "Administrator"
      : probe.name + "()";
    return `<div class="structure-row"><span>${escapeHtml(label)}</span><strong>${addressLink(probe.value, explorer)}</strong></div>`;
  }).join("");

  const movers = (activity.topNetInflow || []).map((mover) => `
    <div class="mover-row">
      <span class="mover-address">${addressLink(mover.address, explorer)}</span>
      <span class="mover-net">+${escapeHtml(mover.net)}</span>
      <span class="mover-share">${mover.sharePct === null || mover.sharePct === undefined ? "—" : escapeHtml(String(mover.sharePct)) + "%"}</span>
    </div>`).join("");

  const signals = (entry.signals || []).map((signal) => `
    <div class="signal-row signal-${escapeHtml(signal.severity)}">
      <span class="state-tag ${signal.severity === "risk" ? "failed" : signal.severity === "watch" ? "gap" : "fetched"}">${escapeHtml(SEVERITY_LABEL[signal.severity] || signal.severity)}</span>
      <div><strong>${escapeHtml(readerText(signal.label))}</strong><small>${escapeHtml(readerText(signal.detail))}</small></div>
    </div>`).join("");

  const windowLine = window.blocksCovered
    ? `Recent activity covers about ${escapeHtml(String(window.estimatedMinutes))} minutes.`
    : "No recent activity period was available.";

  return `
    <div class="network-metrics">
      <div class="network-metrics-head">
        <span class="source-state ${activity.scanFailed ? "failed" : "proven"}"></span>
        <strong>${escapeHtml(entry.label || key)}</strong>
        <span class="state-tag ${activity.scanFailed ? "failed" : "proven"}">${activity.scanFailed ? "scan incomplete" : "measured"}</span>
      </div>

      <div class="erc20-grid metric-cells">
        ${identityCells.map(([label, value]) => `<div class="erc20-cell"><span>${escapeHtml(label)}</span><strong>${escapeHtml(String(value))}</strong></div>`).join("")}
      </div>

      ${structureRows ? `<div class="structure-list"><h4>Contract structure</h4>${structureRows}</div>` : ""}

      ${movers ? `<div class="movers"><h4>Largest increase in token balance during this period</h4>${movers}
        <p class="micro-note">This compares tokens received with tokens sent during the recent period only. An address appearing here is not necessarily a long-term holder.</p></div>` : ""}

      ${signals ? `<div class="signals"><h4>Contract warnings</h4>${signals}</div>` : ""}

      <p class="micro-note window-note">${escapeHtml(windowLine)}</p>
      <p class="micro-note">${escapeHtml(readerText(activity.caveat || ""))}</p>
    </div>`;
}

function providersPanel(dossier) {
  const providers = dossier.providers || {};
  const llama = providers.defillama;
  const gecko = providers.coingecko;
  const arcChain = providers.arcChain;
  const rootdata = (providers.rootdata && providers.rootdata.matched) || null;

  const money = (value) => (typeof value === "number"
    ? "$" + value.toLocaleString("en-US", { maximumFractionDigits: 0 })
    : "—");

  const protocolCells = arcChain ? [
    ["Network TVL", typeof arcChain.tvlUsd === "number" ? money(arcChain.tvlUsd) : null],
    ["Stablecoins on Arc", typeof arcChain.stablecoinSupplyUsd === "number" ? money(arcChain.stablecoinSupplyUsd) : null],
    ["DEX volume · 24h", typeof arcChain.dexVolume24hUsd === "number" ? money(arcChain.dexVolume24hUsd) : null],
    ["DEX volume · 7d", typeof arcChain.dexVolume7dUsd === "number" ? money(arcChain.dexVolume7dUsd) : null],
    ["Protocol fees · 24h", typeof arcChain.fees24hUsd === "number" ? money(arcChain.fees24hUsd) : null],
    ["Protocol fees · 7d", typeof arcChain.fees7dUsd === "number" ? money(arcChain.fees7dUsd) : null],
  ].filter(([, value]) => value !== null) : llama ? [
    ["Category", llama.category],
    ["TVL", typeof llama.tvlUsd === "number" ? money(llama.tvlUsd) : null],
    ["7d change", typeof llama.change7dPct === "number" ? llama.change7dPct.toFixed(1) + "%" : null],
    ["Market cap", typeof llama.mcapUsd === "number" ? money(llama.mcapUsd) : null],
    ["Chains", (llama.chains || []).slice(0, 4).join(", ")],
  ].filter(([, value]) => value !== null && value !== undefined && value !== "") : [];

  const geckoCells = gecko ? [
    ["Market cap", typeof gecko.marketCapUsd === "number" ? money(gecko.marketCapUsd) : null],
    ["FDV", typeof gecko.fdvUsd === "number" ? money(gecko.fdvUsd) : null],
    ["24h volume", typeof gecko.volume24hUsd === "number" ? money(gecko.volume24hUsd) : null],
    ["24h price", typeof gecko.priceChange24hPct === "number" ? gecko.priceChange24hPct.toFixed(2) + "%" : null],
    ["Rank", gecko.marketCapRank],
  ].filter(([, value]) => value !== null && value !== undefined && value !== "") : [];

  const funding = (llama && llama.funding) || [];
  const incidents = (llama && llama.incidents) || [];
  const team = (rootdata && rootdata.team) || [];
  const hasFunding = Boolean((rootdata && rootdata.totalFundingUsd) || funding.length);
  const hasContent = protocolCells.length || geckoCells.length || team.length || hasFunding || incidents.length;
  if (!hasContent) return "";

  return `
    <section class="providers-panel">
      <div class="metrics-head">
        <h3>Project data</h3>
        <p>Current third-party figures matched to this project's official domain or X profile.</p>
      </div>

      ${protocolCells.length ? `
        <div class="provider-card">
          <div class="provider-head">
            <strong>Protocol metrics</strong>
          </div>
          <div class="erc20-grid metric-cells">
            ${protocolCells.map(([label, value]) => `<div class="erc20-cell"><span>${escapeHtml(label)}</span><strong>${escapeHtml(String(value))}</strong></div>`).join("")}
          </div>
        </div>` : ""}

      ${geckoCells.length ? `
        <div class="provider-card">
          <div class="provider-head">
            <strong>Token market</strong>
          </div>
          <div class="erc20-grid metric-cells">
            ${geckoCells.map(([label, value]) => `<div class="erc20-cell"><span>${escapeHtml(label)}</span><strong>${escapeHtml(String(value))}</strong></div>`).join("")}
          </div>
        </div>` : ""}

      ${team.length ? `
      <div class="provider-card">
        <div class="provider-head">
          <strong>Team</strong>
        </div>
        ${team.map((person) => `<div class="provider-row"><span>${escapeHtml(person.name || "")}</span><strong>${escapeHtml(person.role || "")}</strong></div>`).join("")}
      </div>` : ""}

      ${hasFunding ? `
      <div class="provider-card">
        <div class="provider-head">
          <strong>Funding</strong>
        </div>
        ${rootdata && rootdata.totalFundingUsd ? `<div class="erc20-grid metric-cells">
          <div class="erc20-cell"><span>Total raised</span><strong>${money(rootdata.totalFundingUsd)}</strong></div>
          ${rootdata.investorCount ? `<div class="erc20-cell"><span>Investors</span><strong>${escapeHtml(String(rootdata.investorCount))}</strong></div>` : ""}
        </div>` : ""}
        ${rootdata && (rootdata.leadInvestors || []).length ? `<div class="provider-sub"><h4>Lead investors</h4><div class="provider-row"><span>${escapeHtml(rootdata.leadInvestors.join(", "))}</span></div></div>` : ""}
        ${funding.slice(-4).map((round) => `<div class="provider-row"><span>${escapeHtml(round.date || "")} · ${escapeHtml(round.round || "Round")}</span><strong>${round.amountUsdM ? "$" + escapeHtml(String(round.amountUsdM)) + "M" : ""}</strong></div>`).join("")}
      </div>` : ""}

      ${incidents.length ? `<div class="provider-card is-risk"><div class="provider-head"><strong>Security incidents</strong></div>${incidents.slice(-3).map((item) => `<div class="provider-row"><span>${escapeHtml(item.date || "")} · ${escapeHtml(item.classification || "Incident")}</span><strong>${item.amountUsd ? money(Number(item.amountUsd)) : ""}</strong></div>`).join("")}</div>` : ""}
    </section>`;
}

function scorecardPanel(dossier) {
  const frame = dossier.gradingFrame;
  if (!frame || frame.total === null || frame.total === undefined) return "";
  const groups = (frame.groups || []).filter((group) => group.score !== null);
  const modules = (frame.modules || []).filter((module) => module.score !== null);

  return `
    <section class="scorecard-panel">
      <div class="metrics-head">
        <h3>Why this score</h3>
        <p>It ranks research priority, not investment merit. Missing token, funding or revenue data is left out instead of counted as zero.</p>
      </div>
      <div class="scorecard-total">
        <strong>${Math.round(frame.total)}</strong><span>${escapeHtml(frame.researchLevel || "research score")}</span>
        <small>${frame.coveragePct}% evidence coverage</small>
      </div>
      ${groups.length ? `<div class="research-groups">${groups.map((group) => `
        <div class="research-group"><span>${escapeHtml(readerText(group.name))}</span><strong>${Math.round(group.score)}</strong>${group.summary ? `<p>${escapeHtml(readerText(group.summary))}</p>` : ""}</div>`).join("")}</div>` : ""}
      <div class="scorecard-modules">${modules.map((module) => `
        <span>${escapeHtml(readerText(module.name))} <strong>${module.score}/${module.maxScore}</strong></span>`).join("")}</div>
    </section>`;
}

function metricsPanel(dossier) {
  const metrics = dossier.tokenMetrics;
  if (!metrics || !metrics.networks) return "";
  const order = ["mainnet", "testnet"];
  const blocks = order
    .filter((key) => metrics.networks[key] && metrics.networks[key].deployed)
    .map((key) => networkMetricsBlock(dossier, key, metrics.networks[key]));
  if (!blocks.length) return "";

  return `
    <section class="metrics-panel">
      <div class="metrics-head">
        <h3>Blockchain activity</h3>
        <p>Recent use and contract controls for this Arc address.</p>
      </div>
      ${blocks.join("")}
    </section>`;
}

/* ----------------------------------------------------------- ai panel -- */

function aiNotConfigured() {
  return `
    <div class="ai-notice">
      <strong>Narrative layer not configured</strong>
      <p>The written analysis is produced server-side. The evidence snapshot, metrics and scorecard above do not
      depend on it and are complete on their own.</p>
    </div>`;
}

function naturalList(items) {
  if (items.length < 2) return items[0] || "";
  if (items.length === 2) return items.join(" and ");
  return items.slice(0, -1).join(", ") + ", and " + items[items.length - 1];
}

function contractSituation(dossier) {
  const networks = (dossier.tokenMetrics && dossier.tokenMetrics.networks) || {};
  const entry = networks.mainnet && networks.mainnet.deployed
    ? networks.mainnet
    : Object.values(networks).find((network) => network && network.deployed);
  if (!entry) return [];

  const identity = entry.identity || {};
  const activity = entry.activity || {};
  const window = activity.window || {};
  const symbol = identity.symbol && identity.symbol !== "—" ? identity.symbol : "";
  const label = entry.label || "Arc";
  const networkName = networks.mainnet === entry ? `${label} mainnet` : label;
  const contractName = symbol ? `${symbol} token contract` : "smart contract";
  const supply = identity.totalSupply ? ` It reports a total supply of ${identity.totalSupply}.` : "";

  const activityFacts = [];
  if (activity.transfers !== undefined && activity.transfers !== null) activityFacts.push(`${fmtInt(Number(activity.transfers))} transfers`);
  if (activity.uniqueAddresses !== undefined && activity.uniqueAddresses !== null) activityFacts.push(`${fmtInt(Number(activity.uniqueAddresses))} active addresses`);
  if (activity.transfersPerMinute !== undefined && activity.transfersPerMinute !== null) activityFacts.push(`${activity.transfersPerMinute} transfers per minute`);
  const period = window.estimatedMinutes ? `During the latest ${window.estimatedMinutes}-minute period checked` : "During the recent period checked";
  const activityLine = activityFacts.length ? ` ${period}, the contract recorded ${naturalList(activityFacts)}.` : "";

  const flowFacts = [];
  if (Number(activity.mints) === 0) flowFacts.push("no new token creation");
  if (Number(activity.burns) === 0) flowFacts.push("no token destruction");
  if (Number(activity.largeTransfers) === 0) flowFacts.push("no transfers of at least 1% of supply");
  const flowLine = flowFacts.length ? ` The same period showed ${naturalList(flowFacts)}.` : "";

  const structure = entry.structure || [];
  const administrator = structure.find((probe) => probe.callable && (probe.name === "owner" || probe.name === "admin"));
  const controlLine = administrator
    ? " The contract also exposes an administrator address, so privileged control may exist; the available data does not establish who controls it or the full extent of those powers."
    : "";

  const discovery = dossier.discovery || {};
  const sources = dossier.sources || [];
  const officialIdentity = Boolean(discovery.website || discovery.social || sources.some((source) => source.id === "website" || source.id === "social"));
  const providers = dossier.providers || {};
  const rootdata = providers.rootdata && providers.rootdata.matched;
  const llama = providers.defillama;
  const missing = [];
  if (!officialIdentity) missing.push("an official website or X account linking the address to a named project");
  if (!rootdata || !(rootdata.team || []).length) missing.push("a verified team");
  if (!(rootdata && rootdata.totalFundingUsd) && !(llama && (llama.funding || []).length)) missing.push("funding history");
  if (!providers.coingecko) missing.push("market price, market capitalisation, liquidity, or valuation data");
  const explorerNetworks = (dossier.explorerFacts && dossier.explorerFacts.networks) || {};
  const hasDistribution = Object.values(explorerNetworks).some((network) => network && network.distribution && network.distribution.top10Pct !== null && network.distribution.top10Pct !== undefined);
  if (!hasDistribution) missing.push("holder concentration");
  missing.push("a token unlock schedule");

  const identityGap = missing.length
    ? ` What remains unverified is ${naturalList(missing)}.`
    : "";
  const conclusion = officialIdentity
    ? ` The evidence therefore establishes a live ${networkName} deployment with measurable recent use, while the remaining gaps still limit an investment assessment.`
    : ` The evidence proves that the contract is live and being transferred on ${networkName}, but it does not yet prove who operates it, what product it belongs to, or whether the token has sustainable value.`;

  return [
    `This address is a live ${contractName} on ${networkName}; the deployment itself is verified.${supply}${activityLine}${flowLine}${controlLine}`,
    `${identityGap}${conclusion}`.trim(),
  ].filter(Boolean);
}

function researchOverview(dossier) {
  const frame = dossier.gradingFrame || {};
  const modules = (frame.modules || []).filter((module) => module.score !== null && module.score !== undefined);
  if (!modules.length) return "";

  const contractSummary = contractSituation(dossier);
  if (contractSummary.length) {
    const total = Number(frame.total);
    const scoreContext = Number.isFinite(total)
      ? `The ${Math.round(total)}/100 research-priority score reflects the evidence currently available. It is not a buy or sell recommendation.`
      : "This is an evidence summary, not a buy or sell recommendation.";
    return `<div class="research-overview">
      <span>Overall snapshot</span>
      ${contractSummary.map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`).join("")}
      <p class="research-overview-context">${escapeHtml(scoreContext)}</p>
    </div>`;
  }

  const scoreSummary = naturalList(modules.map((module) => {
    const score = Number(module.score);
    const formatted = Number.isInteger(score) ? String(score) : score.toFixed(1);
    return `${readerText(module.name)} ${formatted}/5`;
  }));

  const evidence = [];
  modules.forEach((module) => {
    (module.evidence || []).slice(0, 1).forEach((item) => {
      const cleaned = readerText(item).replace(/[.]$/, "");
      if (cleaned && !evidence.includes(cleaned)) evidence.push(cleaned);
    });
  });

  const openQuestions = {
    product: "a clearly differentiated and fully documented product",
    data: "sustained usage and growth",
    team: "a verified execution team",
    funding: "confirmed financial backing",
    token: "clear token value capture and valuation",
    position: "category leadership within the Arc ecosystem",
    heat: "a dated market catalyst",
  };
  const unresolved = modules
    .filter((module) => Number(module.score) < 3)
    .map((module) => openQuestions[module.id])
    .filter(Boolean);

  const total = Number(frame.total);
  const profile = Number.isFinite(total) && total >= 75
    ? "a strong evidence profile"
    : Number.isFinite(total) && total >= 60
      ? "a developing evidence profile"
      : "an early evidence profile";
  const coverage = Number.isFinite(Number(frame.coveragePct))
    ? ` The score covers ${Math.round(Number(frame.coveragePct))}% of the research framework; modules without verified data are omitted rather than counted as weaknesses.`
    : "";
  const evidenceSentence = evidence.length
    ? ` The evidence currently confirms: ${evidence.slice(0, 4).join("; ")}.`
    : "";
  const unresolvedSentence = unresolved.length
    ? ` The available information does not yet establish ${naturalList([...new Set(unresolved)].slice(0, 4))}.`
    : "";

  return `<div class="research-overview">
    <span>Overall snapshot</span>
    <p>This dossier currently presents ${profile}. The measured areas are ${escapeHtml(scoreSummary)}.${escapeHtml(evidenceSentence)}${escapeHtml(unresolvedSentence)}${escapeHtml(coverage)}</p>
  </div>`;
}

function aiPanel(dossier) {
  const status = state.aiStatus;
  if (!status || !status.configured) return "";
  return `
    <section class="ai-panel" data-query="${escapeHtml(dossier.query)}">
      <div class="ai-head">
        <div>
          <h3>Research report</h3>
          <p>A detailed, plain-language answer from the most relevant available evidence.</p>
        </div>
      </div>
      ${researchOverview(dossier)}
      <div class="ai-body" id="ai-body"><p class="ai-status">Preparing the analysis…</p></div>
    </section>`;
}

function aiAnalysisBody(result) {
  const report = result.report;
  const analysis = report.analysis || {};
  const narrative = analysis.narrative || {};
  const fields = [
    ["Overview", narrative.overview],
    ["Product", narrative.product],
    ["Traction", narrative.traction],
    ["Team and backing", narrative.backing],
    ["Token opportunity", narrative.tokenOpportunity],
    ["Ecosystem and timing", narrative.timing],
    ["Overall analysis", narrative.overallAnalysis],
  ].filter(([, value]) => value && String(value).trim());
  if (!fields.length) return "";

  return `
    <div class="ai-result">
      ${fields.map(([label, value]) => `<div class="ai-field"><span>${escapeHtml(label)}</span><p>${escapeHtml(readerText(value))}</p></div>`).join("")}
      ${(analysis.risks || []).length ? `<div class="ai-field"><span>What to verify next</span><ul>${analysis.risks.slice(0, 3).map((item) => `<li>${escapeHtml(readerText(item.summary || ""))}</li>`).join("")}</ul></div>` : ""}
    </div>`;
}

function aiPendingBody(result) {
  return `
    <div class="ai-notice ai-notice-pending">
      <strong>${result.status === "budget-exhausted" ? "Daily budget reached" : "Analysis pending"}</strong>
      <p>${escapeHtml(result.message || "")}</p>
      ${(result.attempts || []).length ? `<ul>${result.attempts.map((attempt) => `<li>${attempt.shortenedRetry ? "shortened retry" : "first attempt"}: ${escapeHtml(attempt.error)}</li>`).join("")}</ul>` : ""}
      ${result.packet ? `<p class="micro-note">The evidence packet contains ${result.packet.facts.length} facts and is ready for another attempt.</p>` : ""}
    </div>`;
}

async function loadAiStatus() {
  try {
    const payload = await api("/api/ai/status");
    if (payload.ok) state.aiStatus = payload.data;
  } catch {
    state.aiStatus = null;
  }
}

async function runAnalysis() {
  const panel = document.querySelector(".ai-panel");
  const body = $("#ai-body");
  if (!panel || !body) return;
  if (!state.aiStatus || !state.aiStatus.configured) return;

  const query = panel.dataset.query;
  body.innerHTML = `<p class="ai-status">Writing the research report…</p>`;
  try {
    const payload = await api("/api/analyze?q=" + encodeURIComponent(query) + "&mode=quick");
    if (!payload.ok) throw new Error(payload.error || "the server rejected the request");
    const result = payload.data;
    const content = result.report ? aiAnalysisBody(result) : aiPendingBody(result);
    if (content) body.innerHTML = content;
    else body.innerHTML = `<p class="ai-status">No additional narrative was available.</p>`;
  } catch (error) {
    body.innerHTML = `<div class="ai-notice ai-notice-pending"><strong>Analysis unavailable</strong><p>${escapeHtml(error.message || "The analysis request failed.")}</p></div>`;
  }
}

function knowledgeLink(label, href) {
  const safe = safeHttpUrl(href);
  return safe ? `<a href="${escapeHtml(safe)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)} ↗</a>` : "";
}

function renderKnowledgeCandidates(result, query) {
  const candidates = result.candidates || [];
  const container = $("#search-result");
  container.innerHTML = `<article class="result-card result-unverified">
    <div class="result-heading"><div><span class="result-status">Identity check</span>
      <h3>More than one project matches “${escapeHtml(query)}”</h3>
      <p>Select the contract address instead of merging projects that share a name or symbol.</p></div></div>
    <div class="knowledge-candidates">${candidates.map((item) => `
      <button type="button" class="knowledge-candidate" data-knowledge-ca="${escapeHtml(item.contractAddress || "")}">
        <span><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(item.symbol || "")}</small></span>
        <code>${escapeHtml(item.contractAddress || "No token contract")}</code>
      </button>`).join("")}</div>
  </article>`;
  container.querySelectorAll("[data-knowledge-ca]").forEach((button) => {
    button.addEventListener("click", () => runSearch(button.dataset.knowledgeCa, { count: true }));
  });
}

function renderKnowledgeResult(result, query) {
  const profile = result.match;
  const container = $("#search-result");
  const token = (profile.tokens || [])[0] || {};
  const website = knowledgeLink("Official website", profile.website);
  const handle = String(profile.xHandle || "").replace(/^@/, "");
  const social = handle ? knowledgeLink("X · @" + handle, "https://x.com/" + handle) : "";
  const modules = Object.entries(profile.modules || {});
  const links = [website, social].filter(Boolean).join("");
  const sources = (profile.sources || []).map((source, index) => {
    const href = safeHttpUrl(source.url);
    return href ? `<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">Source ${index + 1} ↗</a>` : "";
  }).filter(Boolean);

  container.innerHTML = `<article class="result-card result-verified knowledge-result">
    <div class="result-heading">
      <div><span class="result-status">Saved Arc research · ${escapeHtml(profile.researchDate || "date unavailable")}</span>
        <h3>${escapeHtml(profile.name)}${profile.symbol ? ` <small>${escapeHtml(profile.symbol)}</small>` : ""}</h3>
        ${profile.summaryEn ? `<p>${escapeHtml(profile.summaryEn)}</p>` : profile.summaryZh ? `<p>${escapeHtml(profile.summaryZh)}</p>` : ""}
      </div>
      <div class="knowledge-speed"><strong>${escapeHtml(String(result.latencyMs || 0))} ms</strong><span>local match</span></div>
    </div>

    <section class="knowledge-section">
      <div class="metrics-head"><h3>Project overview</h3><p>Identity matched before any external research call.</p></div>
      <div class="knowledge-identity">
        ${profile.category ? `<span><small>Category</small><strong>${escapeHtml(profile.category)}</strong></span>` : ""}
        ${token.contract_address ? `<span><small>Arc contract · chain 5042</small><code>${escapeHtml(token.contract_address)}</code></span>` : ""}
        ${links ? `<span class="knowledge-links"><small>Official surfaces</small>${links}</span>` : ""}
      </div>
    </section>

    <section class="knowledge-section" id="knowledge-market">
      <div class="metrics-head"><h3>Market data</h3><p>Loading the latest market data independently…</p></div>
      <div class="market-loading">Research is already available while the market request runs.</div>
    </section>

    ${modules.length ? `<section class="knowledge-section">
      <div class="metrics-head"><h3>Saved research</h3><p>Imported from the v0.5 research package. Unverified fields remain unverified.</p></div>
      <div class="knowledge-modules">${modules.map(([name, value]) => `<article>
        <span>${escapeHtml(name.replace(/^\d+_?/, "").replaceAll("_", " "))}</span>
        <p>${escapeHtml(value)}</p>
      </article>`).join("")}</div>
    </section>` : ""}

    ${(profile.risks || []).length ? `<section class="knowledge-section">
      <div class="metrics-head"><h3>Risks to review</h3><p>Research flags, not buy or sell recommendations.</p></div>
      <ul class="knowledge-risks">${profile.risks.map((risk) => `<li>${escapeHtml(risk)}</li>`).join("")}</ul>
    </section>` : ""}

    ${sources.length ? `<details class="knowledge-sources"><summary>Research sources · ${sources.length}</summary><div>${sources.join("")}</div></details>` : ""}
    <div class="result-foot"><span>FOUND AS</span><code>${escapeHtml(query)}</code><button class="button button-ghost" id="recheck" type="button">Refresh data</button></div>
  </article>`;

  const recheck = $("#recheck");
  if (recheck) recheck.addEventListener("click", () => runSearch(query, { count: false, fresh: true }));
  container.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderKnowledgeMarket(payload) {
  const section = $("#knowledge-market");
  if (!section) return;
  const tokens = payload.tokens || [];
  const market = tokens.find((item) => item.status !== "unavailable") || tokens[0];
  if (!market || market.status === "unavailable") {
    section.innerHTML = `<div class="metrics-head"><h3>Market data</h3><span class="market-status is-unavailable">Unavailable</span></div>
      <p class="market-empty">No reliable market quote was returned. The saved project research remains available above.</p>`;
    return;
  }
  const status = market.status || payload.status || "unavailable";
  const cells = [
    ["Price", formatUsd(market.priceUsd)], ["Market cap", formatUsd(market.marketCapUsd)],
    ["FDV", formatUsd(market.fdvUsd)], ["Volume · 24h", formatUsd(market.volume24hUsd)],
    ["Liquidity", formatUsd(market.liquidityUsd)], ["Transactions · 24h", fmtInt(market.txns24h)],
    ["Change · 1h", formatPercent(market.priceChange1hPct)], ["Change · 6h", formatPercent(market.priceChange6hPct)],
    ["Change · 24h", formatPercent(market.priceChange24hPct)],
  ].filter(([, value]) => value !== "—");
  const pairLink = knowledgeLink("Open primary pool", market.pairUrl);
  section.innerHTML = `<div class="metrics-head"><div><h3>Market data</h3><p>${escapeHtml(market.dataSource || "Market API")} · ${escapeHtml(market.updatedAt || "time unavailable")}</p></div>
      <span class="market-status is-${escapeHtml(status)}">${escapeHtml(status)}</span></div>
    ${cells.length ? `<div class="erc20-grid metric-cells">${cells.map(([label, value]) => `<div class="erc20-cell"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}</div>` : ""}
    ${(market.pairAddress || pairLink) ? `<div class="market-pair">${market.pairAddress ? `<code>${escapeHtml(market.pairAddress)}</code>` : ""}${pairLink}</div>` : ""}`;
}

function renderResult(dossier) {
  const container = $("#search-result");
  const hardGate = dossier.status === "not-arc";
  const noArcScore = dossier.status === "unverified";
  const frame = dossier.gradingFrame || {};
  const researchScore = frame.total === null || frame.total === undefined ? null : Math.round(frame.total);
  const scorePanel = researchScore !== null
    ? `<div class="detail-score"><strong>${researchScore}</strong><span>${escapeHtml(frame.researchLevel || "RESEARCH SCORE")}</span></div>`
    : "";
  const description = dossier.description && !/^No source-supplied/i.test(dossier.description)
    ? `<p>${escapeHtml(dossier.description)}</p>` : "";

  const stopPanel = hardGate
    ? `<div class="ecosystem-stop">
         <strong>Not identified as an Arc ecosystem project</strong>
         <p>No Arc dossier was generated for this search.</p>
       </div>`
    : `${noArcScore ? `<div class="ecosystem-stop">
         <strong>Arc connection not yet verified</strong>
         <p>The available project data is shown below without treating missing Arc evidence as a negative score.</p>
       </div>` : ""}
       ${providersPanel(dossier)}
       ${metricsPanel(dossier)}
       ${scorecardPanel(dossier)}`;

  container.innerHTML = `
    <article class="result-card result-${escapeHtml(dossier.status)}">
      <div class="result-heading">
        <div>
          <span class="result-status">${escapeHtml(dossier.statusLabel)}</span>
          <h3>${escapeHtml(dossier.title)}</h3>
          ${description}
        </div>
        ${scorePanel}
      </div>
      ${stopPanel}
      ${hardGate ? "" : aiPanel(dossier)}
      ${hardGate ? "" : `<div class="result-foot"><button class="button button-ghost" id="recheck" type="button">Refresh data</button></div>`}
    </article>`;

  const recheck = $("#recheck");
  if (recheck) {
    recheck.addEventListener("click", () => runSearch(dossier.query, { count: false, fresh: true }));
  }
  container.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* --------------------------------------------------------------- search -- */

async function runSearch(query, options) {
  const settings = options || {};
  const cleanQuery = String(query || "").trim();
  if (!cleanQuery) {
    showToast("Enter an official website, X profile, or contract address.");
    return;
  }
  if (state.busy) {
    showToast("A screen is already running.");
    return;
  }
  state.busy = true;
  state.lastQuery = cleanQuery;
  showView("search");
  $("#project-query").value = cleanQuery;
  setSearchStatus("Gathering project, market and Arc ecosystem data…", "loading");
  $("#search-result").innerHTML = `<div class="empty-state"><strong>Running the checks…</strong><p>Fetching published sources and reading the Arc chain.</p></div>`;

  try {
    const knowledgePayload = await api("/api/knowledge?q=" + encodeURIComponent(cleanQuery));
    const resolved = knowledgePayload.ok ? knowledgePayload.data : null;
    if (resolved && resolved.match) {
      renderKnowledgeResult(resolved, cleanQuery);
      if (settings.count !== false) recordSearch({
        query: cleanQuery, title: resolved.match.name, status: "saved", sources: [],
      });
      try {
        const shareable = new URL(window.location.href);
        shareable.searchParams.set("q", cleanQuery);
        shareable.searchParams.delete("mode");
        window.history.replaceState(null, "", shareable);
      } catch { /* history is unavailable in some embedding contexts */ }
      setSearchStatus("Saved research loaded. Refreshing current market data…", "loading");
      try {
        const marketPayload = await api("/api/market?project_id=" + encodeURIComponent(resolved.match.projectId) +
          (settings.fresh ? "&fresh=1" : ""));
        if (marketPayload.ok) renderKnowledgeMarket(marketPayload.data);
        else renderKnowledgeMarket({ status: "unavailable", tokens: [] });
      } catch {
        renderKnowledgeMarket({ status: "unavailable", tokens: [] });
      }
      setSearchStatus("");
      return;
    }
    if (resolved && (resolved.candidates || []).length > 1) {
      renderKnowledgeCandidates(resolved, cleanQuery);
      setSearchStatus("");
      return;
    }

    const payload = await api("/api/dossier", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ query: cleanQuery, fresh: Boolean(settings.fresh), profile: "quick" }),
    });
    if (!payload.ok) throw new Error(payload.error || "the server rejected the request");
    renderResult(payload.data);
    if (settings.count !== false) recordSearch(payload.data);
    if (payload.data.chains) {
      state.chains = payload.data.chains;
      renderChains(payload.data.chains);
    }
    try {
      const shareable = new URL(window.location.href);
      shareable.searchParams.set("q", cleanQuery);
      shareable.searchParams.delete("mode");
      window.history.replaceState(null, "", shareable);
    } catch {
      /* history is unavailable in some embedding contexts */
    }
    if (payload.data.status !== "not-arc" && state.aiStatus && state.aiStatus.configured) {
      setSearchStatus("Project data is ready. Writing the research report…", "loading");
      await runAnalysis();
    }
    setSearchStatus("");
  } catch (error) {
    setSearchStatus(
      "Could not assemble a dossier: " + error.message +
      ". The ArcDossier service could not complete the checks. Please try again shortly.",
      "error"
    );
    $("#search-result").innerHTML = `<div class="empty-state"><strong>No dossier assembled.</strong>
      <p>The checks run server-side, so nothing was verified and nothing was scored.</p></div>`;
  } finally {
    state.busy = false;
  }
}

/* --------------------------------------------------------------- wiring -- */

document.querySelectorAll("[data-view-link]").forEach((button) => {
  button.addEventListener("click", (event) => {
    event.preventDefault();
    showView(button.dataset.viewLink);
  });
});

$("#search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  runSearch($("#project-query").value, { count: true });
});

document.querySelectorAll("[data-example-query]").forEach((button) => {
  button.addEventListener("click", () => runSearch(button.dataset.exampleQuery, { count: true }));
});

$("#load-example").addEventListener("click", () => runSearch("arc.io", { count: true }));

document.addEventListener("visibilitychange", () => {
  if (!document.hidden) refreshChains(false);
});

/* A client-side failure used to leave the page silently half-rendered. Surface it
   instead, so a blank result area is never mistaken for "nothing found". */
function surfaceClientError(message) {
  const target = document.querySelector("#search-result");
  if (!target) return;
  target.insertAdjacentHTML("afterbegin",
    `<div class="ai-notice ai-notice-pending"><strong>The page hit a scripting error</strong>
     <p>${escapeHtml(String(message)).slice(0, 400)}</p>
     <p class="micro-note">The checks may have completed on the server; reload to try again.</p></div>`);
}

window.addEventListener("error", (event) => surfaceClientError(event.message + " (line " + event.lineno + ")"));
window.addEventListener("unhandledrejection", (event) => surfaceClientError("unhandled rejection: " + (event.reason && event.reason.message ? event.reason.message : event.reason)));

checkHealth();
renderRecent();
renderMetrics();
window.setInterval(() => refreshChains(false), CHAIN_REFRESH_MS);

/* Load the AI configuration before any dossier renders, so the analysis panel
   never briefly claims the layer is unconfigured when it is not. */
(async function bootstrap() {
  await loadAiStatus();
  await refreshChains(true);

  /* Deep link: /?q=arc.network renders that dossier and its standard report. */
  let shared = null;
  try {
    const params = new URL(window.location.href).searchParams;
    shared = params.get("q");
  } catch {
    shared = null;
  }
  if (shared && shared.trim()) {
    await runSearch(shared, { count: false });
  }
})();
