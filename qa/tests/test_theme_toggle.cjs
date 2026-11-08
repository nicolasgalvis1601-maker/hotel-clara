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
  const buttons = Array.from({ length: 2 }, () => {
    const attributes = {};
    const listeners = {};
    const label = { textContent: '' };
    return {
      attributes,
      listeners,
      label,
      setAttribute: (name, value) => { attributes[name] = value; },
      addEventListener: (name, callback) => { listeners[name] = callback; },
      querySelector: () => label,
    };
  });
  const context = createContext({
    document: {
      documentElement: { dataset: { theme: 'light' } },
    },
    themeToggleButtons: buttons,
    localStorage: {
      value: 'dark',
      getItem() { return this.value; },
      setItem(key, value) { this.key = key; this.value = value; },
    },
  });
  runInContext(`${key[0]};${setTheme[0]};${initializeTheme[0]};initializeTheme();`, context);

  assert.equal(context.document.documentElement.dataset.theme, 'dark');
  buttons.forEach((button) => {
    assert.equal(button.attributes['aria-pressed'], 'true');
    assert.equal(button.attributes['aria-label'], 'Cambiar a modo claro');
    assert.equal(button.label.textContent, 'Modo oscuro');
  });
  assert.equal(context.localStorage.key, 'hotel_theme');
  buttons[0].listeners.click();
  assert.equal(context.document.documentElement.dataset.theme, 'light');
  buttons.forEach((button) => {
    assert.equal(button.attributes['aria-pressed'], 'false');
    assert.equal(button.attributes['aria-label'], 'Cambiar a modo oscuro');
    assert.equal(button.label.textContent, 'Modo claro');
  });
  assert.equal(context.localStorage.value, 'light');
});

test('el selector de tema usa iconos junto a bienvenida y en reservas', () => {
  assert.equal((html.match(/data-theme-toggle/g) || []).length, 2);
  assert.match(html, /auth-topline[\s\S]*?BIENVENIDO[\s\S]*?data-theme-toggle/);
  assert.match(html, /booking-header[\s\S]*?data-theme-toggle/);
  assert.match(html, /theme-icon-sun/);
  assert.match(html, /theme-icon-moon/);
  assert.match(html, /theme-toggle-label/);
  assert.doesNotMatch(html, /CONEXIÓN SEGURA/i);
  assert.match(styles, /:root\[data-theme="light"\] \.theme-icon-sun/);
  assert.match(styles, /:root\[data-theme="dark"\] \.theme-icon-moon/);
  assert.match(styles, /:root\[data-theme="dark"\]/);
  assert.match(styles, /--surface: #1e293b/);
  assert.match(styles, /--ink: #e2e8f0/);
  assert.match(styles, /\.theme-toggle\s*\{[^}]*font-size: 14px;/s);
  assert.doesNotMatch(styles, /\.theme-toggle\s*\{[^}]*position: fixed;/s);
});
