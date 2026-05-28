import { useEffect, useRef } from 'react';
import { useSentimentStore } from '../store/useSentimentStore';

const playBeep = (type = 'BUY') => {
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    const ctx = new Ctx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    // Smooth Sine wave for a premium feel
    osc.type = 'sine';
    
    // Higher pitch for BUY, lower for SELL
    const freq = type === 'BUY' ? 880 : type === 'SELL' ? 330 : 440;
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    
    // Quick attack, slow release (volume envelope)
    gain.gain.setValueAtTime(0, ctx.currentTime);
    gain.gain.linearRampToValueAtTime(0.1, ctx.currentTime + 0.05);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
    
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.5);
  } catch(e) {
    console.error("Audio error", e);
  }
};

const NotificationManager = () => {
    const { signal, currentTicker } = useSentimentStore();
    const prevSignal = useRef(signal);
    const hasRequestedPermission = useRef(false);

    // Request notification permission on mount
    useEffect(() => {
        if (!hasRequestedPermission.current && 'Notification' in window && Notification.permission !== 'granted' && Notification.permission !== 'denied') {
            Notification.requestPermission();
            hasRequestedPermission.current = true;
        }
    }, []);

    // Listen for signal changes
    useEffect(() => {
        // Only alert if the signal actually shifted from something else TO a Buy or Sell
        if (prevSignal.current !== signal && signal !== 'HOLD') {
            
            // 1. Audio Alert
            playBeep(signal);
            
            // 2. Browser Push Notification
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification(`AlphaSignal: ${currentTicker} is a ${signal}`, {
                    body: `The sentiment signal for ${currentTicker} has shifted to ${signal}. Check the intelligence feed for details!`,
                });
            }
        }
        prevSignal.current = signal;
    }, [signal, currentTicker]);

    return null; // Headless component
};

export default NotificationManager;
