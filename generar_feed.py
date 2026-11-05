"""Feed de productos de blacksecret.mx para el catálogo de Meta "Productos para blacksecret.mx" (925970951517526).

Lee la lista pública de Shopify (/products.json) y escribe feed.csv con el formato de Meta.
id = id de variante de Shopify: es el mismo que manda el píxel y el que ya usa ese catálogo,
así Meta actualiza las prendas existentes en vez de duplicarlas.
"""

import csv
import html
import json
import re
import subprocess
import sys
import time

STORE = "https://blacksecret.mx"
BRAND = "Black Secret Boutique"
PAGE_SIZE = 250
MAX_PAGES = 20
TIMEOUT_S = 30
USER_AGENT = "blacksecret-feed-meta/1.0 (+Caliber Studio)"
OUT = "feed.csv"
MIN_VARIANTS = 500  # si llegan menos, algo falló: no se sobreescribe el feed bueno

COLUMNS = [
    "id", "item_group_id", "title", "description", "availability", "condition",
    "price", "sale_price", "link", "image_link", "brand", "size", "color",
]


def fetch_page(page):
    # Se descarga con curl: Shopify responde 429 a urllib de Python (y a Workers) aunque el UA sea el mismo.
    url = f"{STORE}/products.json?limit={PAGE_SIZE}&page={page}"
    for attempt in range(3):
        res = subprocess.run(
            ["curl", "-sS", "--max-time", str(TIMEOUT_S), "-A", USER_AGENT, "-w", "\n%{http_code}", url],
            capture_output=True, text=True, check=True,
        )
        body, _, status = res.stdout.rpartition("\n")
        if status == "200":
            return json.loads(body)["products"]
        if status != "429" or attempt == 2:
            raise RuntimeError(f"products.json pagina {page}: HTTP {status}")
        time.sleep(15 * (attempt + 1))


def fetch_all():
    products = []
    for page in range(1, MAX_PAGES + 1):
        batch = fetch_page(page)
        products.extend(batch)
        if len(batch) < PAGE_SIZE:
            return products
        time.sleep(3)
    raise RuntimeError(f"más de {MAX_PAGES} páginas")


def strip_html(text):
    text = re.sub(r"<[^>]*>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()[:5000]


def to_row(p, v):
    def option(names):
        for i, o in enumerate(p["options"]):
            if o["name"].lower() in names:
                return v.get(f"option{i + 1}") or ""
        return ""

    image = (v.get("featured_image") or {}).get("src") or (p["images"][0]["src"] if p["images"] else "")
    title = f'{p["title"]} - {v["title"]}' if v["title"] != "Default Title" else p["title"]
    compare = v.get("compare_at_price")
    on_sale = bool(compare) and float(compare) > float(v["price"])
    return [
        str(v["id"]),
        str(p["id"]),
        title,
        strip_html(p.get("body_html")) or p["title"],
        "in stock" if v["available"] else "out of stock",
        "new",
        f'{compare if on_sale else v["price"]} MXN',
        f'{v["price"]} MXN' if on_sale else "",
        f'{STORE}/products/{p["handle"]}?variant={v["id"]}',
        image,
        p.get("vendor") or BRAND,
        option({"talla", "size", "tamaño"}),
        option({"color", "colour"}),
    ]


def main():
    products = fetch_all()
    rows = [to_row(p, v) for p in products for v in p["variants"]]
    if len(rows) < MIN_VARIANTS:
        sys.exit(f"Solo llegaron {len(rows)} variantes (mínimo {MIN_VARIANTS}); no se actualiza el feed.")
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    print(f"{len(products)} productos, {len(rows)} variantes -> {OUT}")


if __name__ == "__main__":
    main()
