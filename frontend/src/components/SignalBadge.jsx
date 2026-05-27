import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSentimentStore } from '../store/useSentimentStore';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import axios from 'axios';

const SignalBadge = () => {
    const { signal, newsFeed, currentTicker } = useSentimentStore();

    // Poll signal every 30 seconds as fallback
    useEffect(() => {
        if (!currentTicker) return;
        
        const fetchSignal = async () => {
            try {
                const res = await axios.get(`http://localhost:8000/api/signal/${currentTicker}`);
                if (res.data && res.data.signal) {
                    useSentimentStore.setState({ signal: res.data.signal });
                }
            } catch (err) {
                console.error("Error polling signal:", err);
            }
        };

        const intervalId = setInterval(fetchSignal, 30000);
        return () => clearInterval(intervalId);
    }, [currentTicker]);

    const config = {
        BUY: {
            color: 'bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-[#00f0ff]/40 to-transparent border border-[#00f0ff]/50',
            text: 'text-[#00f0ff] drop-shadow-[0_0_15px_rgba(0,240,255,0.8)]',
            icon: <TrendingUp className="w-10 h-10 text-[#00f0ff] drop-shadow-[0_0_10px_rgba(0,240,255,1)]" />,
            glow: 'rgba(0, 240, 255, 0.5)'
        },
        SELL: {
            color: 'bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-[#ff00e5]/40 to-transparent border border-[#ff00e5]/50',
            text: 'text-[#ff00e5] drop-shadow-[0_0_15px_rgba(255,0,229,0.8)]',
            icon: <TrendingDown className="w-10 h-10 text-[#ff00e5] drop-shadow-[0_0_10px_rgba(255,0,229,1)]" />,
            glow: 'rgba(255, 0, 229, 0.5)'
        },
        HOLD: {
            color: 'bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-[#7000ff]/40 to-transparent border border-[#7000ff]/50',
            text: 'text-[#7000ff] drop-shadow-[0_0_15px_rgba(112,0,255,0.8)]',
            icon: <Minus className="w-10 h-10 text-[#7000ff] drop-shadow-[0_0_10px_rgba(112,0,255,1)]" />,
            glow: 'rgba(112, 0, 255, 0.5)'
        }
    };

    const current = config[signal] || config.HOLD;

    // Calculate averages
    const newsItems = newsFeed.filter(item => item.source === 'news');
    const redditItems = newsFeed.filter(item => item.source === 'reddit');
    const newsAvg = newsItems.length ? newsItems.reduce((acc, curr) => acc + curr.score, 0) / newsItems.length : 0;
    const redditAvg = redditItems.length ? redditItems.reduce((acc, curr) => acc + curr.score, 0) / redditItems.length : 0;

    return (
        <div className="flex flex-col items-center justify-between p-6 glass-card rounded-2xl relative overflow-hidden group shadow-2xl h-auto min-h-[300px] shrink-0">
            <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/40 pointer-events-none" />
            
            <div className="w-full flex justify-between items-center mb-2 relative z-10">
                <span className="text-slate-400 text-[10px] font-black uppercase tracking-[0.2em] flex items-center gap-2">
                    Decision Engine
                </span>
                <div className="flex items-center gap-1.5 bg-black/20 px-2 py-1 rounded-full border border-white/5">
                    <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${signal === 'BUY' ? 'bg-[#00f0ff]' : signal === 'SELL' ? 'bg-[#ff00e5]' : 'bg-[#7000ff]'}`} />
                    <span className="text-[9px] font-bold text-slate-300 uppercase tracking-widest">Active</span>
                </div>
            </div>
            
            <div className="flex-1 flex flex-col items-center justify-center w-full relative z-10 py-6">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={signal}
                        initial={{ scale: 0.5, opacity: 0, rotateX: 90 }}
                        animate={{ 
                            scale: 1, 
                            opacity: 1,
                            rotateX: 0,
                            transition: { type: 'spring', stiffness: 200, damping: 15 }
                        }}
                        exit={{ scale: 0.5, opacity: 0, rotateX: -90 }}
                        className="flex flex-col items-center gap-5"
                    >
                        <div className={`p-6 rounded-full ${current.color} shadow-2xl relative overflow-hidden group-hover:scale-110 transition-transform duration-700 backdrop-blur-md`}>
                            <motion.div
                                animate={{ 
                                    scale: [1, 1.2, 1],
                                    opacity: [0.3, 0, 0.3]
                                }}
                                transition={{ 
                                    duration: 2, 
                                    repeat: Infinity,
                                    ease: "easeInOut"
                                }}
                                className="absolute inset-0 bg-white rounded-full"
                            />
                            <div className="relative z-10 text-white">
                                {current.icon}
                            </div>
                        </div>
                        
                        <div className="text-center mt-[-10px]">
                            <motion.span 
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className={`text-5xl font-black italic tracking-tighter uppercase ${current.text}`}
                            >
                                {signal}
                            </motion.span>
                        </div>
                    </motion.div>
                </AnimatePresence>
            </div>

            <div className="w-full grid grid-cols-3 gap-2 mt-auto pt-4 border-t border-white/10 relative z-10">
                <div className="flex flex-col items-center group/stat">
                    <span className="text-[9px] text-slate-400 uppercase font-bold tracking-widest mb-1 group-hover/stat:text-[#00f0ff] transition-colors">News Avg</span>
                    <span className={`text-sm font-mono font-bold ${newsAvg > 0 ? 'text-[#00f0ff] drop-shadow-[0_0_3px_rgba(0,240,255,0.8)]' : newsAvg < 0 ? 'text-[#ff00e5]' : 'text-slate-400'}`}>
                        {newsAvg > 0 ? '+' : ''}{newsAvg.toFixed(2)}
                    </span>
                </div>
                <div className="flex flex-col items-center border-l border-r border-white/10 group/stat">
                    <span className="text-[9px] text-slate-400 uppercase font-bold tracking-widest mb-1 group-hover/stat:text-[#7000ff] transition-colors">Reddit Avg</span>
                    <span className={`text-sm font-mono font-bold ${redditAvg > 0 ? 'text-[#00f0ff] drop-shadow-[0_0_3px_rgba(0,240,255,0.8)]' : redditAvg < 0 ? 'text-[#ff00e5]' : 'text-slate-400'}`}>
                        {redditAvg > 0 ? '+' : ''}{redditAvg.toFixed(2)}
                    </span>
                </div>
                <div className="flex flex-col items-center group/stat">
                    <span className="text-[9px] text-slate-400 uppercase font-bold tracking-widest mb-1 group-hover/stat:text-white transition-colors">Articles</span>
                    <span className="text-sm font-mono font-bold text-white drop-shadow-[0_0_3px_rgba(255,255,255,0.5)]">
                        {newsFeed.length}
                    </span>
                </div>
            </div>
        </div>
    );
};

export default SignalBadge;
