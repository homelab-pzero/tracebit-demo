def render(invoice: dict) -> str:
    lines = [f"Invoice {invoice['id']}"]
    for item in invoice["items"]:
        lines.append(f"  {item['name']:<30} {item['cents'] / 100:>10.2f}")
    total = sum(i["cents"] for i in invoice["items"])
    lines.append(f"  {'TOTAL':<30} {total / 100:>10.2f}")
    return "\n".join(lines)
