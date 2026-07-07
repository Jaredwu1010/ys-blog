import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// ── 這張 schema 就是「frontmatter 規格」，對齊文章引擎的輸出 ──
const blog = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/blog' }),
  schema: ({ image }) =>
    z.object({
      // 來自引擎【SEO標題】
      title: z.string().min(8).max(40),
      // 來自引擎【Meta描述】
      description: z.string().min(30).max(120),
      // 發布日期（⑤ 發布時蓋章）
      pubDate: z.coerce.date(),
      updatedDate: z.coerce.date().optional(),
      // 內容支柱（對齊選題庫）
      pillar: z.enum([
        '產業', '技術', '課程', '教學', '器材',
        '安全', '規則', '數據', '初學FAQ', '樂齡',
      ]),
      // 目標關鍵字
      keywords: z.array(z.string()).default([]),
      // 主圖（來自【配圖brief】，PIL 疊字後的成圖放這；與 .md 同資料夾）
      heroImage: image().optional(),
      heroAlt: z.string().default(''),
      author: z.string().default('YS 躍升匹克球學院'),
      // 是否顯示 LINE CTA 區塊
      lineCta: z.boolean().default(true),
      // ── ④ 審核關：預設 true（未審核不發布），審核過改成 false 才上線 ──
      draft: z.boolean().default(true),
    }),
});

export const collections = { blog };
