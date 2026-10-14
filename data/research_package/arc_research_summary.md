# ArcDossier v0.5 — Executive Research Summary

Research date: 2026-10-14 · Arc Mainnet Chain ID: 5042.

## Coverage and deduplication

- Raw entries from two discovery lists: 30. Every original discovery record is retained.
- Token-contract projects: 27. One official Arc Network record was added, for 28 researched entities in total.
- Merged: ARGUS V3 and V4 are two pools for the same token; CRCL V3 and V4 are treated as the same candidate token while the mapping awaits further verification; the 16-hour UpSideDownCat pool is provisionally grouped pending review.
- Kept separate: The Duke of Arc and Duke use two different contract addresses.

## Seven supplementary contract addresses

| Token identity | User-provided contract | Evidence level in this review |
|---|---|---|
| Kairo | `0x3EAd4E80e9e5bC0e01682D7Ee74C4881b040D3EA` | confirmed_by_independent_explorer_not_rpc |
| Arcus Network | `0xB7C934FF18730c24e6113BB4bC5A68feEf16fD29` | confirmed_by_official_project_website_not_rpc |
| ARCAT | `0x07704B06981eA962b87296362a1281484d160000` | confirmed_by_official_project_website_not_rpc |
| LONG | `0x2164bB17a2D38c1b5170E987b2c0416DF1EFc752` | confirmed_by_independent_explorer_not_rpc |
| The Duke of Arc | `0x41358Defd0dedc90528b3F1835715E907B686e6a` | market_and_user_correlated_not_rpc |
| Duke | `0xe6a2476f33Ec1566288AA32Ec3319A6B77DD1E3B` | user_supplied_unverified |
| Bozo.fun | `0x25b2F893EC15808dBDc542938A4A091ece7AEC44` | user_supplied_unverified |

## Key Arc Network findings

Arc launched its public mainnet on 2026-09-16. It uses Chain ID 5042, is EVM-compatible, charges Gas in native USDC, and currently uses a permissioned PoA validator set. Its stated focus includes cross-border payments, RWA, trading, and AI agents. On the same date, Circle announced the genesis mint of 10 billion ARC, but not a public token launch. No DEX token should therefore be identified as the official ARC token. Official materials describe PoS exploration for 2027, selective privacy, and Network Sectors as roadmap items rather than fully live capabilities.

## Token-economics observations

- Kairo: the website describes a staking-pool mechanism involving KAIRO purchases and burns. Perpetuals documentation mentions a 0.03% builder fee, but this cannot yet be treated as token revenue.
- Arcus: the official website confirms its Arc contract and a 1 billion supply, and describes a future holder pool funded by USDC platform revenue. The share and distribution method remain TBA.
- Arclight: official documentation describes non-custodial Uniswap V3/V4 liquidity-position construction. Whether this creates value for ARCLIGHT holders remains unverified.
- LONG: an independent explorer shows a proxy contract and historical concentration data. These figures are not a current holder snapshot.
- ARCAT: the project website publishes a contract address but says ARC pays network Gas, which conflicts with Arc's current official USDC Gas model.
- CRCL and USDC tickers: these identities are especially easy to confuse. Users must verify the exact token contract before interacting.

## Four priority follow-ups

1. Verify bytecode, owner and role controls, mint, pause, upgrade functions, and pool `token0/token1` for all 27 tokens through Arc RPC.
2. Recheck the BOZO 7-hour pool, the UpSideDownCat 16-hour pool, and the pool address associated with the second Duke token.
3. Measure project net revenue, independent real users, and buyback or burn activity from contract events, using cached block heights and timestamps.
4. Present Arc network activity, project business metrics, and Meme attention separately to avoid conflating them in investment decisions.

## Package structure

`arc_projects.json` contains 28 English research profiles and 30 discovery records. `arc_research.md` contains the full English research. `arc_market_snapshot.json` stores non-live market and discovery records. `arc_project_sources.json` stores source classifications for each project. This file summarizes the main findings.

## Key references

- Arc mainnet announcement: https://www.arc.io/pressroom/circle-launches-arc-mainnet-an-economic-operating-system-for-the-internet
- Arc token whitepaper: https://www.arc.io/arc-token-whitepaper
- Kairo official website: https://kairo.market/
- Arcus token page: https://arcusnetwork.co/arcus
- ARCAT official website: https://arcat.online/
- LONG proxy contract: https://arc-scan.org/address/0x2164bb17a2d38c1b5170e987b2c0416df1efc752/contract
