import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { useSentimentStore } from '../store/useSentimentStore';
import { Search, ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { API_BASE } from '../config';

const TickerSearch = () => {
    const [tickers, setTickers] = useState([]);
    const [isOpen, setIsOpen] = useState(false);
    const { currentTicker, setTicker } = useSentimentStore();
    const dropdownRef = useRef(null);

    useEffect(() => {
        let retries = 0;
        const fetchTickers = () => {
            axios.get(`${API_BASE}/tickers`)
                .then(res => {
                    if (res.data && res.data.length > 0) {
                        setTickers(res.data);
                    } else if (retries < 5) {
                        retries++;
                        setTimeout(fetchTickers, 3000);
                    }
                })
                .catch(err => {
                    console.error("Ticker fetch error:", err);
                    if (retries < 5) {
                        retries++;
                        setTimeout(fetchTickers, 3000);
                    }
                });
        };
        fetchTickers();
    }, []);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <div className="relative flex items-center" ref={dropdownRef}>
            <Search className="absolute left-4 text-[#00f0ff] w-4 h-4 z-10 pointer-events-none drop-shadow-[0_0_5px_rgba(0,240,255,0.5)]" />
            
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="pl-12 pr-10 py-2 glass-panel border border-white/10 hover:border-[#00f0ff]/50 rounded-xl text-white font-mono focus:outline-none transition-all cursor-pointer min-w-[160px] flex items-center justify-between shadow-[0_4px_20px_rgba(0,0,0,0.3)] relative group overflow-hidden"
            >
                <div className="absolute inset-0 bg-gradient-to-r from-[#00f0ff]/0 via-[#00f0ff]/5 to-[#00f0ff]/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 ease-in-out"></div>
                <span className="relative z-10 tracking-widest font-bold">{currentTicker || 'Select...'}</span>
                <ChevronDown className={`absolute right-3 w-4 h-4 text-[#7000ff] transition-transform duration-300 relative z-10 ${isOpen ? 'rotate-180 text-[#00f0ff]' : ''}`} />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div 
                        initial={{ opacity: 0, y: -10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                        className="absolute top-[calc(100%+8px)] left-0 right-0 bg-[#05050a] rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.8)] overflow-hidden z-50 py-2 border border-[#00f0ff]/20"
                    >
                        {(() => {
                            const inTickers = tickers.filter(t => t.endsWith('.NS') || t.endsWith('.BO'));
                            const usTickers = tickers.filter(t => !t.endsWith('.NS') && !t.endsWith('.BO'));
                            
                            const renderTicker = (t) => (
                                <motion.div
                                    key={t}
                                    onClick={() => { setTicker(t); setIsOpen(false); }}
                                    className={`px-5 py-2.5 cursor-pointer font-mono font-bold text-sm transition-all relative overflow-hidden group ${
                                        currentTicker === t 
                                            ? 'text-[#00f0ff] bg-[#00f0ff]/10 border-l-2 border-[#00f0ff]' 
                                            : 'text-slate-300 hover:text-white border-l-2 border-transparent'
                                    }`}
                                >
                                    <div className="absolute inset-0 bg-gradient-to-r from-white/5 to-transparent translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-300"></div>
                                    <span className="relative z-10">{t}</span>
                                </motion.div>
                            );

                            return (
                                <>
                                    <div className="px-3 pb-2 pt-1 border-b border-white/10 mb-2">
                                        <input
                                            type="text"
                                            placeholder="Add new ticker (e.g. MSFT)..."
                                            className="w-full bg-black/40 border border-white/10 rounded px-3 py-1.5 text-white font-mono text-xs focus:outline-none focus:border-[#00f0ff] transition-colors shadow-inner"
                                            onClick={(e) => e.stopPropagation()}
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter' && e.target.value) {
                                                    const val = e.target.value.trim().toUpperCase();
                                                    if (!tickers.includes(val)) {
                                                        const inputEl = e.target;
                                                        inputEl.disabled = true;
                                                        inputEl.placeholder = 'Validating...';
                                                        axios.post(`${API_BASE}/tickers/${val}`)
                                                            .then(() => {
                                                                setTickers(prev => [...prev, val]);
                                                                setTicker(val);
                                                                setIsOpen(false);
                                                            })
                                                            .catch(err => {
                                                                alert(err.response?.data?.detail || 'Error validating ticker');
                                                                inputEl.disabled = false;
                                                                inputEl.placeholder = 'Add new ticker (e.g. MSFT)...';
                                                                inputEl.value = '';
                                                            });
                                                    } else {
                                                        setTicker(val);
                                                        setIsOpen(false);
                                                    }
                                                }
                                            }}
                                        />
                                    </div>
                                    {usTickers.length > 0 && (
                                        <div className="px-3 pt-2 pb-1 text-[10px] uppercase font-black tracking-widest text-[#00f0ff] flex items-center gap-2">
                                            <div className="w-1.5 h-3 bg-[#00f0ff] rounded-full drop-shadow-[0_0_5px_rgba(0,240,255,0.8)]"></div> US Markets
                                        </div>
                                    )}
                                    {usTickers.map(t => renderTicker(t))}

                                    {inTickers.length > 0 && (
                                        <div className="px-3 pt-3 pb-1 text-[10px] uppercase font-black tracking-widest text-[#ff00e5] flex items-center gap-2 border-t border-white/5 mt-1">
                                            <div className="w-1.5 h-3 bg-[#ff00e5] rounded-full drop-shadow-[0_0_5px_rgba(255,0,229,0.8)]"></div> Indian Markets (NSE)
                                        </div>
                                    )}
                                    {inTickers.map(t => renderTicker(t))}
                                </>
                            );
                        })()}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default TickerSearch;
