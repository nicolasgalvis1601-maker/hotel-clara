const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const fs = require('node:fs');
const childProcess = require('node:child_process');
const { resolve } = require('node:path');
const { test } = require('node:test');

const root = resolve(__dirname, '..', '..');
const launcher = resolve(root, 'backend', 'scripts', 'dev.js');

function launch(t, virtualenv, args = [], envExists = true) {
  const server = new EventEmitter();
  server.kill = t.mock.fn();
  const spawn = t.mock.method(childProcess, 'spawn', () => server);
  t.mock.method(fs, 'existsSync', (path) => (
    path === resolve(root, '.env') ? envExists : virtualenv
  ));
  const originalExitCode = process.exitCode;
  const originalDirectory = process.cwd();
  const interruptListeners = process.listeners('SIGINT');
  const terminateListeners = process.listeners('SIGTERM');
  t.after(() => {
    process.exitCode = originalExitCode;
    process.chdir(originalDirectory);
    for (const [signal, original] of [
      ['SIGINT', interruptListeners], ['SIGTERM', terminateListeners],
    ]) {
      for (const listener of process.listeners(signal)) {
        if (!original.includes(listener)) process.removeListener(signal, listener);
      }
    }
    delete require.cache[launcher];
    delete require.cache[resolve(root, 'backend', 'scripts', 'setup-local-env.js')];
  });
  delete require.cache[launcher];
  require(launcher).startDev(args);
  return { server, call: spawn.mock.calls[0].arguments };
}

test('dev usa el entorno virtual y sirve frontend y API con recarga', (t) => {
  const { call } = launch(t, true);
  const expected = process.platform === 'win32'
    ? resolve(root, '.venv', 'Scripts', 'python.exe')
    : resolve(root, '.venv', 'bin', 'python');
  assert.equal(call[0], expected);
  assert.deepEqual(call[1], ['-m', 'uvicorn', 'backend.app:app', '--reload']);
  assert.deepEqual(call[2], { cwd: root, stdio: 'inherit' });
});

test('dev usa Python del PATH sin entorno virtual y transmite opciones', (t) => {
  const { call } = launch(t, false, ['--port', '8001']);
  assert.equal(call[0], 'python');
  assert.deepEqual(call[1].slice(-2), ['--port', '8001']);
});

test('dev crea configuracion con secretos nuevos solamente si falta .env', (t) => {
  const write = t.mock.method(fs, 'writeFileSync', () => {});
  t.mock.method(console, 'log', () => {});
  launch(t, false, [], false);
  assert.equal(write.mock.calls.length, 1);
  const [path, contents, options] = write.mock.calls[0].arguments;
  assert.equal(path, resolve(root, '.env'));
  assert.match(contents, /JWT_SECRET=[a-f0-9]{96}/);
  assert.match(contents, /ADMIN_SETUP_KEY=[a-f0-9]{96}/);
  assert.deepEqual(options, { flag: 'wx' });
});

test('dev no sobrescribe la configuracion existente', (t) => {
  const write = t.mock.method(fs, 'writeFileSync', () => {});
  launch(t, false);
  assert.equal(write.mock.calls.length, 0);
});

test('dev conserva el codigo de salida fallido del servidor', (t) => {
  const { server } = launch(t, false);
  server.emit('exit', 3, null);
  assert.equal(process.exitCode, 3);
});

test('dev informa cuando Python no se puede ejecutar', (t) => {
  const log = t.mock.method(console, 'error', () => {});
  const { server } = launch(t, false);
  server.emit('error', new Error('spawn python ENOENT'));
  assert.equal(process.exitCode, 1);
  assert.match(log.mock.calls[0].arguments[0], /ENOENT/);
  assert.match(log.mock.calls[1].arguments[0], /requirements\.txt/);
});

test('dev transmite la interrupcion al servidor', (t) => {
  const { server } = launch(t, false);
  process.emit('SIGINT');
  assert.deepEqual(server.kill.mock.calls[0].arguments, ['SIGINT']);
  server.emit('exit', null, 'SIGINT');
  assert.equal(process.exitCode, 0);
});

test('dev transmite la terminacion al servidor', (t) => {
  const { server } = launch(t, false);
  process.emit('SIGTERM');
  assert.deepEqual(server.kill.mock.calls[0].arguments, ['SIGTERM']);
});
