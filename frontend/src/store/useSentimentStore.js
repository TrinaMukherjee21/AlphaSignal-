import { create } from 'zustand';
import axios from 'axios';

const API_BASE = "http://localhost:8000/api";
const WS_BASE = "ws://localhost:8000/ws";

export const useSentimentStore = create((set, get) => ({
    currentTicker: "AAPL",
    scores: [],
    signal: "HOLD",
    priceData: [],
    newsFeed: [],
    timeframe: '1D',
    ws: null,

    wsStatus: 'connecting',

    setTicker: async (ticker) => {
        const { connectWebSocket } = get();
        set({ currentTicker: ticker, scores: [], newsFeed: [], priceData: [], wsStatus: 'connecting', timeframe: '1D' });
        
        // Fetch initial data
        try {
            const [sentimentRes, priceRes, signalRes] = await Promise.all([
                axios.get(`${API_BASE}/sentiment/${ticker}`),
                axios.get(`${API_BASE}/prices/${ticker}`),
                axios.get(`${API_BASE}/signal/${ticker}`)
            ]);
            
            set({ 
                scores: sentimentRes.data,
                priceData: priceRes.data,
                signal: signalRes.data.signal,
                newsFeed: sentimentRes.data // News feed is basically historical sentiment here
            });
            
            connectWebSocket(ticker);
        } catch (error) {
            console.error("Error fetching initial ticker data:", error);
        }
    },

    setTimeframe: async (tf) => {
        set({ timeframe: tf });
        const { currentTicker } = get();
        if (!currentTicker) return;

        let period = '1d';
        if (tf === '1W') period = '1wk';
        if (tf === '1M') period = '1mo';

        try {
            const priceRes = await axios.get(`${API_BASE}/prices/${currentTicker}?period=${period}`);
            set({ priceData: priceRes.data });
        } catch (error) {
            console.error("Error fetching timeframe relative data:", error);
        }
    },

    connectWebSocket: (ticker, retryDelay = 1000) => {
        const { ws: oldWs } = get();
        if (oldWs) oldWs.close();

        set({ wsStatus: 'connecting' });
        const ws = new WebSocket(`${WS_BASE}/${ticker}`);
        
        ws.onopen = () => {
            set({ wsStatus: 'connected' });
        };

        const handleReconnect = () => {
            // Only reconnect if we're still on the same ticker
            if (get().currentTicker !== ticker) return;
            set({ wsStatus: 'reconnecting' });
            const nextDelay = Math.min(retryDelay * 2, 30000);
            console.log(`[WS] Reconnecting ${ticker} in ${retryDelay}ms...`);
            setTimeout(() => get().connectWebSocket(ticker, nextDelay), retryDelay);
        };

        ws.onclose = handleReconnect;
        ws.onerror = () => ws.close(); // triggers onclose which handles reconnect
        
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            
            if (message.type === "sentiment" || message.score !== undefined) {
                // It's a sentiment update
                set((state) => ({
                    scores: [message, ...state.scores].slice(0, 100),
                    newsFeed: [message, ...state.newsFeed].slice(0, 100),
                    signal: message.signal || state.signal
                }));
            } else if (message.type === "price" || message.close !== undefined) {
                // It's a price update - but only append if we are looking at real-time 1D data
                if (get().timeframe === '1D') {
                    set((state) => ({
                        priceData: [...state.priceData, message].slice(-300)
                    }));
                }
            }
        };

        set({ ws });
    }
}));
