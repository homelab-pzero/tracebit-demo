// The "product": a price formatter. It exists so the pipeline has something real to build and test.
export function formatPrice(cents, currency = "USD") {
  if (!Number.isInteger(cents)) throw new TypeError("cents must be an integer");
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(cents / 100);
}
