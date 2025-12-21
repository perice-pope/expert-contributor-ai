// Tests for example module

const { add, multiply } = require('./example');

test('add function', () => {
  expect(add(2, 3)).toBe(5);
  expect(add(0, 0)).toBe(0);
  expect(add(-1, 1)).toBe(0);
});

test('multiply function', () => {
  expect(multiply(2, 3)).toBe(6);
  expect(multiply(0, 5)).toBe(0);
  expect(multiply(-1, 4)).toBe(-4);
});

