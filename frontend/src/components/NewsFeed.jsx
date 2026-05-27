import React from 'react';
import { useSentimentStore } from '../store/useSentimentStore';
import { ExternalLink, Clock, BrainCircuit } from 'lucide-react';
import { motion } from 'framer-motion';

const NewsFeed = () => {
    const { newsFeed } = useSentimentStore();

    // Helper to decode HTML entities like &amp;
    const decodeHTMLEntities = (text) => {
        const textArea = document.createElement('textarea');
        textArea.innerHTML = text;
        return textArea.value;
    };

    const getSentimentStyles = (score) => {
        if (score > 0.3) return {
            pill: 'bg-[#00f0ff]/10 text-[#00f0ff] border-[#00f0ff]/30 shadow-[0_0_10px_rgba(0,240,255,0.2)]',
            border: 'border-l-[#00f0ff]',
            label: 'Strong Buy'
        };
        if (score < -0.3) return {
            pill: 'bg-[#ff00e5]/10 text-[#ff00e5] border-[#ff00e5]/30 shadow-[0_0_10px_rgba(255,0,229,0.2)]',
            border: 'border-l-[#ff00e5]',
            label: 'Strong Sell'
        };
        return {
            pill: 'bg-white/5 text-slate-300 border-white/10 shadow-sm',
            border: 'border-l-slate-500',
            label: 'Neutral'
        };
    };

    // Animation variants for stagger effects
    const containerVariants = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: { staggerChildren: 0.1 }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, x: 20 },
        show: { opacity: 1, x: 0, transition: { type: 'spring', stiffness: 300, damping: 24 } }
    };

    return (
        <div className="flex flex-col h-full glass-card rounded-2xl overflow-hidden shadow-2xl relative group pb-2">
            <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] to-transparent pointer-events-none" />
            
            <div className="px-5 py-4 border-b border-white/10 bg-black/20 flex justify-between items-center backdrop-blur-md z-10 relative">
                <div className="flex items-center gap-2">
                    <BrainCircuit className="w-4 h-4 text-[#00f0ff] animate-pulse" />
                    <h3 className="text-white font-bold text-[11px] tracking-[0.2em] uppercase">Intelligence Feed</h3>
                </div>
                <div className="flex items-center gap-2 bg-black/30 px-2.5 py-1 rounded-full border border-white/5">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00f0ff] opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00f0ff]"></span>
                    </span>
                    <span className="text-[9px] font-black text-slate-300 uppercase tracking-widest">{newsFeed.length} Events</span>
                </div>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar bg-transparent z-10 relative">
                {newsFeed.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-slate-500">
                        <Clock className="w-8 h-8 mb-3 animate-pulse text-[#7000ff]" />
                        <p className="text-[10px] font-bold uppercase tracking-[0.2em]">Scanning Networks...</p>
                    </div>
                ) : (
                    <motion.div 
                        variants={containerVariants}
                        initial="hidden"
                        animate="show"
                        className="space-y-3"
                    >
                        {newsFeed.map((item, i) => {
                            const styles = getSentimentStyles(item.score);
                            return (
                                <motion.div 
                                    variants={itemVariants}
                                    key={i} 
                                    className={`p-4 bg-black/20 backdrop-blur-md rounded-xl border border-white/5 border-l-4 ${styles.border} hover:bg-black/40 hover:border-white/20 transition-all group/item shadow-lg relative overflow-hidden`}
                                >
                                    <div className="absolute inset-0 bg-gradient-to-r from-white/5 to-transparent translate-x-[-100%] group-hover/item:translate-x-0 transition-transform duration-500 ease-out pointer-events-none" />
                                    
                                    <div className="flex justify-between items-start mb-3 relative z-10">
                                        <div className="flex items-center gap-2">
                                            <span className={`text-[9px] font-mono font-black px-2.5 py-1 rounded border uppercase tracking-tighter ${styles.pill}`}>
                                                {styles.label} ({item.score?.toFixed(2)})
                                            </span>
                                        </div>
                                        <span className="text-[9px] font-mono text-slate-500 flex items-center group-hover/item:text-[#00f0ff] transition-colors">
                                            <Clock className="w-2.5 h-2.5 mr-1" />
                                            {new Date(item.timestamp || item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                        </span>
                                    </div>
                                    <h4 className="text-slate-300 text-sm font-medium leading-relaxed mb-4 group-hover/item:text-white transition-colors relative z-10 drop-shadow-sm">
                                        {decodeHTMLEntities(item.headline || item.title)}
                                    </h4>
                                    <div className="flex justify-between items-center mt-auto pt-3 border-t border-white/5 relative z-10">
                                        <div className="flex items-center gap-2">
                                            <div className="w-1.5 h-1.5 rounded-full bg-[#7000ff]/50 drop-shadow-[0_0_2px_rgba(112,0,255,0.8)]" />
                                            <span className="text-[9px] text-slate-400 uppercase font-black tracking-widest">{item.source}</span>
                                        </div>
                                        {item.url && (
                                            <a href={item.url} target="_blank" rel="noreferrer" className="text-slate-500 hover:text-[#00f0ff] p-1.5 rounded-lg hover:bg-[#00f0ff]/10 transition-all group-hover/item:shadow-[0_0_10px_rgba(0,240,255,0.2)]">
                                                <ExternalLink className="w-3.5 h-3.5" />
                                            </a>
                                        )}
                                    </div>
                                </motion.div>
                            );
                        })}
                    </motion.div>
                )}
            </div>
        </div>
    );
};

export default NewsFeed;
