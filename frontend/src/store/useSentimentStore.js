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
    ws: null,

    wsStatus: 'connecting',

    setTicker: async (ticker) => {
        const { connectWebSocket } = get();
        set({ currentTicker: ticker, scores: [], newsFeed: [], priceData: [], wsStatus: 'connecting' });
        
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

    connectWebSocket: (ticker) => {
        const { ws: oldWs } = get();
        if (oldWs) oldWs.close();

        set({ wsStatus: 'connecting' });
        const ws = new WebSocket(`${WS_BASE}/${ticker}`);
        
        ws.onopen = () => set({ wsStatus: 'connected' });
        ws.onclose = () => set({ wsStatus: 'reconnecting' });
        ws.onerror = () => set({ wsStatus: 'reconnecting' });
        
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
                // It's a price update
                set((state) => ({
                    priceData: [...state.priceData, message].slice(-200)
                }));
            }
        };

        set({ ws });
    }
}));
