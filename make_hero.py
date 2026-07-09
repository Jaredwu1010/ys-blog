#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_hero.py — YS 知識 blog 主圖(hero image)產生器

功能：
  讀取文章 frontmatter 的 title / pillar，產出品牌化主圖。
  中文字一律用 PIL 疊上（不是 AI 生成），所以不會出現錯字／簡體字。

兩種底圖模式：
  1) 品牌底圖（預設，全自動、免 AI）：程式畫出球場配色的漸層卡片。
  2) AI 情境底圖：用 --base 丟一張 ChatGPT/API 生的「無文字」情境圖，
     腳本會自動裁切、加暗部遮罩，再把中文字疊上去。

用法範例：
  # 單篇（臨時指定標題）
  python3 make_hero.py --title "什麼是 dink？匹克球最關鍵的入門技術" --pillar 技術 --out hero.webp

  # 單篇（讀某個 .md 的 frontmatter）
  python3 make_hero.py --md src/content/blog/what-is-dink.md

  # 批次：掃描整個 blog 資料夾，每篇產一張，並把 heroImage 寫回 frontmatter
  python3 make_hero.py --all --dir src/content/blog --inject

  # 用 AI 情境底圖
  python3 make_hero.py --md src/content/blog/what-is-dink.md --base scene.jpg
"""

import argparse, os, glob, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    import yaml
except ImportError:
    yaml = None

# ── 品牌配色（沿用 blog 的球場配色）──
COURT   = (13, 59, 57)
COURT2  = (8, 40, 38)
VOLT    = (200, 224, 52)
PAPER   = (246, 244, 238)
WHITE   = (245, 248, 246)

# ── 字型候選：容器 Noto CJK ＋ macOS 內建 PingFang（她的 Mac 免安裝）──
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/PingFang.ttc",          # macOS 內建
    "/System/Library/Fonts/STHeiti Medium.ttc",     # macOS 備援
    "/Library/Fonts/NotoSansCJKtc-Black.otf",
]

def load_font(size, override=None):
    paths = ([override] if override else []) + FONT_CANDIDATES
    for p in paths:
        if p and os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    print("⚠️  找不到中文字型，請用 --font 指定一個 .ttc/.otf 路徑", file=sys.stderr)
    sys.exit(1)


def read_frontmatter(md_path):
    """回傳 (frontmatter_dict, raw_lines)。手動切 --- 區塊，避免額外相依。"""
    with open(md_path, encoding="utf-8") as f:
        text = f.read()
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm = yaml.safe_load(parts[1]) if yaml else {}
    return (fm or {}), text


def wrap_cjk(draw, text, font, max_width):
    """中文無空格，逐字累加到超過寬度就換行；同時尊重原有空白斷點。"""
    lines, cur = [], ""
    for ch in text:
        test = cur + ch
        if draw.textlength(test, font=font) <= max_width or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = ch
        if ch == "\n":
            lines.append(cur.rstrip("\n"))
            cur = ""
    if cur:
        lines.append(cur)
    return lines


def make_gradient_bg(w, h):
    """球場配色的對角漸層底圖 ＋ 品牌球體 motif。"""
    base = Image.new("RGB", (w, h), COURT)
    top = Image.new("RGB", (w, h), COURT)
    # 垂直漸層 COURT -> COURT2
    grad = Image.new("L", (1, h))
    for y in range(h):
        grad.putpixel((0, y), int(255 * (y / h)))
    grad = grad.resize((w, h))
    dark = Image.new("RGB", (w, h), COURT2)
    base = Image.composite(dark, top, grad)

    draw = ImageDraw.Draw(base, "RGBA")
    # 右下角半透明品牌球（含球洞 motif）
    r = int(h * 0.55)
    cx, cy = int(w * 0.86), int(h * 0.92)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=VOLT + (26,))
    # 幾顆球洞
    import random
    random.seed(7)
    for _ in range(10):
        a = random.uniform(0, 6.28); rr = random.uniform(0.2, 0.8) * r
        hx, hy = cx + int(rr * 0.9 * (a % 2 - 1)), cy + int(rr * (a % 3 - 1) * 0.5)
        draw.ellipse([hx - 6, hy - 6, hx + 6, hy + 6], fill=COURT + (60,))
    # 細球場線
    draw.line([(0, int(h * 0.5)), (w, int(h * 0.5))], fill=WHITE + (18,), width=2)
    return base


def fit_base_image(path, w, h):
    """cover 裁切外部底圖到指定尺寸，並加底部暗部漸層遮罩讓文字可讀。"""
    img = Image.open(path).convert("RGB")
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    img = img.resize((int(iw * scale), int(ih * scale)))
    left = (img.width - w) // 2; top = (img.height - h) // 2
    img = img.crop((left, top, left + w, top + h))
    # 底部→上 的暗部遮罩
    scrim = Image.new("L", (1, h))
    for y in range(h):
        v = int(200 * max(0, (y / h - 0.25) / 0.75))
        scrim.putpixel((0, y), v)
    scrim = scrim.resize((w, h))
    dark = Image.new("RGB", (w, h), (5, 20, 19))
    return Image.composite(dark, img, scrim)


def draw_pill(draw, xy, text, font):
    x, y = xy
    pad_x, pad_y = 22, 12
    tw = draw.textlength(text, font=font)
    th = font.size
    draw.rounded_rectangle([x, y, x + tw + pad_x * 2, y + th + pad_y * 2],
                           radius=(th + pad_y * 2) // 2, fill=VOLT)
    draw.text((x + pad_x, y + pad_y - 2), text, font=font, fill=COURT)
    return y + th + pad_y * 2


def render(title, pillar, size=(1600, 840), base=None, font_override=None):
    w, h = size
    img = fit_base_image(base, w, h) if base else make_gradient_bg(w, h)
    draw = ImageDraw.Draw(img, "RGBA")

    margin = 80
    f_pill  = load_font(30, font_override)
    f_title = load_font(76, font_override)
    f_brand = load_font(30, font_override)

    # 支柱 pill（左上）
    if pillar:
        draw_pill(draw, (margin, margin), str(pillar), f_pill)

    # 標題（左下、往上排）
    max_w = int(w * 0.78)
    lines = wrap_cjk(draw, title, f_title, max_w)
    line_h = int(f_title.size * 1.28)
    brand_y = h - margin - f_brand.size - 6
    ty = brand_y - 40 - len(lines) * line_h
    for ln in lines:
        # 乾淨白字 ＋ 輕微投影（不用 stroke，避免中文筆畫糊在一起）
        draw.text((margin + 2, ty + 3), ln, font=f_title, fill=(0, 0, 0, 90))  # 陰影
        draw.text((margin, ty), ln, font=f_title, fill=WHITE)                   # 主字
        ty += line_h

    # 品牌字樣（左下）＋ 小球點
    draw.ellipse([margin, brand_y + 4, margin + 22, brand_y + 26], fill=VOLT)
    draw.text((margin + 34, brand_y), "YS 躍升匹克球學院", font=f_brand, fill=WHITE)
    return img


def process_md(md_path, args):
    fm, raw = read_frontmatter(md_path)
    title = fm.get("title")
    pillar = fm.get("pillar", "")
    if not title:
        print(f"跳過（沒有 title）：{md_path}"); return
    stem = os.path.splitext(os.path.basename(md_path))[0]
    out_name = f"{stem}-hero.webp"
    out_path = os.path.join(os.path.dirname(md_path), out_name)
    img = render(title, pillar, base=args.base, font_override=args.font)
    img.save(out_path, "WEBP", quality=88, method=6)
    print(f"✅ {out_path}")
    if args.inject and "heroImage" not in fm:
        # 在 frontmatter 結尾插入 heroImage / heroAlt
        parts = raw.split("---", 2)
        inject = f"heroImage: ./{out_name}\nheroAlt: {title}\n"
        new = f"---{parts[1]}{inject}---{parts[2]}"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"   ↳ 已寫入 heroImage 到 {os.path.basename(md_path)}")
    elif not args.inject:
        print(f"   ↳ 請在 frontmatter 加：heroImage: ./{out_name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title")
    ap.add_argument("--pillar", default="")
    ap.add_argument("--md")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dir", default="src/content/blog")
    ap.add_argument("--base", help="AI 情境底圖（無文字）路徑；不給則用品牌漸層底圖")
    ap.add_argument("--out", default="hero.webp")
    ap.add_argument("--font", help="自訂中文字型路徑（.ttc/.otf）")
    ap.add_argument("--inject", action="store_true", help="把 heroImage 寫回 frontmatter")
    args = ap.parse_args()

    if args.all:
        files = sorted(glob.glob(os.path.join(args.dir, "*.md")))
        if not files:
            print(f"在 {args.dir} 找不到 .md"); return
        for md in files:
            process_md(md, args)
    elif args.md:
        process_md(args.md, args)
    elif args.title:
        img = render(args.title, args.pillar, base=args.base, font_override=args.font)
        img.save(args.out, "WEBP", quality=88, method=6)
        print(f"✅ {args.out}")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
