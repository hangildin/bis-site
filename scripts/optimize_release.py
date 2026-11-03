#!/usr/bin/env python3
"""Optimize a generated BIS V2 release without changing source photos or PDFs.

Runs ONLY on the dist/ tree, requires Pillow. Converts compatible image assets
to appropriately sized WebP, rewrites HTML/CSS/inline JS and social meta links,
adds responsive image variants, preserves photographic proportions and names.
"""
import argparse
import re
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dist",type=Path,default=Path("dist"))
    args=ap.parse_args()
    root=args.dist.resolve()
    if not (root/"index.html").is_file() or not (root/"assets").is_dir():
        ap.error("Expected an existing generated release tree with index and assets")
    all_images=list((root/"assets").rglob("*"))
    all_images=[p for p in all_images if p.is_file() and p.suffix.lower() in (".jpg",".jpeg",".png")]
    start_bytes=sum(p.stat().st_size for p in all_images)
    replacements={}
    dims={}
    variants={}
    medium={}
    converted=skipped=0
    for path in all_images:
        rel=path.relative_to(root).as_posix()
        try:
            with Image.open(path) as base:
                im=ImageOps.exif_transpose(base)
                if im.mode not in ("RGB","RGBA"):
                    im=im.convert("RGBA" if "A" in im.getbands() else "RGB")
                im.thumbnail((1800,1800),Image.Resampling.LANCZOS)
                new=path.with_suffix(".webp")
                if new.exists() and new!=path:
                    raise ValueError("Duplicate WebP target: "+str(new))
                im.save(new,format="WEBP",quality=78,method=5)
                if new.stat().st_size>=path.stat().st_size*.95:
                    new.unlink()
                    skipped+=1
                    continue
                newrel=new.relative_to(root).as_posix()
                replacements[rel]=newrel
                dims[newrel]=(im.width,im.height)
                if im.width>=1100:
                    small=im.copy()
                    small.thumbnail((800,800),Image.Resampling.LANCZOS)
                    smallpath=path.with_name(path.stem+"-mobile.webp")
                    small.save(smallpath,format="WEBP",quality=73,method=5)
                    variants[newrel]=smallpath.relative_to(root).as_posix()
                    # Extra source for the hero LCP: high-DPR mobile otherwise downloads 1800px.
                    if rel=='assets/zelenodolsk/photo_4_2026-10-19_15-18-08.jpg':
                        mid=im.copy()
                        mid.thumbnail((1200,1200),Image.Resampling.LANCZOS)
                        midpath=path.with_name(path.stem+'-medium.webp')
                        mid.save(midpath,format='WEBP',quality=74,method=5)
                        medium[newrel]=midpath.relative_to(root).as_posix()
                converted+=1
        except (UnidentifiedImageError,OSError) as e:
            raise SystemExit(f"Cannot optimize source {rel}: {e}")
    # Handle HTML, style url(), OG, Article JSON-LD, inline script image references.
    for page in list(root.glob("*.html"))+list(root.rglob("*.css")):
        html=page.read_text(encoding="utf-8")
        for old,new in replacements.items():
            html=html.replace(old,new)
        if page.suffix==".html":
            def add_attrs(match):
                tag=match.group(0)
                source=re.search(r'\bsrc="(assets/[^"]+)"',tag)
                if not source:return tag
                src=source.group(1)
                if src not in dims:return tag
                w,h=dims[src]
                if not re.search(r'\bwidth=',tag):
                    tag=tag[:-1]+f' width="{w}" height="{h}">'
                if src in variants and "srcset=" not in tag:
                    sm=variants[src]
                    responsive=f'{sm} 800w, {src} {w}w'
                    if src in medium:responsive=f'{sm} 800w, {medium[src]} 1200w, {src} {w}w'
                    tag=tag[:-1]+f' srcset="{responsive}" sizes="(max-width: 800px) 100vw, (max-width: 1250px) 65vw, 1200px">'
                return tag
            html=re.sub(r'<img\b[^>]*>',add_attrs,html,flags=re.I)
            # Responsive preload must match srcset; otherwise small phones download the full hero unnecessarily.
            def preload(match):
                tag=match.group(0)
                if 'rel="preload"' not in tag or 'as="image"' not in tag:return tag
                ref=re.search(r'href="(assets/[^"]+)"',tag)
                if not ref:return tag
                src=ref.group(1)
                if src not in variants:return tag
                small=variants[src]
                w=dims[src][0]
                responsive=f'{small} 800w, {src} {w}w'
                if src in medium:responsive=f'{small} 800w, {medium[src]} 1200w, {src} {w}w'
                return tag[:-1]+f' imagesrcset="{responsive}" imagesizes="(max-width: 800px) 100vw, 65vw">'
            html=re.sub(r'<link\b[^>]*>',preload,html,flags=re.I)
            # The carousel changes img.src in JS. Keeping a previous srcset would lock it to slide one.
            if 'id="heroSlideImage"' in html:
                html=html.replace('img.src=item.src;',
                    'img.removeAttribute("srcset");img.removeAttribute("sizes");img.src=item.src;')
        page.write_text(html,encoding="utf-8")
    # Source images aren't needed when all HTML and styles use the optimized files.
    # Originals remain untouched in GitHub's source branch.
    for old in replacements:
        (root/old).unlink()
    ending_bytes=sum(p.stat().st_size for p in (root/"assets").rglob("*") if p.is_file() and p.suffix.lower() in (".jpg",".jpeg",".png",".webp"))
    print(f"BIS image optimization: {len(all_images)} considered, {converted} WebP, {skipped} preserved, {len(variants)} responsive variants.")
    print(f"Asset images before: {start_bytes/1048576:.2f} MiB; after: {ending_bytes/1048576:.2f} MiB; ratio: {ending_bytes/max(start_bytes,1):.3f}.")
    if not replacements:raise SystemExit("Optimization found no eligible photos; investigate inputs.")

if __name__=="__main__":main()
