import React, { useEffect, useState } from 'react';
import { useSentimentStore } from './store/useSentimentStore';
import TickerSearch from './components/TickerSearch';
import PriceChart from './components/PriceChart';
import SignalBadge from './components/SignalBadge';
import NewsFeed from './components/NewsFeed';
import NotificationManager from './components/NotificationManager';
import { TrendingUp, Clock, Globe } from 'lucide-react';
import { motion } from 'framer-motion';
import './App.css';

function App() {
  const { currentTicker, setTicker, priceData, scores, newsFeed, signal, wsStatus } = useSentimentStore();
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    setTicker(currentTicker);
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const getMarketStatus = () => {
    const day = time.getDay();
    const hour = time.getUTCHours();
    const minute = time.getUTCMinutes();
    
    // Constraints
    const isWeekend = day === 0 || day === 6;
    const usWorking = (hour === 14 && minute >= 30) || (hour > 14 && hour < 21);
    const inWorking = (hour === 3 && minute >= 45) || (hour > 3 && hour < 10);
    
    // Dynamic determination based on currently selected ticker
    const isIndianStock = currentTicker && (currentTicker.endsWith('.NS') || currentTicker.endsWith('.BO'));
    
    if (isIndianStock) {
        return isWeekend || !inWorking ? 
          { status: 'Closed', name: 'NSE', color: 'text-red-500 bg-red-500/10 border-red-500/30' } : 
          { status: 'Open', name: 'NSE', color: 'text-[#00f0ff] bg-[#00f0ff]/10 border-[#00f0ff]/30' };
    } else {
        return isWeekend || !usWorking ? 
          { status: 'Closed', name: 'NYSE', color: 'text-red-500 bg-red-500/10 border-red-500/30' } : 
          { status: 'Open', name: 'NYSE', color: 'text-[#00f0ff] bg-[#00f0ff]/10 border-[#00f0ff]/30' };
    }
  };

  const market = getMarketStatus();

  const currentPrice = priceData.length > 0 ? priceData[priceData.length - 1].close : 0;
  const currentSentiment = scores.length > 0 
    ? scores.reduce((acc, curr) => acc + curr.score, 0) / scores.length 
    : 0;
  
  const getSignalStrength = (score) => {
    const abs = Math.abs(score);
    if (abs > 0.6) return { text: 'Strong', color: 'text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]' };
    if (abs > 0.3) return { text: 'Moderate', color: 'text-slate-200' };
    return { text: 'Weak', color: 'text-slate-400' };
  };

  const signalStrength = getSignalStrength(currentSentiment);

  // Background blobs for extra depth
  const backgroundBlobs = (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-[-1]">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-[rgba(112,0,255,0.15)] rounded-full neo-blur animate-blob"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-[rgba(0,240,255,0.1)] rounded-full neo-blur animate-blob animation-delay-2000"></div>
      <div className="absolute top-[40%] left-[60%] w-[30%] h-[30%] bg-[rgba(255,0,229,0.1)] rounded-full neo-blur animate-blob animation-delay-4000"></div>
    </div>
  );

  return (
    <div className="min-h-screen text-slate-200 font-sans selection:bg-[#00f0ff]/30 relative overflow-hidden">
      <NotificationManager />
      {backgroundBlobs}
      
      {/* Top Navigation Bar - Frost Glass */}
      <motion.nav 
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="glass-panel border-b-0 border-opacity-20 sticky top-0 z-50 rounded-b-2xl mx-4 mt-2"
      >
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4 group cursor-pointer">
            <div className="bg-[#00f0ff]/10 border border-[#00f0ff]/30 p-2 rounded-lg group-hover:border-[#00f0ff] transition-colors duration-300 relative overflow-hidden">
              <div className="absolute inset-0 bg-[#00f0ff]/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
              <TrendingUp className="text-[#00f0ff] w-5 h-5 relative z-10 group-hover:scale-110 transition-transform" />
            </div>
            <span className="text-2xl font-black tracking-tight text-white flex items-center">
              Alpha<span className="text-gradient ml-1">Signal</span>
            </span>
          </div>

          <div className="flex items-center gap-6">
            <div className="hidden lg:flex items-center gap-4 px-5 py-2 glass-card rounded-xl">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-[#00f0ff]" />
                <span className="text-xs font-mono text-slate-200 font-semibold tracking-wider">
                  {time.toLocaleTimeString([], { hour12: false })}
                </span>
              </div>
              <div className="w-px h-4 bg-white/10" />
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-[#7000ff]" />
                <span className={`text-[10px] font-bold uppercase ${market.color} border px-2 py-0.5 rounded shadow-sm`}>
                  {market.name}: {market.status}
                </span>
              </div>
              <div className="w-px h-4 bg-white/10" />
              <div className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-full ${wsStatus === 'connected' ? 'bg-[#00f0ff] shadow-[0_0_10px_rgba(0,240,255,0.8)]' : wsStatus === 'connecting' ? 'bg-[#ff00e5] animate-pulse' : 'bg-red-500 animate-pulse'}`} />
                <span className="text-[10px] font-bold text-slate-300 uppercase tracking-widest w-[80px]">
                    {wsStatus === 'connected' ? 'Live Feed' : wsStatus === 'connecting' ? 'Connecting' : 'Reconnecting'}
                </span>
              </div>
            </div>
            <TickerSearch />
          </div>
        </div>
      </motion.nav>

      <main className="max-w-[1600px] mx-auto p-4 lg:p-6 flex flex-col gap-6 mt-2">
        
        {/* Stats Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { 
              label: 'Current Price', 
              value: `$${currentPrice > 0 ? currentPrice.toFixed(2) : '---'}`, 
              color: 'text-white' 
            },
            { 
              label: 'Net Sentiment', 
              value: `${currentSentiment > 0 ? '+' : ''}${currentSentiment ? currentSentiment.toFixed(3) : '0.000'}`, 
              color: currentSentiment > 0 ? 'text-[#00f0ff] drop-shadow-[0_0_5px_rgba(0,240,255,0.5)]' : currentSentiment < 0 ? 'text-[#ff00e5]' : 'text-slate-400'
            },
            { 
              label: 'Event Volume', 
              value: newsFeed.length, 
              sub: 'items',
              color: 'text-white' 
            },
            { 
              label: 'Signal Strength', 
              value: signalStrength.text, 
              sub: `(${signal})`, 
              color: signalStrength.color,
              uppercase: true
            }
          ].map((stat, idx) => (
            <motion.div 
              key={idx}
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.4, delay: idx * 0.1 }}
              className="glass-card rounded-2xl p-5 flex flex-col justify-between group overflow-hidden relative"
            >
              <div className="absolute top-0 right-0 w-24 h-24 bg-white/5 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2 group-hover:bg-[#00f0ff]/10 transition-colors duration-500"></div>
              <span className="text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-2 z-10">{stat.label}</span>
              <span className={`text-3xl font-mono tracking-tight z-10 ${stat.uppercase ? 'uppercase text-2xl' : ''} ${stat.color}`}>
                {stat.value} {stat.sub && <span className="text-sm text-slate-500 ml-1 nornal-case font-sans tracking-normal">{stat.sub}</span>}
              </span>
            </motion.div>
          ))}
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-280px)] min-h-[600px]">
          
          {/* Chart Section */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="lg:col-span-3 flex flex-col gap-4 overflow-hidden"
          >
            <div className="flex items-center justify-between px-2">
              <h2 className="text-xs font-bold text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#7000ff] animate-pulse"></span>
                Price & Sentiment Core
              </h2>
            </div>
            <div className="flex-1 min-h-0 glass-card rounded-2xl overflow-hidden shadow-2xl relative">
              <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] to-transparent pointer-events-none"></div>
              <PriceChart />
            </div>
          </motion.div>

          {/* Intelligence Section */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="lg:col-span-1 flex flex-col gap-6 h-full overflow-hidden"
          >
            <SignalBadge />
            <div className="flex-1 min-h-0">
              <NewsFeed />
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}

export default App;
