const { spawn } = require('node:child_process');
const { existsSync } = require('node:fs');
const { resolve } = require('node:path');

const root = resolve(__dirname, '..', '..');

function startDev(args = process.argv.slice(2)) {
  process.chdir(root);
  if (!existsSync(resolve(root, '.env'))) {
    require('./setup-local-env.js');
  }

  const virtualPython = process.platform === 'win32'
    ? resolve(root, '.venv', 'Scripts', 'python.exe')
    : resolve(root, '.venv', 'bin', 'python');
  const python = existsSync(virtualPython) ? virtualPython : 'python';
  const server = spawn(python, [
    '-m', 'uvicorn', 'backend.app:app', '--reload', ...args,
  ], { cwd: root, stdio: 'inherit' });

  server.on('error', (error) => {
    console.error(`No se pudo iniciar Python: ${error.message}`);
    console.error('Instala Python y las dependencias con: python -m pip install -r requirements.txt');
    process.exitCode = 1;
  });
  server.on('exit', (code, signal) => {
    process.exitCode = code ?? (signal === 'SIGINT' ? 0 : 1);
  });
  process.on('SIGINT', () => {
    server.kill('SIGINT');
  });
  process.on('SIGTERM', () => {
    server.kill('SIGTERM');
  });
  return server;
}

if (require.main === module) {
  startDev();
}

module.exports = { startDev };
