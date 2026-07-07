# YS 躍升匹克球學院 · 知識 Blog（Astro 6 + Cloudflare Pages）

文章引擎輸出 markdown → 存進 `src/content/blog/` → `git push` → GitHub Actions 自動 build 上線。
本專案已在 Astro v6.4.8 實測 build 通過（首頁、文章頁、RSS、sitemap 皆正常）。

## 一次性設定（只做一次）

1. **改站台資訊**：編輯 `src/consts.ts`，把 `url` 換成你的正式網域、`lineUrl` 換成你的官方 LINE 連結；
   同步把 `astro.config.mjs` 的 `site` 與 `public/robots.txt` 的網域改成一致。
2. **建 Cloudflare Pages 專案**：Cloudflare 後台 → Workers & Pages → 建一個名為 `ys-blog` 的 Pages 專案
   （或首次 `wrangler pages deploy` 時自動建立）。若專案名不叫 `ys-blog`，記得改 `.github/workflows/deploy.yml` 的 `--project-name`。
3. **設兩個 GitHub Secrets**（repo → Settings → Secrets and variables → Actions）：
   - `CLOUDFLARE_API_TOKEN`：Cloudflare 後台建 API Token，權限選「Edit Cloudflare Pages」。
   - `CLOUDFLARE_ACCOUNT_ID`：Cloudflare 帳號總覽頁可查到。

## 本地開發

```bash
npm install          # 首次；會產生 package-lock.json，請一併 commit
npm run dev          # 本地預覽 http://localhost:4321
npm run build        # 產出靜態網站到 dist/
```

## 自動部署

推到 `main` 分支就會觸發 `.github/workflows/deploy.yml`：安裝 → build → 用 wrangler 部署到 Cloudflare Pages。
（workflow 用 `npm ci`，所以請確保 `package-lock.json` 有 commit 進 repo。）

## Frontmatter 規格（對齊文章引擎輸出）

定義在 `src/content.config.ts`。每篇 `.md` 開頭：

```yaml
---
title: <引擎【SEO標題】>          # 8–40 字
description: <引擎【Meta描述】>    # 30–120 字
pubDate: 2026-07-07               # 發布日期
pillar: 樂齡                       # 產業/技術/課程/教學/器材/安全/規則/數據/初學FAQ/樂齡
keywords: ["樂齡 匹克球", "..."]   # 目標關鍵字
heroImage: ./cover.webp           # 選填；PIL 疊字後的成圖，與 .md 同資料夾
heroAlt: 圖片說明                  # 選填
author: YS 躍升匹克球學院          # 選填，有預設
lineCta: true                     # 是否顯示 LINE CTA 區塊
draft: true                       # ★ 審核關：true 不發布，審核過改 false 才上線
---
```

## ④ 審核關怎麼運作

- 引擎新產出的文章一律 `draft: true` → build 時（正式環境）**不會出現在網站與 RSS**。
- 你在 Notion 審核、把【事實查核清單】逐條核對完 → 把該篇的 `draft` 改成 `false` → push → 自動上線。
- 本地 `npm run dev` 仍看得到 draft，方便你預覽未發布的稿。

## 發一篇文章的完整流程

1. 引擎產出 → 取【SEO標題】【Meta描述】【內文】組成一支 `.md`，`draft: true`。
2. 存到 `src/content/blog/你的檔名.md`（檔名會變成網址 slug，建議用英數或關鍵字）。
3.（選）把【配圖brief】→ image API 底圖 → PIL 疊中文 → 成圖放同資料夾，frontmatter 補 `heroImage`。
4. 審核通過 → `draft: false`。
5. `git push` → 自動上線。
6.【社群發文】FB/IG/Threads 走另一條分發（不進 blog），CTA 一樣導 LINE。

## 之後可加

- 電子報：想做「內容 + 訂閱」時可接 Ghost 或用 RSS（`/rss.xml` 已內建）串電子報服務。
- Google Search Console：上線後把網域加進去，看收錄與關鍵字成效。
