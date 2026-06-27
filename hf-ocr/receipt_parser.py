import json
import re

SKIP_PATTERNS = [
    r"편의점",
    r"세븐",
    r"주소",
    r"TEL",
    r"전화",
    r"사업자",
    r"대표",
    r"등록",
    r"상품명",
    r"수량",
    r"금액",
    r"합\s*계",
    r"받을",
    r"카드",
    r"승인",
    r"거래",
    r"일시",
    r"POS",
    r"영수증",
    r"채널",
    r"부가세",
    r"면세",
    r"과세",
    r"^\*",
    r"^>+",
    r"^\d{4}-\d{2}-\d{2}",
    r"^\d{2}:\d{2}",
    r"^#\d+",
    r"문정.*점",
    r"^\d{5,}$",
]

PRICE_RE = re.compile(r"^[\d,]+$")


def is_price(text: str) -> bool:
    cleaned = text.replace(" ", "").replace("₩", "").replace("원", "")
    return bool(PRICE_RE.match(cleaned)) and len(cleaned) >= 2


def should_skip(line_text: str) -> bool:
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, line_text, re.IGNORECASE):
            return True
    return False


def group_by_row(detections, y_threshold: float = 20):
    items = []
    for bbox, text, conf in detections:
        text = text.strip()
        if not text:
            continue
        ys = [point[1] for point in bbox]
        xs = [point[0] for point in bbox]
        items.append(
            {
                "text": text,
                "conf": conf,
                "y": sum(ys) / len(ys),
                "x": min(xs),
            }
        )

    items.sort(key=lambda item: (item["y"], item["x"]))

    rows = []
    current_row = []
    current_y = None

    for item in items:
        if current_y is None or abs(item["y"] - current_y) <= y_threshold:
            current_row.append(item)
            current_y = item["y"] if current_y is None else sum(i["y"] for i in current_row) / len(current_row)
        else:
            if current_row:
                rows.append(sorted(current_row, key=lambda i: i["x"]))
            current_row = [item]
            current_y = item["y"]

    if current_row:
        rows.append(sorted(current_row, key=lambda i: i["x"]))

    return rows


def parse_receipt_items(detections):
    items = []

    for row in group_by_row(detections):
        texts = [cell["text"] for cell in row]
        line = " ".join(texts)

        if should_skip(line):
            continue

        if len(texts) >= 2 and is_price(texts[-1]):
            price = texts[-1].replace("₩", "").replace("원", "").strip()
            rest = texts[:-1]
            if len(rest) >= 2 and rest[-1].isdigit() and len(rest[-1]) == 1:
                name = " ".join(rest[:-1])
            else:
                name = " ".join(rest)
            if name and len(name) >= 2:
                items.append({"name": name.strip(), "price": price})
            continue

        prices = [text for text in texts if is_price(text)]
        non_prices = [text for text in texts if not is_price(text) and not (text.isdigit() and len(text) == 1)]
        if prices and non_prices:
            name = " ".join(non_prices).strip()
            price = prices[-1].replace("₩", "").replace("원", "").strip()
            if name and len(name) >= 2 and not should_skip(name):
                items.append({"name": name, "price": price})

    unique = []
    seen = set()
    for item in items:
        key = (item["name"], item["price"])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique


def format_receipt_items(items):
    if not items:
        return "영수증에서 상품명·금액을 찾지 못했습니다."
    lines = ["상품명 | 금액", "--- | ---"]
    for item in items:
        lines.append(f"{item['name']} | {item['price']}")
    return "\n".join(lines)


def receipt_items_to_json(items):
    return json.dumps(items, ensure_ascii=False)
