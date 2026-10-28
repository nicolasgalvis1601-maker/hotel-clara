// Conexión del frontend con la API (backend FastAPI).
//
// En Render el mismo servicio entrega la página y la API, así que la URL queda
// vacía y el navegador llama a "/api/..." en el mismo dominio. No cambies nada.
//
// Solo si publicas el frontend en otro sitio (por ejemplo GitHub Pages), escribe
// aquí la URL HTTPS de tu servicio en Render, sin "/" al final, y agrega ese
// dominio de GitHub Pages a la variable CORS_ORIGINS en Render.
const RENDER_API_URL = 'https://hotel-clara.onrender.com';

window.HOTEL_API_BASE_URL = window.location.hostname.endsWith('github.io') ? RENDER_API_URL : '';
