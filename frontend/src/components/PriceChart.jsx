import React, { useMemo, useEffect, useState } from 'react';
import { 
    ComposedChart, 
    Bar, 
    XAxis, 
    YAxis, 
    CartesianGrid, 
    Tooltip, 
    ResponsiveContainer, 
    Cell,
    Line,
    Area,
    ReferenceLine,
    ReferenceDot
} from 'recharts';
import { useSentimentStore } from '../store/useSentimentStore';
import { TrendingUp, Zap } from 'lucide-react';

const PriceChart = () => {
    const { priceData, scores, timeframe, setTimeframe } = useSentimentStore();
    const [flash, setFlash] = useState(false);

    // Trigger flash animation on data updates
    useEffect(() => {
        if (priceData.length > 0) {
            setFlash(true);
            const timer = setTimeout(() => setFlash(false), 1000);
            return () => clearTimeout(timer);
        }
    }, [priceData.length]);

    // Process Data
    const fullData = useMemo(() => {
        if (!priceData || priceData.length === 0) return [];
        
        let merged = priceData.map((p) => {
            let ts = p.timestamp;
            let dateObj;
            if (typeof ts === 'string') {
                dateObj = new Date(ts.endsWith('Z') || ts.includes('+') ? ts : ts + 'Z');
                if (isNaN(dateObj.getTime())) dateObj = new Date(ts);
            } else if (typeof ts === 'number') {
                dateObj = new Date(ts < 20000000000 ? ts * 1000 : ts);
            } else {
                dateObj = new Date();
            }
            
            const isHistorical = timeframe === '1W' || timeframe === '1M';
            
            const timeStr = !isNaN(dateObj.getTime()) 
                ? isHistorical 
                    ? dateObj.toLocaleDateString([], { month: 'short', day: '2-digit' }) + ' ' + dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
                    : dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }) 
                : '??:??';

            const s = scores.find(s => Math.abs(new Date(s.timestamp).getTime() - dateObj.getTime()) < 60000);
            
            return {
                ...p,
                time: timeStr,
                rawTime: dateObj.getTime(),
                sentiment: s ? s.score : 0,
                news: s ? s.text : null,
                close: p.close || 0,
                high: p.high || p.close || 0,
                low: p.low || p.close || 0,
                volume: p.volume || 0
            };
        });

        merged.sort((a, b) => a.rawTime - b.rawTime);
        return merged;
    }, [priceData, scores]);

    if (fullData.length === 0) {
        return (
            <div className="w-full min-h-[400px] h-full flex flex-col items-center justify-center relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-br from-[#00f0ff]/5 to-transparent animate-pulse" />
                <div className="relative z-10 flex flex-col items-center gap-4">
                    <div className="p-4 bg-[#00f0ff]/10 rounded-full border border-[#00f0ff]/20 animate-bounce shadow-[0_0_15px_rgba(0,240,255,0.3)]">
                        <TrendingUp className="w-8 h-8 text-[#00f0ff]" />
                    </div>
                    <div className="text-center">
                        <h3 className="text-slate-200 font-bold tracking-widest uppercase text-[10px]">Initializing Intelligence Feed...</h3>
                    </div>
                </div>
            </div>
        );
    }

    const latest = fullData[fullData.length - 1];
    const currentPrice = latest.close;
    const firstPrice = fullData[0].close;
    const changePercent = firstPrice > 0 ? ((currentPrice - firstPrice) / firstPrice) * 100 : 0;
    
    const priceMin = Math.min(...fullData.map(d => d.close));
    const priceMax = Math.max(...fullData.map(d => d.close));
    const pricePadding = (priceMax - priceMin) * 0.1 || currentPrice * 0.01;

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="bg-black/80 backdrop-blur-md border border-[#00f0ff]/30 p-3 rounded-xl shadow-[0_0_20px_rgba(0,240,255,0.15)] flex flex-col gap-1 z-[100] relative">
                    <p className="text-[#00f0ff] font-black text-[10px] uppercase tracking-widest mb-1">{label}</p>
                    <p className="text-white font-mono font-bold text-[13px]">Price: ${data.close.toFixed(2)}</p>
                    {data.news && (
                        <div className="mt-2 pt-2 border-t border-white/10 max-w-[220px]">
                            <p className="text-[9px] text-[#ff00e5] font-black uppercase tracking-widest mb-1">News Impact</p>
                            <p className="text-[11px] text-slate-300 leading-tight">{data.news}</p>
                        </div>
                    )}
                </div>
            );
        }
        return null;
    };

    const renderCustomDot = (props) => {
        const { cx, cy, payload, key } = props;
        if (payload.news) {
            return (
                <circle key={key} cx={cx} cy={cy} r={4.5} fill={payload.sentiment > 0.2 ? '#00f0ff' : payload.sentiment < -0.2 ? '#ff00e5' : '#fff'} stroke="#000" strokeWidth={1.5} style={{ filter: 'drop-shadow(0 0 5px rgba(255,255,255,0.8))' }} />
            );
        }
        return null;
    };

    return (
        <div className="w-full h-full bg-transparent p-6 flex flex-col gap-6 relative overflow-hidden rounded-2xl group">
            {/* Global Styles for Neon Effects */}
            <style dangerouslySetInnerHTML={{ __html: `
                .chart-line-glow { filter: drop-shadow(0 0 8px #00f0ff); }
                .pulse-outer { animation: chart-pulse 2s cubic-bezier(0, 0, 0.2, 1) infinite; }
                @keyframes chart-pulse {
                    0% { stroke-width: 0; stroke-opacity: 0.8; }
                    100% { stroke-width: 25; stroke-opacity: 0; }
                }
                .update-flash { animation: flash-bg 0.8s ease-out; }
                @keyframes flash-bg {
                    0% { background-color: rgba(0, 240, 255, 0.15); }
                    100% { background-color: transparent; }
                }
            `}} />

            {/* Premium Header Metrics */}
            <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 bg-white/5 border border-white/10 rounded-xl p-5 relative transition-colors duration-500 backdrop-blur-md ${flash ? 'update-flash' : ''}`}>
                {flash && (
                    <div className="absolute top-2 right-2">
                        <Zap className="w-4 h-4 text-[#00f0ff] fill-[#00f0ff] animate-pulse drop-shadow-[0_0_5px_rgba(0,240,255,0.8)]" />
                    </div>
                )}
                <div className="relative group/metric overflow-hidden">
                    <div className="text-[9px] text-slate-400 uppercase font-black tracking-[0.2em] mb-1 group-hover/metric:text-[#00f0ff] transition-colors">Live Execution</div>
                    <div className="text-2xl lg:text-3xl font-mono text-white flex flex-wrap items-center gap-2 font-bold tracking-tighter drop-shadow-md">
                        ${currentPrice.toFixed(2)}
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded shadow-xl ${changePercent >= 0 ? 'bg-[#00f0ff]/10 text-[#00f0ff] border border-[#00f0ff]/20' : 'bg-[#ff00e5]/10 text-[#ff00e5] border border-[#ff00e5]/20'}`}>
                            {changePercent >= 0 ? '▲' : '▼'}{Math.abs(changePercent).toFixed(2)}%
                        </span>
                    </div>
                    <div className="absolute -inset-4 bg-gradient-to-r from-transparent via-white/5 to-transparent translate-x-[-100%] group-hover/metric:translate-x-[100%] transition-transform duration-1000"></div>
                </div>
                <div className="border-l border-white/5 pl-4 relative group/metric overflow-hidden">
                    <div className="text-[9px] text-slate-400 uppercase font-black tracking-[0.2em] mb-1 group-hover/metric:text-[#00f0ff] transition-colors">Session High</div>
                    <div className="text-xl lg:text-2xl font-mono text-slate-200">${Math.max(...fullData.map(d => d.high)).toFixed(2)}</div>
                </div>
                <div className="border-l border-white/5 pl-4 relative group/metric overflow-hidden">
                    <div className="text-[9px] text-slate-400 uppercase font-black tracking-[0.2em] mb-1 group-hover/metric:text-[#ff00e5] transition-colors">Session Low</div>
                    <div className="text-xl lg:text-2xl font-mono text-slate-200">${Math.min(...fullData.map(d => d.low)).toFixed(2)}</div>
                </div>
                <div className="border-l border-white/5 pl-4 relative group/metric overflow-hidden">
                    <div className="text-[9px] text-slate-400 uppercase font-black tracking-[0.2em] mb-1 group-hover/metric:text-[#7000ff] transition-colors">Tick Volume</div>
                    <div className="text-xl lg:text-2xl font-mono text-slate-200">{latest.volume.toLocaleString()}</div>
                </div>
            </div>

            {/* Main Price Visualization */}
            <div className="flex-1 flex flex-col gap-2 min-h-0 bg-black/20 p-4 rounded-xl border border-white/5">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                        <div className="w-1.5 h-3 bg-[#00f0ff] rounded-full drop-shadow-[0_0_5px_rgba(0,240,255,0.8)]" />
                        <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">Core Price Trajectory</h3>
                    </div>
                    <div className="flex items-center gap-1 bg-black/40 p-1 rounded-lg border border-white/5">
                        {['1D', '1W', '1M'].map(tf => (
                            <button 
                                key={tf}
                                onClick={() => setTimeframe(tf)}
                                className={`px-3 py-1 rounded text-[10px] font-black uppercase tracking-widest transition-colors ${timeframe === tf ? 'bg-[#00f0ff]/20 text-[#00f0ff] border border-[#00f0ff]/30 shadow-[0_0_10px_rgba(0,240,255,0.2)]' : 'bg-transparent text-slate-500 hover:text-slate-300 border border-transparent cursor-pointer'}`}
                            >
                                {tf}
                            </button>
                        ))}
                    </div>
                </div>
                
                <div className="flex-1 min-h-0 w-full relative">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={fullData} syncId="alphaChartSync" margin={{ top: 15, right: 60, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorPriceDepth" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#00f0ff" stopOpacity={0.4}/>
                                    <stop offset="60%" stopColor="#7000ff" stopOpacity={0.1}/>
                                    <stop offset="95%" stopColor="#7000ff" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="4 6" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis 
                                dataKey="time" 
                                stroke="#64748b" 
                                fontSize={9} 
                                tickLine={false} 
                                axisLine={false}
                                minTickGap={40}
                                interval="preserveStartEnd"
                                tick={{ fill: '#64748b', fontWeight: 'bold' }}
                                padding={{ left: 20, right: 20 }}
                            />
                            <YAxis 
                                domain={[priceMin - pricePadding, priceMax + pricePadding]} 
                                orientation="right" 
                                stroke="#64748b" 
                                fontSize={10} 
                                fontFamily="monospace"
                                tickLine={false} 
                                axisLine={false}
                                tickFormatter={(val) => `$${val.toFixed(2)}`}
                                tick={{ fill: '#94a3b8', fontWeight: 'bold' }}
                            />
                            <Tooltip 
                                content={<CustomTooltip />} 
                                cursor={{ stroke: 'rgba(0, 240, 255, 0.4)', strokeWidth: 1, strokeDasharray: '3 3' }} 
                            />
                            
                            <Area
                                type="monotoneX"
                                dataKey="close"
                                stroke="none"
                                fillOpacity={1}
                                fill="url(#colorPriceDepth)"
                                animationDuration={1000}
                                animationEasing="ease-out"
                            />
                            
                            <Line 
                                type="monotone" 
                                dataKey="close" 
                                stroke="#00f0ff" 
                                strokeWidth={3} 
                                dot={renderCustomDot}
                                activeDot={{ r: 6, fill: '#00f0ff', stroke: '#fff', strokeWidth: 2 }}
                                className="chart-line-glow"
                                animationDuration={1000}
                                animationEasing="ease-out"
                            />
                            
                            {/* Pulse Indicator */}
                            {fullData.length > 0 && (
                                <ReferenceDot 
                                    x={latest.time} 
                                    y={currentPrice} 
                                    r={5} 
                                    fill="#fff" 
                                    stroke="#00f0ff" 
                                    strokeWidth={3}
                                    isFront={true}
                                >
                                    <circle r="6" fill="#00f0ff" className="pulse-outer" />
                                </ReferenceDot>
                            )}

                            <ReferenceLine y={currentPrice} stroke="#00f0ff" strokeDasharray="3 3" opacity={0.4} />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Sentiment Overlay Bar Chart */}
            <div className="h-[140px] flex flex-col gap-2 bg-black/20 p-4 rounded-xl border border-white/5">
                <div className="flex justify-between items-center px-1">
                    <div className="flex items-center gap-2">
                        <div className="w-1.5 h-3 bg-[#7000ff] rounded-full drop-shadow-[0_0_5px_rgba(112,0,255,0.8)]" />
                        <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">Emotional Index</h3>
                    </div>
                </div>
                <div className="flex-1 w-full relative">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={fullData} syncId="alphaChartSync" margin={{ top: 10, right: 60, left: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="time" hide />
                            <YAxis 
                                domain={[-1, 1]} 
                                orientation="right" 
                                stroke="#64748b" 
                                fontSize={9} 
                                tickLine={false} 
                                axisLine={false}
                                tickFormatter={(val) => val === 0 ? 'NEUT' : val > 0 ? '+BULL' : '-BEAR'}
                                tick={{ fill: '#64748b', fontWeight: 'bold' }}
                            />
                            <Bar dataKey="sentiment" radius={[4, 4, 4, 4]} barSize={8} animationDuration={1000}>
                                {fullData.map((entry, index) => (
                                    <Cell 
                                        key={`cell-${index}`} 
                                        fill={entry.sentiment > 0.2 ? '#00f0ff' : entry.sentiment < -0.2 ? '#ff00e5' : '#475569'} 
                                        fillOpacity={0.5 + Math.abs(entry.sentiment) * 0.5}
                                    />
                                ))}
                            </Bar>
                            <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" strokeWidth={1} />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default PriceChart;
