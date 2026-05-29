const isProd = typeof window !== 'undefined' && window.location.hostname !== 'localhost';
const default_backend = isProd ? "trade-sentiment-backend.onrender.com" : "localhost:8000";

export const API_BASE = import.meta.env.VITE_API_URL || (isProd ? `https://${default_backend}/api` : `http://${default_backend}/api`);
export const WS_BASE = import.meta.env.VITE_WS_URL || (isProd ? `wss://${default_backend}/ws` : `ws://${default_backend}/ws`);
