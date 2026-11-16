import { test } from "node:test";
import assert from "node:assert/strict";
import { formatPrice } from "../src/index.js";

test("formats cents as dollars", () => {
  assert.equal(formatPrice(123456), "$1,234.56");
});

test("rejects fractional cents", () => {
  assert.throws(() => formatPrice(1.5), TypeError);
});
