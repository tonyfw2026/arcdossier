# Fonts

The three families below are self-hosted in `fonts/` so the prototype renders
identically with no network access and no requests to third-party font CDNs.
Only the `latin` subset of each weight is included (88 KB total).

| Family | Weights | Files | Used for |
|---|---|---|---|
| [DM Sans](https://fonts.google.com/specimen/DM+Sans) | 400, 500, 700 | `dmsans-*.woff2` | Body text, buttons, UI |
| [Space Grotesk](https://fonts.google.com/specimen/Space+Grotesk) | 500, 700 | `spacegrotesk-*.woff2` | Display headings, live numbers |
| [Space Mono](https://fonts.google.com/specimen/Space+Mono) | 400, 700 | `spacemono-*.woff2` | Eyebrows, receipts, chain data |

All three are licensed under the **SIL Open Font License 1.1**, which permits
redistribution. The full licence text for each family ships next to the files:

- `OFL-dmsans.txt`
- `OFL-spacegrotesk.txt`
- `OFL-spacemono.txt`

The `@font-face` rules live at the top of `styles.css` and point at relative
paths (`./fonts/…`). `server.py` serves `/fonts/<name>` from a strict whitelist:
filenames must match `[A-Za-z0-9][A-Za-z0-9._-]*` with a `.woff2`, `.txt` or
`.json` extension, and any name containing `..` is rejected.

The families were chosen to match the type pairing published on arc.io
(DM Sans for body, Space Grotesk for display, Space Mono for labels). The fonts
themselves are the upstream Google Fonts builds, not files copied from arc.io.

`manifest.json` records the family, weight and byte size of each downloaded file.
