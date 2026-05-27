import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { useSentimentStore } from '../store/useSentimentStore';
import { Search, ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const TickerSearch = () => {
    const [tickers, setTickers] = useState([]);
    const [isOpen, setIsOpen] = useState(false);
    const { currentTicker, setTicker } = useSentimentStore();
    const dropdownRef = useRef(null);

    useEffect(() => {
        axios.get("http://localhost:8000/api/tickers")
            .then(res => setTickers(res.data))
            .catch(err => console.error(err));
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
                        className="absolute top-[calc(100%+8px)] left-0 right-0 glass-card rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.5)] overflow-hidden z-50 py-2 border border-[#00f0ff]/20"
                    >
                        {tickers.map((t, idx) => (
                            <motion.div
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: idx * 0.05 }}
                                key={t}
                                onClick={() => {
                                    setTicker(t);
                                    setIsOpen(false);
                                }}
                                className={`px-5 py-2.5 cursor-pointer font-mono font-bold text-sm transition-all relative overflow-hidden group ${
                                    currentTicker === t 
                                        ? 'text-[#00f0ff] bg-[#00f0ff]/10 border-l-2 border-[#00f0ff]' 
                                        : 'text-slate-300 hover:text-white border-l-2 border-transparent'
                                }`}
                            >
                                <div className="absolute inset-0 bg-gradient-to-r from-white/5 to-transparent translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-300"></div>
                                <span className="relative z-10">{t}</span>
                            </motion.div>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default TickerSearch;
