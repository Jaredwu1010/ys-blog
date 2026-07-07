import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// ⚠️ 換成你的正式網域（要跟 src/consts.ts 的 url 一致），sitemap 才會正確
export default defineConfig({
  site: 'https://ys-blog-cup.pages.dev',
  integrations: [sitemap()],
});
