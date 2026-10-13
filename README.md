# ArcDossier v0.3 — Arc ecosystem research

ArcDossier turns a project identifier into an evidence-backed dossier about the Arc
ecosystem. It is deliberately narrow: one input, a documented ecosystem gate, live
source probes, an on-chain Arc membership check, a transparent score, and a stated
list of what it still cannot prove.

The v0.2 prototype was static. v0.3 replaced it with live systems — see "What
changed" below.

## Website

[arcdossier.site](https://arcdossier.site) is the public product entry point.

Deep link: `https://arcdossier.site/?q=arc.network` renders that dossier on load.

## Onchain receipt contract

`contracts/src/ArcDossierRegistry.sol` is the only ArcDossier component intended for
Arc deployment. It stores a compact receipt (`projectId`, `reportHash`, generation
time, and scoring version); the report body and source material remain offchain. Only
the wallet that deploys the contract can publish receipts. The contract never holds or
moves user funds.

Build and test with Arc Foundry:

```bash
arc-forge test --network arc
```

ArcDossierRegistry is deployed on Arc Mainnet. Deployment addresses and transaction
hashes are recorded under `contracts/deployments/`; private keys never belong in this
repository. No report receipt has been anchored yet.
The deployed bytecode has an [exact-match source verification on Sourcify](https://sourcify.dev/server/v2/verify/0bafc9f3-cef7-43b3-bafc-7d9f84d7418b).

| Network | Contract | Deployment transaction |
|---|---|---|
| Arc Mainnet (5042) | [`0xFB7b…4336`](https://explorer.arc.io/address/0xFB7b800F5EE5bA8a38CEF7407897F5F3a2A14336) | [`0x9925…c0bc`](https://explorer.arc.io/tx/0x9925c860275a400e570d41276b129b3d9ec955c8e23622d268353464976ec0bc) |

## What is real

- **Arc membership proof.** Contract addresses are read with `eth_getCode` on **Arc
  mainnet and Arc testnet separately**. Bytecode size, the block it was read at, and a
  SHA-256 of the returned code are recorded. An empty result is reported as a finding,
  not smoothed over.
- **Live source probes.** Every source on the dossier is fetched by the ArcDossier service,
  which records HTTP status, final URL after redirects, content type, byte count, page
  title, description, the SHA-256 of the body, and the timestamp.
- **Link discovery, not URL guessing.** Documentation and repository links are probed
  only when the project's own page publishes them. A missing link is reported as a gap.
- **On-chain ERC-20 reads.** When bytecode exists, `symbol()`, `name()` and `decimals()`
  are read with `eth_call`.
- **Transparent scoring.** Every point maps to a specific check with a stated reason.
  When Arc membership is unproven, **no score is issued** and the zeroed breakdown stays
  visible so the reader can see which checks came back empty.
- **Deterministic metrics for contract searches.** Supply, contract structure and a
  bounded activity window, all read from the chain — see the section below.
- **Live network readout.** Mainnet and testnet head blocks, chain IDs and RPC latency,
  with the returned chain ID verified against the expected one on every refresh.

## Research report

The interface has one report path. It gathers a bounded evidence set, then uses
`MiniMax-M2.7-highspeed` without an explicit reasoning-effort field to write a detailed,
plain-language report. Output is capped at 2,200 tokens, the evidence packet at 16,000
characters, and an unsuccessful response is not automatically sent again. Stable prompts,
content-hash caching and evidence ordering keep repeated searches from spending another
model call when the evidence has not changed. If the single model response cannot be
parsed, the server finishes a simpler report from the verified packet and caches it;
there is no paid repair call. The former deep-report endpoint returns HTTP 410.

**The interface never names the model.** Public status (`/api/ai/status`) returns the modes
and the budget but no model, provider or protocol; the operator can read those from the
report log or `/api/ai/status?admin=1`.

## Scorecard

Seven dimensions instead of one blended number:

| Dimension | Max | Source |
|---|---|---|
| Arc membership | 20 | `eth_getCode` on mainnet and testnet |
| Contract safety | 20 | explorer verification + structure probes + observed minting |
| Distribution | 15 | explorer holder list: top-1 and top-10 share of supply |
| Market activity | 15 | transfer-log scan: rate, breadth, mints, burns |
| Source verifiability | 18 | live probes + mutually confirmed cross-links |
| Narrative and documentation | 10 | whether the project documents itself, not whether the story convinces |
| Funding and team | 10 | **no data source connected — always unmeasured today** |

Two rules keep this honest:

1. **A dimension with no data source is marked unmeasured and excluded from the total.**
   Scoring it zero would report our blind spots as findings about the project.
2. **Limits of the query shape never cost points.** A contract-only screen has no website to
   verify, so "Source verifiability" is unmeasured rather than 0/18.

## Cross-source discovery

One input should lead to the project's other surfaces.

- **From a website** the page's own links yield the X handle, and any published contract
  addresses are extracted from the text.
- **From an X handle** the profile's declared link yields the website. X renders that link in
  a React payload with an unquoted `expanded_url` key, so it is found by scanning the page
  body rather than its `href` attributes.
- **A candidate website only counts once it links back to the same handle.** One-way links
  from a profile are routinely tweets, mirrors or unrelated CDNs — an early version of this
  code confidently reported `pbs.twimg.com` (X's image host) as a project homepage.
- **From a contract address, reverse lookup is not possible** and the dossier says so. The
  chain holds no address-to-website registry, and the explorer publishes token metadata
  rather than a project home page.

## Data sources

| Source | Covers | Access | Measured here? |
|---|---|---|---|
| Arc RPC | deployment, supply, contract structure, transfer activity | free, no key | yes |
| Arc explorer (Blockscout API) | holder count, supply concentration, source verification | free; mainnet is behind a bot challenge | yes (testnet) |
| **DefiLlama** | TVL, product category, chains, market cap, funding rounds, security incidents | free, no key | yes |
| **CoinGecko** | market cap, FDV, 24h volume, price change, categories | free tier | yes |
| Official website and X | the project's own numbers, quoted | free | yes, labelled as claims |
| **RootData** | team identity, funding, investors | **no public API** — partnership only | no |
| Crunchbase / CryptoRank / Messari | team, funding | paid keys | not wired |

**Team identity has no free structured source.** RootData would cover it but publishes no open
API (`api.rootdata.com` returns 404 and its pages sit behind JS protection), so that dimension
stays unmeasured rather than being filled with whatever a website says about itself.

**Funding is available for free after all** — the bulk `/raises` endpoint returns HTTP 402, but
the per-protocol `raises` field on `/protocol/{slug}` carries the round, the amount and the
sector. The same response carries `hacks`, so recorded exploits feed the safety dimension.

### Matching, and why it is by domain

Protocols are matched against the **domain and X handle the project itself publishes**, joined
against DefiLlama's own `url` and `twitter` fields (5,285 protocols publish a URL). Name matching
is only a last resort. A name-based match is a guess; a domain match is an exact join.

### Two channels, never merged

Third-party figures and self-reported figures are displayed in separate blocks. On Lido the two
channels disagree slightly — DefiLlama reports $24,856,815,688 TVL, the project's own page says
$24,689,839,600 — which is exactly why they are not averaged together.

Self-reported extraction is deliberately strict: the number must sit directly before its keyword
and fall inside a plausible range for that kind of metric. A looser version reported "32.7B users"
on a real site; a claim that absurd would discredit every other number on the page. Each claim is
shown with the sentence it came from, because that sentence is often the caveat — on Aave the
"21M+ users" turned out to refer to a partner's users, not Aave's own.

### Product-type awareness

DefiLlama's curated category selects what the dossier highlights, per a per-category template —
a Launchpad surfaces launches and volume, a Liquid Staking protocol surfaces staked value and
validator risk, a Bridge surfaces bridged value and incident history.

## Explorer facts

Holder counts, supply distribution and verification status come from the explorer's
Blockscout-compatible API. Only metadata is read — never published source code.

`explorer.arc.io` sits behind a Cloudflare bot-protection challenge and refuses automated
lookups; this is reported as such rather than worked around, and the scorecard states which
network's explorer the holder data came from.

## Deterministic metrics

Contract searches get a second panel that involves no model and no estimation. Every
number is either a decoded `eth_call` result or a count of logs the server actually
retrieved:

| Group | Contents |
|---|---|
| Identity | `symbol()`, `name()`, `decimals()`, `totalSupply()` |
| Contract structure | `implementation()`, `owner()`, `admin()`, `paused()` — probed by calling them |
| Activity window | transfers, unique addresses, transfers/min, mints, burns, transfers ≥ 1% of supply, largest net inflow |
| Risk signals | upgradeable proxy, owner role, separate admin, pausable, minting observed, activity concentration, large transfers |

Three honesty rules are baked in:

1. **Structure is probed by calling, not by scanning bytecode.** A four-byte selector
   can appear in a contract as data, so a selector hit is not evidence. A decodable
   `eth_call` answer is.
2. **The activity window is bounded and labelled as such.** It is not a holder snapshot
   and not a full history. The panel prints the exact block range, its estimated
   duration, how many RPC calls it took, and what stopped it.
3. **A failed scan is not reported as an absence of activity.** If the RPC refuses every
   log query, the panel says `scan incomplete` and draws no conclusion. Likewise "no
   minting in window" is stated as exactly that, never as "cannot mint".

These figures never affect the Arc membership score. Deployment is a fact about
membership; activity is a different question.

### The log-scan constraint, as measured

`eth_getLogs` on Arc is tighter than the documented 10,000-block range suggests, and
**the cap is dynamic**. Measured against USDC on Arc testnet:

| Requested span | Result |
|---|---|
| 2,000 blocks | succeeded once (8,586 logs), rejected as `-32602 exceeds max results` on another attempt |
| 2,500 blocks | succeeded (10,571 logs) |
| 3,000 blocks | succeeded (12,619 logs) |
| 5,000 blocks | rejected `-32602` |
| 10,000 / 20,000 blocks | rejected `-32012 requested range too large` |

The same span can pass or fail minutes apart, so the scanner starts at 2,000 blocks,
halves on a range error, grows while results stay sparse, retries transient non-JSON
responses with backoff, and stops at 14 calls, 20,000 logs or 30 seconds — whichever
comes first. A dense token therefore yields a shorter window than a sparse one, and the
panel always states which window you actually got.

## What is still not verified

- **Ownership.** RPC proves a contract is deployed on Arc. It does not prove the team
  behind the website owns that contract. Nothing here establishes that link.
- **Quality.** A deployed contract is not a good project. No code audit, no tokenomics.
- **X profile identity.** Profile shells are login-walled: presence is confirmed,
  account ownership is not.
- **Testnet vs mainnet weight.** A testnet deployment is cheap. Testnet-only projects are
  labelled as such and score lower than mainnet deployments.
- **Rate limits.** Arc does not document numeric RPC rate limits. This server stays
  polite anyway: 40 source probes per minute, a 10 s fetch timeout, a 512 KB body cap,
  4 redirects maximum, and a 5-minute probe cache.

## API

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Liveness and version |
| `GET /api/chain` | Both networks: chainId, head block, latency, client version |
| `GET /api/probe?url=` | Fetch one source, return its receipt |
| `GET /api/contract?address=` | `eth_getCode` + ERC-20 metadata on both networks |
| `GET /api/token?address=` | Deterministic token metrics: identity, structure probes, activity window, risk signals |
| `GET /api/ai/status` | Whether the AI layer is configured, which model and endpoint, daily budget usage. Never returns the key |
| `GET /api/analyze?q=&mode=quick` | Build the evidence packet and run the single public report; served from the report cache when the evidence is unchanged |
| `GET /api/report` | Removed deep-report endpoint; returns HTTP 410 without calling a model |
| `GET /api/ai/status` | Modes and budget only. Add `?admin=1` to see the model and provider |
| `GET/POST /api/dossier?q=` | Full dossier for a website, X handle, or contract |

Add `fresh=1` to bypass the cache. Static assets are served from a whitelist
(`/`, `/index.html`, `/styles.css`, `/app.js`) plus `/fonts/<name>` from a strict
filename pattern; everything else 404s.

## AI analysis layer

Optional and off by default. The server calls the model; the browser never does, and
no key is ever sent to the front end.

```bash
cp .env.example .env      # then put your key in it
set -a; . ./.env; set +a
python3 server.py
```

Without a credential the panel says so plainly and nothing is sent anywhere. The
deterministic sections are unaffected — they never needed the model.

**Division of labour, enforced structurally.** Deterministic code owns every number,
score, risk signal and freshness value. The model owns narrative and cross-source
reasoning only. Three mechanisms keep that boundary from eroding:

1. **The output schema contains no score field.** A model cannot influence a score
   that has nowhere to be written.
2. **Score-like keys are stripped from any response** (`score`, `rating`, `grade`,
   `confidence`, `rank`, `recommendation`, `verdict`), and the removal is displayed.
3. **Citations are checked against the packet.** Every claim must cite fact ids;
   a claim citing an id that does not exist in the evidence packet is not shown as a
   finding — it is moved into Open questions with the reason recorded.

**Cost and quota control**

| Control | Behaviour |
|---|---|
| Explicit thinking effort | Not sent by the public report path |
| Daily call cap | `ARC_AI_DAILY_CALLS` (default 50); over budget, cached analyses keep serving |
| Content-hash cache | Identical evidence is never analysed twice |
| One-call ceiling | No automatic retry; an unusable response falls back to an evidence-only report and is cached |
| Input budget | The packet is truncated to a fixed character budget rather than filling the 1M-token window |

**Provenance and the report hash chain.** Each stored report records the model, protocol,
effort, token usage, latency, packet hash, cache key, and its own hash plus the previous
report's hash. That gives tamper-evident history without spending gas. Anchoring
report hashes on Arc is deliberately **not** implemented: it costs USDC per write, and
it would only prove that a document existed at a time, not that it was true.

**Cache key vs packet hash.** The packet hash covers everything the model saw. The cache
key deliberately excludes chain head blocks, which advance on every request; without that
distinction every call would look new and burn quota. The panel prints both, so the
tolerance is visible rather than hidden.

### Provider configuration

| Variable | Default | Notes |
|---|---|---|
| `ARC_AI_PROVIDER` | `minimax` | `mock` exercises the pipeline without spending quota; mock output is labelled as such |
| `MINIMAX_API_KEY` | — | Or `ARC_AI_API_KEY`. Subscription and pay-as-you-go keys both work |
| `ARC_AI_BASE_URL` | `https://api.minimax.cn/anthropic` | |
| `ARC_AI_PROTOCOL` | `anthropic` | The documented recommended route; `openai` uses `/chat/completions` |
| `ARC_AI_MODEL_QUICK` | `MiniMax-M2.7-highspeed` | Model used by the single public research report |
| `ARC_AI_MAX_TOKENS_QUICK` | `2200` | Maximum report output |
| `ARC_AI_PACKET_CHARS_QUICK` | `16000` | Maximum evidence packet size |

The public path omits the provider-specific thinking-effort field. The Anthropic-compatible
route authenticates with `Authorization: Bearer`, not `x-api-key`.

## Visual language

The interface is matched to arc.io rather than invented, using the design tokens
that site publishes:

| Token | Value | Applied to |
|---|---|---|
| protocol navy | `#1b3158` | Headings, primary text |
| near-black | `#12192b` | Primary buttons, active nav, toast |
| validator blue | `#2f578c` | Links, "proven" state, dark score card |
| sky sync | `#acc6e9` | Hero wash, "fetched" state |
| static ether | `#d5e0e7` | Quiet chips and code backgrounds |
| amber | `#e9a13f` | Accent, gaps, zeroed score rows |
| rust | `#d14424` | Failures and gate stops |
| hero wash | `#a7d9fa → #fbf5f0` | Hero gradient (extra mid stops, since our hero is shorter) |
| radii | `8px` base | Buttons, chips, small cards; `16px` for feature cards |

Type pairing: DM Sans for body, Space Grotesk for display, Space Mono for
eyebrows and receipts. All three are self-hosted — see `fonts/README.md` for
licensing. **No external stylesheet, font or image is requested at runtime.**

Semantic states reuse that palette instead of importing an unrelated set:
verified/proven is validator blue, fetched is sky, gap is amber, failed is rust.

## Endpoints and chain facts

| | Arc mainnet | Arc testnet |
|---|---|---|
| RPC | `https://rpc.mainnet.arc.io` | `https://rpc.testnet.arc.io` |
| chainId | 5042 (`0x13b2`) | 5042002 (`0x4cef52`) |
| Explorer | `https://explorer.arc.io` | `https://explorer.testnet.arc.io` |
| Gas token | USDC (18 decimals native) | USDC (18 decimals native) |

Override with `ARC_RPC_MAINNET` / `ARC_RPC_TESTNET`.

Two traps this code handles explicitly:

1. `rpc.testnet.arc.network` is an undocumented **testnet-only alias**; the canonical
   hosts are on `.arc.io`. `rpc.mainnet.arc.network` does not resolve.
2. Native USDC gas accounting is **18 decimals** while the ERC-20 USDC interface
   (`0x3600…0000`) reports **6 decimals**. Same balance — never render them as two rows.

## Security posture

- Probe targets are resolved first and refused if they are loopback, RFC1918,
  link-local, reserved, multicast or unspecified (basic SSRF protection). Redirects are
  re-checked at every hop.
- All fetched text is escaped before it reaches the DOM, since page titles and
  descriptions are untrusted third-party content.

## Files

| File | Role |
|---|---|
| `server.py` | Stdlib HTTP server, Arc RPC client, probe engine, scoring |
| `index.html` | Views: Overview, Search, Roadmap |
| `styles.css` | Self-contained stylesheet and bundled `@font-face` rules |
| `app.js` | Fetches the API, renders receipts and manages recent searches |
| `fonts/` | Self-hosted DM Sans / Space Grotesk / Space Mono + OFL licences |
| `.env.example` | Server environment template; the real `.env` is git-ignored |
| `reports/` | Runtime analysis log (append-only hash chain), git-ignored |
| `shots/` | Headless-Chrome renders used to verify the UI |

There is no wallet, private key, custody or paid placement in the product flow.

## Provenance

Network facts (RPC hosts, chain IDs, contract addresses, the decimal trap) were verified
against live Arc endpoints and are filed with sources under `../arc-research/`.
