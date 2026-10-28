const { randomBytes } = require('node:crypto');
const { writeFileSync, existsSync } = require('node:fs');
const { resolve } = require('node:path');

const envPath = resolve(process.cwd(), '.env');
if (existsSync(envPath)) {
  throw new Error('Refusing to overwrite an existing .env file.');
}

const secret = () => randomBytes(48).toString('hex');
const contents = [
  'MONGODB_URI=mongodb://localhost:27017/',
  'MONGODB_DATABASE=hotel',
  `JWT_SECRET=${secret()}`,
  `ADMIN_SETUP_KEY=${secret()}`,
  'CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500',
  '',
].join('\n');

writeFileSync(envPath, contents, { flag: 'wx' });
console.log('Created ignored .env with unique secrets. Read ADMIN_SETUP_KEY locally for one-time admin setup.');
