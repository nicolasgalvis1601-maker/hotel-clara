const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const { test } = require('node:test');
const { createContext, runInContext } = require('node:vm');

const root = resolve(__dirname, '..', '..');
const script = readFileSync(resolve(root, 'frontend', 'script.js'), 'utf8');
const html = readFileSync(resolve(root, 'frontend', 'index.html'), 'utf8');
const styles = readFileSync(resolve(root, 'frontend', 'styles.css'), 'utf8');

test('el botón cambia el tema, accesibilidad y preferencia guardada', () => {
  const key = script.match(/const THEME_STORAGE_KEY = 'hotel_theme';/);
  const setTheme = script.match(/function setTheme\(theme\) \{[\s\S]*?\n\}/);
  const initializeTheme = script.match(/function initializeTheme\(\) \{[\s\S]*?\n\}/);
  assert.ok(key && setTheme && initializeTheme, 'Debe existir la inicialización persistente del tema');
  const attributes = {};
  const listeners = {};
  const label = { textContent: '' };
  const button = {
    setAttribute: (name, value) => { attributes[name] = value; },
    addEventListener: (name, callback) => { listeners[name] = callback; },
  };
  const context = createContext({
    document: {
      documentElement: { dataset: { theme: 'light' } },
    },
    themeToggleButton: button,
    themeToggleLabel: label,
    localStorage: {
      value: 'dark',
      getItem() { return this.value; },
      setItem(key, value) { this.key = key; this.value = value; },
    },
  });
  runInContext(`${key[0]};${setTheme[0]};${initializeTheme[0]};initializeTheme();`, context);

  assert.equal(context.document.documentElement.dataset.theme, 'dark');
  assert.equal(attributes['aria-pressed'], 'true');
  assert.equal(attributes['aria-label'], 'Cambiar a modo claro');
  assert.equal(label.textContent, 'Modo claro');
  assert.equal(context.localStorage.key, 'hotel_theme');
  listeners.click();
  assert.equal(context.document.documentElement.dataset.theme, 'light');
  assert.equal(attributes['aria-pressed'], 'false');
  assert.equal(label.textContent, 'Modo oscuro');
  assert.equal(context.localStorage.value, 'light');
});

test('la página incluye el botón y variables para un tema oscuro contrastado', () => {
  assert.match(html, /id="theme-toggle"/);
  assert.doesNotMatch(html, /CONEXIÓN SEGURA/i);
  assert.match(styles, /:root\[data-theme="dark"\]/);
  assert.match(styles, /--surface: #1e293b/);
  assert.match(styles, /--ink: #e2e8f0/);
  assert.match(styles, /\.theme-toggle\s*\{[^}]*position: fixed;[^}]*right: 20px;[^}]*bottom: 20px;/s);
});
