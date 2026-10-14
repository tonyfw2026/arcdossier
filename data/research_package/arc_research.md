# ArcDossier v0.5｜Arc 主网生态全项目知识库与研究汇总
**研究日期：2026-10-14｜Arc Mainnet chain ID 5042｜数据可信度：分层记录**

> 研究覆盖此前两榜单全部 30 条原始记录、按 Token CA 去重后的 27 个逻辑代币项目，以及新增的官方 Arc Network（arc.io）研究对象。这里的“七模块覆盖”不表示每个字段均已核实；未知值如实标为 Unknown。所有市场数值保持非实时报价处理。

## 一、Executive Summary｜关键结论

**一条主线：** Arc 不只是 Meme 新链，而是 Circle 背书的美元稳定币原生结算 L1，已上线主网，价值验证重点应落在真实 USDC 支付、链上经济活动、跨链资金流和已交付应用，而不是 DEX 热度本身。

**三项身份边界：** Arc 官方网络 `arc.io` ≠ 第三方 $ARC 或 $CRCL Meme；Arc 官方原生 USDC ≠ UpSideDownCat ($USDC)；两个 DUKE CA 不同，属于不同 Token。

**一项重要升级：** 用户补充 7 个完整 20-byte CA；KAIRO、ARCUS、ARCAT、LONG 等得到项目官网或独立区块浏览器交叉匹配，但不是本报告进行了 RPC 权限核验。

**项目研究优先级（研究价值，不是买入推荐）：** 重点核对 Kairo、Arcus、Argus、Tolly、Arclight、ArcStocks、Faze、UBI、SolonPad、LONG 是否有持续真实产品交易和 Token 收益兑现。

## 二、身份去重总表：30 条发现 → 27 个 Token 项目 + Arc Network

| 原榜单序号 | 项目 | Symbol | CA / 身份状态 | 处理规则 |
|---:|---|---|---|---|
| 1 | Faze | FAZE | `0x394d38f807ee0027a182216f5e67a15ae441fa2e` | 独立 |
| 2 | Arcflow / AI Flow | AF | `0x75d658f8101fbe6dc217fbba7e20a0312af5fa2e` | 独立 |
| 3 | Argus | ARGUS | `0xeCe5cA8bf9220718E5727754026757512212cb3c` | 独立 |
| 4 | Argus V4 | ARGUS | `0xeCe5cA8bf9220718E5727754026757512212cb3c` | 同 Token 不同池 |
| 5 | Tolly | TOLLY | `0xBc43CE8DEc648EA298C4275559b81D6261c90b67` | 独立 |
| 6 | usdc is cool | COOL | `0xEb64987643db71c76b2a2BE7E723DECC995E5b37` | 独立 |
| 7 | Arclight Finance | ARCLIGHT | `0xa3de1dda14e4b3ce2eee2f8c1e49315effc15be2` | 独立 |
| 8 | Arc-man | ARCMAN | `0x5849Fd68a097B3eE7d87ce88a0fcBb76857648FF` | 独立 |
| 9 | Circle Internet Group · Arc Token | CRCL | `0x2ba0f44bdfc17fba30eda9cdbecb908ca45b043b` | 独立 |
| 10 | UpSideDownCat | USDC | `0x8E98A62a995A50eca9979bfa016f91bf36A8F9D9` | 独立 |
| 11 | Peach | PEACH | `0x082E97908201e376957Fe2FeCf4A129b0c0Ad3B4` | 独立 |
| 12 | UBI.fun | UBI | `0xFA3fFdF775CC3f6ac82Cd258Fb948a8a21e1749e` | 独立 |
| 13 | ArcStocks | ASTOCK | `0x4C9b47Dbd5933aa4574B2c27F82419E4DBBD0222` | 独立 |
| 14 | Polly | POLL | `0xf76b1D00bD3d63A37246B5f512074e864010E33d` | 独立 |
| 15 | oBrain | oBrain | `0x28F986A61E078795639F239675582a12B4cf7F01` | 独立 |
| 16 | Kairo | KAIRO | `0x3EAd4E80e9e5bC0e01682D7Ee74C4881b040D3EA` | 独立 |
| 17 | MEMESPAD | MEMESPAD | `0x0bb3befba323578dad33efb6356c69b557787777` | 独立 |
| 18 | Circle Internet Group · Arc Token V3 | CRCL | `0x2ba0f44bdfc17fba30eda9cdbecb908ca45b043b` | 同 Token 不同池 |
| 19 | Arcanus | ARCANUS | `0x29316DB42fF99f640FD4D1bb169635B6318Cd430` | 独立 |
| 20 | The Duke of Arc | DUKE | `0x41358Defd0dedc90528b3F1835715E907B686e6a` | 独立 |
| 21 | SolonPad | SOLON | `0xd36687146385F7Dc84A18FEA3D00319d39D6d1a0` | 独立 |
| 22 | ArcTools | ARCT | `0x1EA1e4f9A9975F1f6e9c0a9f6e8Ada7a66E6de52` | 独立 |
| 23 | Arcus Network | ARCUS | `0xB7C934FF18730c24e6113BB4bC5A68feEf16fD29` | 独立 |
| 24 | ARCAT | ARCAT | `0x07704B06981eA962b87296362a1281484d160000` | 独立 |
| 25 | Arc Inu | AI | `0xA39C8e2ceB2a0f9D6e9D059f5E470eDfDA691c15` | 独立 |
| 26 | Architects | Architects | `0x8bcb94279FC2c984EC34e0C1f2192df8c69EA4F0` | 独立 |
| 27 | LONG | LONG | `0x2164bB17a2D38c1b5170E987b2c0416DF1EFc752` | 独立 |
| 28 | Duke | DUKE | `0xe6a2476f33Ec1566288AA32Ec3319A6B77DD1E3B` | 独立 |
| 29 | UpSideDownCat new pool 16H | USDC | `0x8E98A62a995A50eca9979bfa016f91bf36A8F9D9` | 暂归并，待池验证 |
| 30 | Bozo.fun | BOZO | `0x25b2F893EC15808dBDc542938A4A091ece7AEC44` | 独立 |

**去重安全规则：** `chain_id + token_address` 定义 Token 唯一性；同一 Token 的 V3/V4 两池只合并项目主体、不删除池；任何 CA 不一致的 Token 即便名字完全相同也分开。第 29 条 UpSideDownCat 的新池证据暂不足，只能 provisional。第 30 条 BOZO 旧池不能冒充截图 7H 新池。

## 三、Arc Network 官方研究（七模块）

### 01 身份与网络
Arc Network（arc.io）由 Circle 生态推动，通过 Arc Network Services LLC 构建和运行；EVM 兼容开放 L1，Arc Mainnet Chain ID 5042，2026-09-16 公共主网上线。官方资料与应用层的同名 ARC/CRCL/USDC 代币不可混淆。当前验证人集合为许可制 PoA。

### 02 产品与商业模式
核心是美元稳定币驱动的金融结算网络：原生 USDC 作为 Gas、确定性亚秒级 Finality、CCTP/Gateway 跨链互通、StableFX、代币化资产、支付与 AI Agent。Circle 将 Arc 与 Agent Stack、Arc Portal、Arc Studio、App Kits 集成。网络使用收费为 USDC；需独立拆分网络手续费、Circle 业务收入和未来可能的 ARC token 价值捕获。

### 03 产品数据与增长
官方 2026-09-16 主网上线声明称首日超过 100 个应用以及 100+ 机构/生态构建参与方，这是官方披露而非逐个链上复核。独立区块浏览器有交易总数、24h 交易、账户、合约、USDC 转账与费用统计接口，但当前检索页面不保证同步时刻；不将检索页缓存数值伪装为实时值。下一轮需固定 block number 与 UTC 时间重取，并分辨交易笔数/独立付费用户/有效经济活动。

### 04 团队背景与融资
发起/支持方为 Circle Internet Group（美股 CRCL），官方新闻稿引用联合创始人兼 CEO Jeremy Allaire。官方列有 BlackRock、DTCC、Mastercard、Visa、Standard Chartered 等参与生态/验证者计划；需要进一步区分「建立合作关系」「验证节点」「实际部署应用」「资本入股」四种关系。未发现 Arc 网络独立融资估值，不能将 Circle 市值当作 Arc 协议 FDV。

### 05 Tokenomics与价值捕获
2026-09-16 Circle 宣布在美国完成 ARC 的 genesis mint、初始供应量 10,000,000,000。官方同时明确：这不构成 ARC 公开发行承诺，ARC 目前未对公众 launch，也不是 Circle 股票或其收益权凭证。白皮书探索 PoA→PoS（目标 2027）的 staking/delegation、治理、USDC 费用转换为 ARC 奖励/销毁机制；实施规则、分配、开放交易、代币价格及 FDV 均不应当作现状。Arc 交易费仍使用 USDC。

### 06 Arc生态定位与竞争
Arc 与 Ethereum L2、Solana、Tempo、Stable 等结算网络竞争，在支付、跨境结算、RWA 和智能体经济上依托 Circle USDC、CCTP/CPN 渠道与机构客户分发。优势是原生 USDC 费用、EVM 工具和机构入口；劣势/风险包括许可验证者中心化、USDC 依赖、竞争链补贴、合规审查，以及 DeFi/Meme 活跃度与机构真实交易量分离。

### 07 近期进展与注意力
2026-09-16 公共主网正式上线；同日 ARC genesis mint 100 亿、官方宣布未来 PoS/Privacy/Network Sectors 路线图。2026-10-12 官方发布交易所入金/出金集成指南，说明单区块确定性终局性、USDC 原生资产与转账事件整合；Privacy Sector、Payment Sector >100K TPS、Agent Sector 均为规划，不能记作当前已经上线能力。

### Arc 官方网络指标的取数规范
- 官方入口：https://www.arc.io/；主网统计：https://explorer.arc.io/stats；官方声明：https://www.arc.io/pressroom/circle-launches-arc-mainnet-an-economic-operating-system-for-the-internet。
- 统计字段建议：UTC 区块时间、Blocks/Txns/Successful Txns、独立发送地址（去机器人）、Gas Fees USDC、USDC Transfer Volume、CCTP/CPN 跨链净流入、合约创建、真实 DEX Volume 和 TVL。
- **不能**把“累计交易笔数”直接等同于“真实用户数”；不能把 Circle 公司的企业营收等同于 ARC 代币可分配收入。
- 主网浏览器检索页面存在缓存与延迟；以同一 `block_number`、UTC 时间和公开 API 重取为准，本文没有填入无法独立复核的即时报价。

## 四、27 个 Token 项目逐一七模块研究

### 01. Faze（FAZE）

**分类：** Launchpad ｜ **CA：** `0x394d38f807ee0027a182216f5e67a15ae441fa2e` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 1

**核心摘要：** Arc 上的代币发行及发现方向项目，出现在榜单并存在可检索的交易池。

**01 身份与网络：** Faze（FAZE）属于 Launchpad 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x394d38f807ee0027a182216f5e67a15ae441fa2e。验证状态：third_party_index_not_rpc。发现记录：[1]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 上的代币发行及发现方向项目，出现在榜单并存在可检索的交易池。 发行规模、手续费分润与真实使用者仍需项目合约与交易事件验证。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 发行代币与平台收入之间的价值捕获关系未获独立确认。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Faze 的潜在方向为 Launchpad。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：发行平台竞争激烈，存在刷量、协议佣金口径及代币与业务价值脱钩风险。

**参考来源：** [来源1](https://dexscreener.com/arc/0xd9133187331e20885fd1b4ff2f18b892f94793ddaf808b1db6d4ef29ca58b943)

### 02. Arcflow / AI Flow（AF）

**分类：** AI / Payments ｜ **CA：** `0x75d658f8101fbe6dc217fbba7e20a0312af5fa2e` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 2

**核心摘要：** 面向 AI 模型调用和加密支付流程的 Arc 生态叙事，项目曾以 Arcflow 名称在交易市场出现。

**01 身份与网络：** Arcflow / AI Flow（AF）属于 AI / Payments 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x75d658f8101fbe6dc217fbba7e20a0312af5fa2e。验证状态：third_party_index_not_rpc。发现记录：[2]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** 面向 AI 模型调用和加密支付流程的 Arc 生态叙事，项目曾以 Arcflow 名称在交易市场出现。 多模型访问与支付产品的真实订单、付费用户、调用量尚未独立核查。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** AF 与平台收入、模型消费、回购的关系待项目方公开合约及条款。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Arcflow / AI Flow 的潜在方向为 AI / Payments。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：应警惕品牌更名和代币历史身份映射错误。

**参考来源：** [来源1](https://dexscreener.com/arc/0x1c0523377296238f6a2fd25cb3b15f75e280eb330ad29f843b974eec264dfe31)

### 03. Argus（ARGUS）

**分类：** Launchpad / DEX ｜ **CA：** `0xeCe5cA8bf9220718E5727754026757512212cb3c` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 3, 4

**核心摘要：** Arc 生态发行与交易基础设施，已有 V3 和 V4 两条榜单池记录，属于同一 token 的不同交易池。

**01 身份与网络：** Argus（ARGUS）属于 Launchpad / DEX 研究分类；Arc Mainnet Chain ID=5042；Token CA=0xeCe5cA8bf9220718E5727754026757512212cb3c。验证状态：third_party_index_not_rpc。发现记录：[3, 4]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 生态发行与交易基础设施，已有 V3 和 V4 两条榜单池记录，属于同一 token 的不同交易池。 产品自述采用 bonding curve 发行和可配置费用，但发行量、净收入、链上活跃发行用户仍待事件级统计。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 可配置费用用途须看真实合约路由；不能由宣传直接推出持续的 ARGUS 买盘。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Argus 的潜在方向为 Launchpad / DEX。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：需防范版本升级、V3/V4 分池流动性和池迁移误判。

**参考来源：** [来源1](https://dexscreener.com/arc/0x6a3bacaa6493734c1ac221ebf42cf530a96c1e02) ｜ [来源2](https://argus.world/)

### 04. Tolly（TOLLY）

**分类：** Launchpad / Trading ｜ **CA：** `0xBc43CE8DEc648EA298C4275559b81D6261c90b67` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 5

**核心摘要：** Arc 上的交易终端、发行与行情监控产品叙事，存在独立操作指南。

**01 身份与网络：** Tolly（TOLLY）属于 Launchpad / Trading 研究分类；Arc Mainnet Chain ID=5042；Token CA=0xBc43CE8DEc648EA298C4275559b81D6261c90b67。验证状态：third_party_index_not_rpc。发现记录：[5]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 上的交易终端、发行与行情监控产品叙事，存在独立操作指南。 已找到产品说明和交易路径；活跃交易者、真实发行量、协议净收入尚未链上审计。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 可查阅 Tolly 产品功能说明，但不同域名相关性未完全确认，不可直接将其中费率数据纳入本 token 的收入模型。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 另有 tollylabs.org 自称 1% 交易费用含 9% 用于买入并移出 TOLLY 流通；此域名与 tollylabs.com 的身份映射尚待核对，不将其作为已证实代币经济。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Tolly 的潜在方向为 Launchpad / Trading。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：不同域名和费率文档存在身份关联核验需求，暂不合并为已证实经济模型。

**参考来源：** [来源1](https://dexscreener.com/arc/0x162df51c504e7b8321e07387932f333d9be16a72) ｜ [来源2](https://tollylabs.com/guide) ｜ [来源3](https://www.tollylabs.org/)

### 05. usdc is cool（COOL）

**分类：** Meme ｜ **CA：** `0xEb64987643db71c76b2a2BE7E723DECC995E5b37` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 6

**核心摘要：** 围绕 USDC 文化叙事的 Arc Meme 代币；不是 USDC 稳定币本身。

**01 身份与网络：** usdc is cool（COOL）属于 Meme 研究分类；Arc Mainnet Chain ID=5042；Token CA=0xEb64987643db71c76b2a2BE7E723DECC995E5b37。验证状态：third_party_index_not_rpc。发现记录：[6]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** 围绕 USDC 文化叙事的 Arc Meme 代币；不是 USDC 稳定币本身。 可见 DEX 池，但持续产品、营收、产品用户数据缺乏证据。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 未发现可验证的代币收入分配或回购机制。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** usdc is cool 的潜在方向为 Meme。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：与 Circle/USDC 的叙事关联不代表其获得 Circle 官方授权。

**参考来源：** [来源1](https://dexscreener.com/arc/0x40732e01ba7a829dea44f51a10e7c58cd9f37765)

### 06. Arclight Finance（ARCLIGHT）

**分类：** DeFi / Liquidity ｜ **CA：** `0xa3de1dda14e4b3ce2eee2f8c1e49315effc15be2` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 7

**核心摘要：** 定位于 Uniswap V3/V4 集中流动性管理和分层仓位构建；官网说明用户持有相应仓位 NFT。

**01 身份与网络：** Arclight Finance（ARCLIGHT）属于 DeFi / Liquidity 研究分类；Arc Mainnet Chain ID=5042；Token CA=0xa3de1dda14e4b3ce2eee2f8c1e49315effc15be2。验证状态：third_party_index_not_rpc。发现记录：[7]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** 定位于 Uniswap V3/V4 集中流动性管理和分层仓位构建；官网说明用户持有相应仓位 NFT。 官方描述 Builder 不托管仓位，单次交易铸造多个头寸；但用户数、费用与管理资产没有独立可复现聚合值。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 官方对 Uniswap V3/V4 梯形 LP 建仓路径有具体说明，但真实 TVL、仓位 NFT 总数、收费额与用户留存尚未量化。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 文档称 owner 可调整构建费 0–100 bps 和 treasury；ARCLIGHT 代币如何捕获该费用未证实。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Arclight Finance 的潜在方向为 DeFi / Liquidity。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：需核实网页对应的代币 CA，以及 Builder 合约的权限和策略尾部风险。

**参考来源：** [来源1](https://dexscreener.com/arc/0xc510e54d5cee9f8512280f9d3317431aa1fbf78d1a492eac7483cb0a0749b253) ｜ [来源2](https://arclight.finance/docs/how-it-works)

### 07. Arc-man（ARCMAN）

**分类：** Meme ｜ **CA：** `0x5849Fd68a097B3eE7d87ce88a0fcBb76857648FF` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 8

**核心摘要：** Arc 生态社区/meme 资产，榜单与交易池可检索。

**01 身份与网络：** Arc-man（ARCMAN）属于 Meme 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x5849Fd68a097B3eE7d87ce88a0fcBb76857648FF。验证状态：third_party_index_not_rpc。发现记录：[8]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 生态社区/meme 资产，榜单与交易池可检索。 未见独立验证的可持续产品或协议收入。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 买回、销毁和持有人收益机制未证实。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Arc-man 的潜在方向为 Meme。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：同名或迁移 token 可能存在，严格按 CA 辨识。

**参考来源：** [来源1](https://dexscreener.com/arc/0xa3abdb2721cd343da530ff6fd0ad73f3caa77163ea2fb8206847249f9bba57d5)

### 08. Circle Internet Group · Arc Token（CRCL）

**分类：** Brand / Synthetic Claim ｜ **CA：** `0x2ba0f44bdfc17fba30eda9cdbecb908ca45b043b` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 9, 18

**核心摘要：** 第三方市场中自称 Circle Internet Group/Arc Token 的 CRCL 资产，不等于 Circle 上市股票或 Circle 授权代币。

**01 身份与网络：** Circle Internet Group · Arc Token（CRCL）属于 Brand / Synthetic Claim 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x2ba0f44bdfc17fba30eda9cdbecb908ca45b043b。验证状态：third_party_index_not_rpc。发现记录：[9, 18]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** 第三方市场中自称 Circle Internet Group/Arc Token 的 CRCL 资产，不等于 Circle 上市股票或 Circle 授权代币。 市场交易不构成代币化股权的权属、储备、托管或可赎回证明。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 无权将其估值视作 Circle 公司股权、ARC 官方资产或现金流权益。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Circle Internet Group · Arc Token 的潜在方向为 Brand / Synthetic Claim。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：高强度身份与品牌混淆；Circle 股票代码 CRCL、Arc 可能的 ARC 代币与该同名代币是不同概念。

**参考来源：** [来源1](https://dexscreener.com/arc/0x9634aa66a6b8d0f734a7865549287a598974838a35ea3c3ca56935151220afa6) ｜ [来源2](https://www.arc.io/network) ｜ [来源3](https://www.arc.io/arc-token-whitepaper)

### 09. UpSideDownCat（USDC）

**分类：** Meme / Symbol Collision ｜ **CA：** `0x8E98A62a995A50eca9979bfa016f91bf36A8F9D9` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 10, 29

**核心摘要：** 使用 USDC 作为交易代码的 Meme 代币，既不是 Circle 官方原生 USDC，也不应当与稳定币资产合并。

**01 身份与网络：** UpSideDownCat（USDC）属于 Meme / Symbol Collision 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x8E98A62a995A50eca9979bfa016f91bf36A8F9D9。验证状态：third_party_index_not_rpc。发现记录：[10, 29]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** 使用 USDC 作为交易代码的 Meme 代币，既不是 Circle 官方原生 USDC，也不应当与稳定币资产合并。 存在市场行情池，但没有真实金融服务或稳定币储备证明。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 不是受 Circle 赎回保障的 1 美元 USDC；任何价格稳定叙事均不能默认成立。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** UpSideDownCat 的潜在方向为 Meme / Symbol Collision。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：Ticker 冒用/冲突极易造成资金误转和误购，必须高亮 CA。

**参考来源：** [来源1](https://dexscreener.com/arc/0x54d5fe8ee7a9546ce74ebe06c1d040defb7757410a627d4793d62a77eaaae4bf) ｜ [来源2](https://www.arc.io/blog/usdc-for-every-action-how-arc-simplifies-building-onchain)

### 10. Peach（PEACH）

**分类：** Meme ｜ **CA：** `0x082E97908201e376957Fe2FeCf4A129b0c0Ad3B4` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 11

**核心摘要：** Arc 上的 PEACH 代币与交易池可检索，项目产品定位资料不足。

**01 身份与网络：** Peach（PEACH）属于 Meme 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x082E97908201e376957Fe2FeCf4A129b0c0Ad3B4。验证状态：third_party_index_not_rpc。发现记录：[11]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 上的 PEACH 代币与交易池可检索，项目产品定位资料不足。 可证事实主要是市场发现记录，真实用户、功能及收入未发现独立统计。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 供给、锁仓、归集、回购与费用分配待核。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Peach 的潜在方向为 Meme。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：信息稀薄、流动性及代币权限需要单独验证。

**参考来源：** [来源1](https://dexscreener.com/arc/0x10d5e420fac5d0159279b324d9fb93a4d541435081125e2c6997945ad3ed658f)

### 11. UBI.fun（UBI）

**分类：** Launchpad ｜ **CA：** `0xFA3fFdF775CC3f6ac82Cd258Fb948a8a21e1749e` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 12

**核心摘要：** Arc 生态发行/启动平台，UBI 出现在主网市场发现记录。

**01 身份与网络：** UBI.fun（UBI）属于 Launchpad 研究分类；Arc Mainnet Chain ID=5042；Token CA=0xFA3fFdF775CC3f6ac82Cd258Fb948a8a21e1749e。验证状态：third_party_index_not_rpc。发现记录：[12]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 生态发行/启动平台，UBI 出现在主网市场发现记录。 应核查真实发行项目数量、参与者、成功迁移率、收费口径，当前未能系统采样。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 平台收费是否直接流入 UBI 持有者或回购地址缺乏硬证据。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** UBI.fun 的潜在方向为 Launchpad。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：发行平台可能受短期 Meme 热潮驱动，需去除机器人和自刷交易。

**参考来源：** [来源1](https://dexscreener.com/arc/0xcb39398862db54384d5bc8c98077e012a5ae7cb1dbc3c6fcaf256c5e10568ab8) ｜ [来源2](https://ubi.fun/)

### 12. ArcStocks（ASTOCK）

**分类：** RWA / StockFi ｜ **CA：** `0x4C9b47Dbd5933aa4574B2c27F82419E4DBBD0222` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 13

**核心摘要：** 围绕 Arc、股票价格敞口和 StockFi 的市场项目，已在 DEX 存在交易。

**01 身份与网络：** ArcStocks（ASTOCK）属于 RWA / StockFi 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x4C9b47Dbd5933aa4574B2c27F82419E4DBBD0222。验证状态：third_party_index_not_rpc。发现记录：[13]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** 围绕 Arc、股票价格敞口和 StockFi 的市场项目，已在 DEX 存在交易。 未独立确认可赎回真实股票、证券托管、牌照或净资产储备。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 不应由 ASTOCK 代币交易量推断公司股权或协议收入份额。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** ArcStocks 的潜在方向为 RWA / StockFi。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：RWA 叙事需最高等级权属和储备核验。

**参考来源：** [来源1](https://dexscreener.com/arc/0x1bb5c22ae4560dc887164d96ebeaa756130948314ce132fee3c8d14e5b95758b)

### 13. Polly（POLL）

**分类：** Unclassified ｜ **CA：** `0xf76b1D00bD3d63A37246B5f512074e864010E33d` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 14

**核心摘要：** Arc 市场中以 POLL 标识的资产，在 Synthra 交易池中有市场记录；具体产品功能尚无可靠材料。

**01 身份与网络：** Polly（POLL）属于 Unclassified 研究分类；Arc Mainnet Chain ID=5042；Token CA=0xf76b1D00bD3d63A37246B5f512074e864010E33d。验证状态：third_party_index_not_rpc。发现记录：[14]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 市场中以 POLL 标识的资产，在 Synthra 交易池中有市场记录；具体产品功能尚无可靠材料。 没有可独立验证的产品用户、协议收入或 TVL。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** Tokenomics 未确认。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Polly 的潜在方向为 Unclassified。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：不要根据名称或流动池推断预测市场/治理功能。

**参考来源：** [来源1](https://dexscreener.com/arc/0x5bc5ced48bec9260c8d626269f44e22808b8d2c1)

### 14. oBrain（oBrain）

**分类：** AI / Agent ｜ **CA：** `0x28F986A61E078795639F239675582a12B4cf7F01` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 15

**核心摘要：** Arc 的 AI/Agent 叙事项目，先前研究识别出交易池及项目入口。

**01 身份与网络：** oBrain（oBrain）属于 AI / Agent 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x28F986A61E078795639F239675582a12B4cf7F01。验证状态：third_party_index_not_rpc。发现记录：[15]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 的 AI/Agent 叙事项目，先前研究识别出交易池及项目入口。 需量化真实智能体调用、订阅收入、支付量、活跃集成而非仅观察价格。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 项目代币与 AI 业务收入的捕获关系待证。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** oBrain 的潜在方向为 AI / Agent。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：容易将概念网站或聊天入口误作商业化验证。

**参考来源：** [来源1](https://dexscreener.com/arc/0xcb884ecb09388944a1afd5e1b74c42a4dfb2f93ec38288ce20c966ec233a0d52)

### 15. Kairo（KAIRO）

**分类：** DeFi / Prediction / Perps ｜ **CA：** `0x3EAd4E80e9e5bC0e01682D7Ee74C4881b040D3EA` ｜ **身份状态：** `confirmed_by_independent_explorer_not_rpc` ｜ **原始发现记录：** 16

**核心摘要：** Arc 上集合预测市场、USDC 交易、代币发行、永续合约接入和 Agent 的产品体系，由 Proodos Group BV 运营界面。

**01 身份与网络：** Kairo（KAIRO）属于 DeFi / Prediction / Perps 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x3EAd4E80e9e5bC0e01682D7Ee74C4881b040D3EA。验证状态：confirmed_by_independent_explorer_not_rpc。发现记录：[16]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 上集合预测市场、USDC 交易、代币发行、永续合约接入和 Agent 的产品体系，由 Proodos Group BV 运营界面。 项目官网介绍 YES/NO 预测市场、Swap、Launch、Agent；Perps 依赖外部交易场所及 Circle CCTP，现有不同页面对上线状态和结算路径描述不一致，需实际交易验证。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 产品官网列出 KAIRO 预测市场、Launch、Swap、Lending/Stake、Perps 和 Agent；但缺少按合约复算的累计成交额、实际付费用户、净收入。Perps 不同页面对是否完全 Arc 原生结算说法不一致。

**04 团队背景与融资：** 官网界面运营主体自述为 Proodos Group BV；项目融资金额及创始人履历暂无可核实公开证据。

**05 Tokenomics与价值捕获：** 官网展示 KAIRO staking pool 的 Buy→Burn→Create 机制，受项目方配置触发；KAIRO Perps 文档声明 0.03% builder fee，不能直接推断全部手续费分配给持币者。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Kairo 的潜在方向为 DeFi / Prediction / Perps。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：衍生品清算、跨链结算/预言机、产品宣传口径冲突与未获得金融监管许可；官网写明未获得相关监管批准。

**参考来源：** [来源1](https://dexscreener.com/arc/0xe59c7fada87c866cffc9261c4e7cb19848f0f3db) ｜ [来源2](https://kairo.market/) ｜ [来源3](https://kairo.market/docs) ｜ [来源4](https://kairo.market/docs/perps) ｜ [来源5](https://arc-scan.org/address/0x3ead4e80e9e5bc0e01682d7ee74c4881b040d3ea/logs)

### 16. MEMESPAD（MEMESPAD）

**分类：** Launchpad ｜ **CA：** `0x0bb3befba323578dad33efb6356c69b557787777` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 17

**核心摘要：** Arc 上的 meme token 发行叙事项目，第三方行情/区块浏览器索引出现该合约。

**01 身份与网络：** MEMESPAD（MEMESPAD）属于 Launchpad 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x0bb3befba323578dad33efb6356c69b557787777。验证状态：third_party_index_not_rpc。发现记录：[17]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 上的 meme token 发行叙事项目，第三方行情/区块浏览器索引出现该合约。 平台发行数量、费用、真实参与用户与迁移效果尚无系统独立数据。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 代币是否分享发行平台费用未确认。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** MEMESPAD 的潜在方向为 Launchpad。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：需先补齐当前精确交易池和官方社交的可信映射。

**参考来源：** [来源1](https://dexscreener.com/arc)

### 17. Arcanus（ARCANUS）

**分类：** Unclassified ｜ **CA：** `0x29316DB42fF99f640FD4D1bb169635B6318Cd430` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 19

**核心摘要：** ARCANUS 是 Arc 主网市场中可定位的交易代币，但可靠产品定义资料不足。

**01 身份与网络：** Arcanus（ARCANUS）属于 Unclassified 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x29316DB42fF99f640FD4D1bb169635B6318Cd430。验证状态：third_party_index_not_rpc。发现记录：[19]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** ARCANUS 是 Arc 主网市场中可定位的交易代币，但可靠产品定义资料不足。 不能从 Token 存在推算 TVL、活跃用户或营收。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 经济模型与持币权益未独立证实。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Arcanus 的潜在方向为 Unclassified。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：识别来源单一，谨防营销信息与协议实际运行混同。

**参考来源：** [来源1](https://dexscreener.com/arc/0xd71e15a5c45a204f5228d68165925741efa79995d2671a9e291e6e5cffcc89fc)

### 18. The Duke of Arc（DUKE）

**分类：** Meme / Community ｜ **CA：** `0x41358Defd0dedc90528b3F1835715E907B686e6a` ｜ **身份状态：** `market_and_user_correlated_not_rpc` ｜ **原始发现记录：** 20

**核心摘要：** The Duke of Arc 是使用 DUKE Ticker 的一个独立 Arc 代币，与另一项名为 Duke 的代币不同。

**01 身份与网络：** The Duke of Arc（DUKE）属于 Meme / Community 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x41358Defd0dedc90528b3F1835715E907B686e6a。验证状态：market_and_user_correlated_not_rpc。发现记录：[20]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** The Duke of Arc 是使用 DUKE Ticker 的一个独立 Arc 代币，与另一项名为 Duke 的代币不同。 项目侧资料显示存在社区接管叙事；没有已证实的产品营收和用户留存数据。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 未见可验证回购/收入分配。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** The Duke of Arc 的潜在方向为 Meme / Community。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：两个 DUKE 具有不同 CA，绝不因 symbol 相同而合并。

**参考来源：** [来源1](https://dexscreener.com/arc/0xd86a9e58d668acc7c13bd547f9fa5cc113ae0083a9fc39f97aab857349ee343d)

### 19. SolonPad（SOLON）

**分类：** Launchpad / RWA Narrative ｜ **CA：** `0xd36687146385F7Dc84A18FEA3D00319d39D6d1a0` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 21

**核心摘要：** Arc 生态发行平台，项目叙事涉及 RWA 和 token 启动。

**01 身份与网络：** SolonPad（SOLON）属于 Launchpad / RWA Narrative 研究分类；Arc Mainnet Chain ID=5042；Token CA=0xd36687146385F7Dc84A18FEA3D00319d39D6d1a0。验证状态：third_party_index_not_rpc。发现记录：[21]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 生态发行平台，项目叙事涉及 RWA 和 token 启动。 平台实际募资项目、用户、资产证明与收益分配尚未充分核实。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** SOLON 的价值捕获与协议费去向未形成独立证据。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** SolonPad 的潜在方向为 Launchpad / RWA Narrative。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：避免将 RWA 营销内容等同于实际资产托管。

**参考来源：** [来源1](https://dexscreener.com/arc/0xe4c4b7da3706193e7bf6e7b236156718a5856bc6d6866440661969ae3dcb0a77)

### 20. ArcTools（ARCT）

**分类：** Infrastructure / Tooling ｜ **CA：** `0x1EA1e4f9A9975F1f6e9c0a9f6e8Ada7a66E6de52` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 22

**核心摘要：** Arc 链上工具类项目，在 DexScreener 存在交易池记录。

**01 身份与网络：** ArcTools（ARCT）属于 Infrastructure / Tooling 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x1EA1e4f9A9975F1f6e9c0a9f6e8Ada7a66E6de52。验证状态：third_party_index_not_rpc。发现记录：[22]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 链上工具类项目，在 DexScreener 存在交易池记录。 实际 API 调用、付费席位和数据收入未能审计。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** ARCT 是否用于支付、质押或收入分享待查。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** ArcTools 的潜在方向为 Infrastructure / Tooling。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：历史同名或冲突 CA 需留独立候选而非覆盖主记录。

**参考来源：** [来源1](https://dexscreener.com/arc/0xf89005ccf237a59eeee1521e74b15c7d8d022ab7)

### 21. Arcus Network（ARCUS）

**分类：** AI / x402 Payments ｜ **CA：** `0xB7C934FF18730c24e6113BB4bC5A68feEf16fD29` ｜ **身份状态：** `confirmed_by_official_project_website_not_rpc` ｜ **原始发现记录：** 23

**核心摘要：** Arc 原生的 AI Agent x402 支付 Facilitator；项目官网发布 Arc Mainnet 合约地址和 10 亿枚总量。

**01 身份与网络：** Arcus Network（ARCUS）属于 AI / x402 Payments 研究分类；Arc Mainnet Chain ID=5042；Token CA=0xB7C934FF18730c24e6113BB4bC5A68feEf16fD29。验证状态：confirmed_by_official_project_website_not_rpc。发现记录：[23]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 原生的 AI Agent x402 支付 Facilitator；项目官网发布 Arc Mainnet 合约地址和 10 亿枚总量。 官网展示 x402 服务能力，但真实代理支付笔数、已收 USDC 手续费、独立付费代理数尚未公开审计。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 官方提供 x402 示例及测试网/主网入门材料，业务量、实际结算笔数、净 USDC 手续费以及分润支付交易均待独立量化。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 项目官网宣称未来部分 USDC 业务收入流入 ARCUS 持有者池，但明确 Holder Revenue Share: TBA，Distribution: TBA；不能将计划当作现有 APR。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Arcus Network 的潜在方向为 AI / x402 Payments。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：收入分润为未确定条款、价值捕获落地尚待链上支付与分配记录证实。

**参考来源：** [来源1](https://dexscreener.com/arc/0x5367c6a97ab3f214f2cf98592e8c3cd9892751a1d4abafc4cffbf9cdd4dd0411) ｜ [来源2](https://arcusnetwork.co/arcus)

### 22. ARCAT（ARCAT）

**分类：** Meme ｜ **CA：** `0x07704B06981eA962b87296362a1281484d160000` ｜ **身份状态：** `confirmed_by_official_project_website_not_rpc` ｜ **原始发现记录：** 24

**核心摘要：** Arc 上的猫主题 Meme 代币。项目官网提供与用户补充一致的合约地址。

**01 身份与网络：** ARCAT（ARCAT）属于 Meme 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x07704B06981eA962b87296362a1281484d160000。验证状态：confirmed_by_official_project_website_not_rpc。发现记录：[24]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 上的猫主题 Meme 代币。项目官网提供与用户补充一致的合约地址。 官网自称公平发行、无团队筹码、无税、燃烧 LP，均尚未独立做权限/持仓/LP NFT 级链上审计。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 项目官网列出交易入口和直播面板，但动态交易数字未由本报告独立抓取；社区互动不能等同于真实长期持有人。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 官网将 ARCAT 定义为不具备内在价值的 Meme，未显示可核实的营收权利。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** ARCAT 的潜在方向为 Meme。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：官网 FAQ 声称持有 $ARC 支付 Gas，与 Arc 官方 USDC Gas 模型明显不一致；应当标注网站信息可靠性问题。

**参考来源：** [来源1](https://dexscreener.com/arc/0xdff4298a98486e7755d1045de883fd2fb620b291) ｜ [来源2](https://arcat.online/) ｜ [来源3](https://www.arc.io/blog/usdc-for-every-action-how-arc-simplifies-building-onchain)

### 23. Arc Inu（AI）

**分类：** Meme ｜ **CA：** `0xA39C8e2ceB2a0f9D6e9D059f5E470eDfDA691c15` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 25

**核心摘要：** Arc Inu 是 Arc 上以 AI 为简称的社区/Meme 代币，项目侧有 community takeover 相关线索。

**01 身份与网络：** Arc Inu（AI）属于 Meme 研究分类；Arc Mainnet Chain ID=5042；Token CA=0xA39C8e2ceB2a0f9D6e9D059f5E470eDfDA691c15。验证状态：third_party_index_not_rpc。发现记录：[25]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc Inu 是 Arc 上以 AI 为简称的社区/Meme 代币，项目侧有 community takeover 相关线索。 没有 AI 模型实际营收或技术交付的独立证据。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 没有确认回购或协议价值捕获。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Arc Inu 的潜在方向为 Meme。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：Ticker AI 不表示项目是 AI 基础设施。

**参考来源：** [来源1](https://dexscreener.com/arc/0xc362f08b2d304500e7299eaaf6184492ba3653d831615fe521d0791147f5a0f2)

### 24. Architects（Architects）

**分类：** Meme / Community ｜ **CA：** `0x8bcb94279FC2c984EC34e0C1f2192df8c69EA4F0` ｜ **身份状态：** `third_party_index_not_rpc` ｜ **原始发现记录：** 26

**核心摘要：** 在 Arc DEX 出现的 Architects 名称社区代币。

**01 身份与网络：** Architects（Architects）属于 Meme / Community 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x8bcb94279FC2c984EC34e0C1f2192df8c69EA4F0。验证状态：third_party_index_not_rpc。发现记录：[26]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** 在 Arc DEX 出现的 Architects 名称社区代币。 与 Arc 官方 Architects 社区计划之间不存在可确认的授权/发行关系。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 无确认营收或代币赋能。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Architects 的潜在方向为 Meme / Community。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：社区名称可能引发官方关系错觉，必须要求官方反向链接。

**参考来源：** [来源1](https://dexscreener.com/arc/0x0069cb6f70e2f848405f4483f232274c720ce6f9)

### 25. LONG（LONG）

**分类：** StockFi / MemeStock ｜ **CA：** `0x2164bB17a2D38c1b5170E987b2c0416DF1EFc752` ｜ **身份状态：** `confirmed_by_independent_explorer_not_rpc` ｜ **原始发现记录：** 27

**核心摘要：** Arc 上的 memestocks 发行叙事项目，区块浏览器能匹配用户 CA 为 LONG ERC-20 代理合约。

**01 身份与网络：** LONG（LONG）属于 StockFi / MemeStock 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x2164bB17a2D38c1b5170E987b2c0416DF1EFc752。验证状态：confirmed_by_independent_explorer_not_rpc。发现记录：[27]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** Arc 上的 memestocks 发行叙事项目，区块浏览器能匹配用户 CA 为 LONG ERC-20 代理合约。 LONG 曾出现在可识别的 USDC 池。独立区块浏览器某历史快照显示 Top100 持仓集中度 89.24%，数据时间较旧，不代表当下。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 独立浏览器曾报告 LONG Top100 占比 89.24%，这一数值属历史快照，不得作为 2026-10-14 实时持仓分布。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 合约被识别为 EIP-1167 代理/clone，源码未在该独立浏览器验证；不等于具有可随意升级的管理员权限，需要检查其指向的实现合约。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** LONG 的潜在方向为 StockFi / MemeStock。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：若与股票/股权相关，需补充法律权属；集中度高且合约源码缺失提升审计难度。

**参考来源：** [来源1](https://dexscreener.com/arc/0xda9f3d166497ddfddf37c93cacfd8aa39b71e493) ｜ [来源2](https://arc-scan.org/address/0x2164bb17a2d38c1b5170e987b2c0416df1efc752/contract) ｜ [来源3](https://arc-scan.org/ja/token/0x2164bb17a2d38c1b5170e987b2c0416df1efc752)

### 26. Duke（DUKE）

**分类：** Meme / Community ｜ **CA：** `0xe6a2476f33Ec1566288AA32Ec3319A6B77DD1E3B` ｜ **身份状态：** `user_supplied_unverified` ｜ **原始发现记录：** 28

**核心摘要：** 另一个独立的 Arc DUKE 市场记录。CA 由用户补充，但尚未独立从该交易池回证其 Token address。

**01 身份与网络：** Duke（DUKE）属于 Meme / Community 研究分类；Arc Mainnet Chain ID=5042；Token CA=0xe6a2476f33Ec1566288AA32Ec3319A6B77DD1E3B。验证状态：user_supplied_unverified。发现记录：[28]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** 另一个独立的 Arc DUKE 市场记录。CA 由用户补充，但尚未独立从该交易池回证其 Token address。 未发现可审计的产品营收及用户留存。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 回购/分红机制未知。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Duke 的潜在方向为 Meme / Community。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：与 The Duke of Arc 的合约地址不同，必须拆分；当前 CA-池映射仍需复核。

**参考来源：** [来源1](https://dexscreener.com/arc/0x9673b01178e483c9ea427a76567ed6383e6ca72f)

### 27. Bozo.fun（BOZO）

**分类：** Launchpad / Meme ｜ **CA：** `0x25b2F893EC15808dBDc542938A4A091ece7AEC44` ｜ **身份状态：** `user_supplied_unverified` ｜ **原始发现记录：** 30

**核心摘要：** 用户新池榜单中的 BOZO / Bozo.fun 记录。提供了候选 CA，但此前检索到的池是旧池而非截图中的 7H 新池。

**01 身份与网络：** Bozo.fun（BOZO）属于 Launchpad / Meme 研究分类；Arc Mainnet Chain ID=5042；Token CA=0x25b2F893EC15808dBDc542938A4A091ece7AEC44。验证状态：user_supplied_unverified。发现记录：[30]。同名、同 symbol 不自动代表同一合约，市场交易池与 Token CA 单独保存。

**02 产品与商业模式：** 用户新池榜单中的 BOZO / Bozo.fun 记录。提供了候选 CA，但此前检索到的池是旧池而非截图中的 7H 新池。 必须核对 7H 新池地址与用户提供的 Token CA 是否一致；当前不能将历史池成交额写成新增池的实时成交额。 现阶段需将官网自述与已完成链上验证严格分开。

**03 产品数据与增长：** 尚无可重复计算的 7D/30D 真实产品用户数、收费交易数、TVL 或 Protocol Revenue；DEX 的交易量、持币地址数量、池流动性只能作为市场活动，不替代真实业务指标。

**04 团队背景与融资：** 未取得可交叉核实的创始人完整履历、机构融资金额、股权结构、投资人条款；保持 Unknown 而不猜测。

**05 Tokenomics与价值捕获：** 发行手续费、平台收入、BOZO 代币赋能待核实。 当前流通量、锁仓日程、投资人释放、Top holder 实时占比和合约 mint/blacklist/owner 权限未完成 Arc RPC 核验，不给出无根据的 FDV/合理价格。

**06 Arc生态定位与竞争：** Bozo.fun 的潜在方向为 Launchpad / Meme。应和 Arc 官方 USDC Gas、CCTP、Uniswap 及相同赛道产品进行竞争关系评估。存在 Arc 池/官网不代表 Circle 或 Arc 官方背书；平台业务收入与 token holder revenue 必须分离。

**07 近期进展与注意力：** 2026-10-14 进入原始 DexScreener Arc 榜单发现集（历史观察，不代表持续排名）。目前未取得可审计的 24 小时 X mentions/KOL accounts/unique posters 增速，社交热度、项目公告与成交异动应下一轮按来源和时间戳采集。风险点：新池高波动、池身份时间错配、CA-池对应关系仍未完成独立验证。

**参考来源：** [来源1](https://dexscreener.com/arc/0xf94c727dd3d6318477f1eccc50a2e838654c03f9c974c4e33ad2ce515f8efd41)

## 五、投研比较与监控优先级

| 项目组 | 代表项目 | 值得验证的业务指标 | 风险 / 当前障碍 |
|---|---|---|---|
| 原生结算与机构基础设施 | **Arc Network** | 真实 USDC 转账额、活跃付费账户、网络 USDC 费用、RWA 存量 | 许可验证者、USDC 依赖、尚未公开 ARC token |
| AI Agent 支付 | **Arcus、Arcflow、oBrain** | x402 成功结算数、唯一代理、USDC 平台收入 | 业务收入与 Token 持有人收入脱钩 |
| 多产品交易 | **Kairo、Tolly** | 协议手续费、活跃交易账户、发行量、KAIRO burn | Perps 外部场所、域名/费率版本不一致 |
| 代币发行基础设施 | **Argus、Faze、UBI、SolonPad、MEMESPAD** | 真实发行合约数、发行者留存、平台净手续费 | 发行/迁移刷量和低留存率 |
| DeFi LP 工具 | **Arclight** | Uniswap LP NFT 数、独立用户、收费、净收益 | LP impermanent loss、权限需验证 |
| RWA/StockFi 叙事 | **ArcStocks、LONG、CRCL** | 权属凭证、托管/赎回、第三方储备、真实交易 | 不能把同名代币映射成股票股权 |
| Meme/社区及资料缺口 | **ARCAT、两个 DUKE、UpSideDownCat、BOZO 等** | 流动性持久性、净新增持有人、权限审计 | 假冒 ticker、池身份不明、极端波动 |

## 六、使用与网站架构建议（不修改线上代码）

1. 四层主键：`discovery_record_id → project_id → (chain_id, token_contract) → pool_address`；不要以 symbol 作为主键。
2. 默认加载静态研究；实时 API 可用时单独覆盖市场板块。API 不可用显示 `Market Data Unavailable`，基础档案仍可读。
3. 用可见证据标记：`project_claim` / `third_party_market` / `independent_explorer` / `rpc_verified`，不将任何前三类误称 RPC verified。
4. 若不同池/同名 CA 发生冲突，前端展示多个身份候选并让用户依据合约确认。
5. 所有行情字段带 `collected_at`、`block_number`、`source`、`freshness`。只在使用真实链上读数时填 `verified=true`。
6. 需要高亮：官方 USDC `0x3600000000000000000000000000000000000000`、非官方 USDC Meme、Arc 官方未公开 ARC 代币、CRCL 品牌冒用风险。
7. 优先补：所有用户提交 CA → RPC `eth_getCode` → Token metadata → 池 `token0/token1` → admin/proxy/owner/mint → LP 归属 → 真实 Revenue。

## 七、研究证据与限制

- **已覆盖:** 原始榜单 30/30，去重 Token 27/27，官方 Arc Network 1，七模块报告实体合计 28。
- **CA 格式:** 27 个 Token 主体均有合法形式的 20-byte 候选/来源地址；这不等于 27 个均通过 Arc 主网 RPC 认证。
- **特别待核:** 第二个 DUKE `0xe6a2476f...`、BOZO `0x25b2F893...` 的「用户 CA ↔ 当前截图目标 Pool」映射，以及 UpSideDownCat #29 新池。
- **没有执行:** 链上批量 RPC 审计、权限探针、实时行情锁定、24h X mentions 的可重现采集；融资/营收/用户数据无证据则保持 Unknown。
- **身份纠错:** ARCAT 自述 gas 使用 ARC 与 Arc 官方 USDC 原生 Gas 相冲突，已显著警示。Kairo Perps 不同介绍页关于结算架构/开放状态存在不一致；应以实际部署链上交易为准。

### 官方与关键原始资料
- [arc_launch](https://www.arc.io/pressroom/circle-launches-arc-mainnet-an-economic-operating-system-for-the-internet)
- [arc_network](https://www.arc.io/network)
- [arc_token](https://www.arc.io/arc-token-whitepaper)
- [arc_stats](https://explorer.arc.io/stats)
- [arc_security](https://www.arc.io/security)
- [arc_exchange](https://www.arc.io/blog/integrating-arc-for-deposits-and-withdrawals)
- [kairo_site](https://kairo.market/)
- [kairo_perps](https://kairo.market/docs/perps)
- [arcus_site](https://arcusnetwork.co/arcus)
- [arcat_site](https://arcat.online/)
- [long_check](https://arc-scan.org/address/0x2164bb17a2d38c1b5170e987b2c0416df1efc752/contract)
- [arclight_docs](https://arclight.finance/docs/how-it-works)
- [tolly_docs](https://tollylabs.com/guide)

**结论：本批数据可作为 ArcDossier 的研究回退层，但不应在未经核验前作为“所有合约均 RPC 验证”“实时行情”或“已确认收入分红”的对外表述。**
