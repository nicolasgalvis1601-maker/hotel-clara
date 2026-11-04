const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const { test } = require('node:test');
const { createContext, runInContext } = require('node:vm');

const root = resolve(__dirname, '..', '..');
const source = readFileSync(resolve(root, 'frontend', 'script.js'), 'utf8');

test('precios COP usan separador de miles sin decimales', () => {
  const definition = source.match(/function formatMoney\(value\) \{[\s\S]*?\n\}/);
  assert.ok(definition, 'Debe existir el formateador compartido de precios');
  const context = createContext({});
  runInContext(definition[0], context);
  for (const [amount, expected] of [
    [89000, '$ 89.000'],
    [115000, '$ 115.000'],
    [162000, '$ 162.000'],
    [234000, '$ 234.000'],
    [0, '$ 0'],
    [125.5, '$ 126'],
  ]) {
    assert.equal(context.formatMoney(amount).replace(/\s/g, ' '), expected);
  }
});

test('catalogo y administracion usan el formateador sin toFixed', () => {
  assert.ok(source.includes('${formatMoney(room.precio * nights)}'));
  assert.ok(source.includes('${formatMoney(service.precio)}'));
  assert.doesNotMatch(source, /\.toFixed\(2\)/);
});
