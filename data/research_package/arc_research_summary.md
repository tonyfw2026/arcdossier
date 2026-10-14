# ArcDossier v0.5｜管理层研究摘要

研究日期：2026-10-14；Arc Mainnet Chain ID 5042。

## 数量与去重

- 原始两榜单条目：30 条（保留全部原始发现记录）。
- Token 合约研究项目：27 个；新增官方 Arc Network 1 个；七模块研究实体共 28 个。
- 合并：ARGUS V3/V4 同 token 两池；CRCL V3/V4 视为同 token 但保留映射待进一步校验；UpSideDownCat 16H 新池临时归并待复核。
- 不合并：The Duke of Arc 与 Duke 两个完全不同 CA。

## 7 个补充合约地址

| 代币身份 | 用户提供 CA | 本轮证据级别 |
|---|---|---|
| Kairo | `0x3EAd4E80e9e5bC0e01682D7Ee74C4881b040D3EA` | confirmed_by_independent_explorer_not_rpc |
| Arcus Network | `0xB7C934FF18730c24e6113BB4bC5A68feEf16fD29` | confirmed_by_official_project_website_not_rpc |
| ARCAT | `0x07704B06981eA962b87296362a1281484d160000` | confirmed_by_official_project_website_not_rpc |
| LONG | `0x2164bB17a2D38c1b5170E987b2c0416DF1EFc752` | confirmed_by_independent_explorer_not_rpc |
| The Duke of Arc | `0x41358Defd0dedc90528b3F1835715E907B686e6a` | market_and_user_correlated_not_rpc |
| Duke | `0xe6a2476f33Ec1566288AA32Ec3319A6B77DD1E3B` | user_supplied_unverified |
| Bozo.fun | `0x25b2F893EC15808dBDc542938A4A091ece7AEC44` | user_supplied_unverified |

## 公链重要结论

Arc 2026-09-16 公共主网上线，Chain ID=5042，EVM 兼容，USDC 原生支付 Gas，许可制 PoA 验证者；面向跨境支付、RWA、交易、AI Agent。2026-09-16 官方声明已完成 ARC 创世铸造 100 亿枚，但未宣布公开上线，不能把任何 DEX 代币认定为官方 ARC。官方透露 PoS 2027 探索方向、选择性隐私和 Network Sectors 路线图，均不应描述为已经全面上线。

## 与代币经济直接有关的独特观察

- Kairo：官网记载 staking pool 机制涉及买入并销毁 KAIRO；Perps 文档提及 0.03% builder fee，暂不可直接外推代币收入。
- Arcus：官网确认 Arc CA、10 亿枚供给，并表示计划从 USDC 平台收入中给 holder pool 分配；具体 share 与 distribution 均 TBA。
- Arclight：官方文档说明非托管 Uniswap V3/V4 流动性建仓，是否价值捕获到 ARCLIGHT 代币另需确认。
- LONG：独立浏览器可观察代理合约以及历史集中度，数据不代表最新持仓。
- ARCAT：项目官网提供 CA，但声称用 ARC 支付网络 Gas，与 Arc 官方现行 USDC Gas 不一致。
- CRCL/USDC ticker：官方身份最容易混淆，交易前必须按 Token 合约核对。

## 四个紧要后续核查

1. 逐一向 Arc RPC 验证全部 27 个 Token 的 bytecode、owner/roles、mint/pause/upgrade，以及 pool `token0/token1`。
2. 回查 BOZO 7H 新池、UpSideDownCat 16H 新池、第二个 Duke 对应池地址。
3. 以合约事件测定项目净收入/独立真实用户/回购销毁，生成有区块高度和时间戳的缓存。
4. 将 ARC 网络数据与项目业务指标、Meme 热度分别展示，避免投资判断混淆。

## 下载结构说明

`arc_projects.json`：28 实体七模块数据+30 发现记录；`arc_research.md`：完整研究；`arc_market_snapshot.json`：非实时市场/发现记录；`arc_project_sources.json`：逐条来源可信等级；本文件：汇总结论。

## 关键参考链接

- Arc 主网公告：https://www.arc.io/pressroom/circle-launches-arc-mainnet-an-economic-operating-system-for-the-internet
- Arc ARC Token 白皮书：https://www.arc.io/arc-token-whitepaper
- Kairo 官方：https://kairo.market/
- Arcus Token：https://arcusnetwork.co/arcus
- ARCAT 官方：https://arcat.online/
- LONG 代理合约：https://arc-scan.org/address/0x2164bb17a2d38c1b5170e987b2c0416df1efc752/contract
