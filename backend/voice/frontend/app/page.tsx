"use client";

import { useEffect, useState, useRef } from "react";
import { Room, RoomEvent, Track, TrackEvent } from "livekit-client";
import { AudioAnalyser } from "@/lib/audioAnalyser";
import VoiceOrb from "@/components/VoiceOrb";
import { motion } from "framer-motion";

export default function Home() {
  const [room, setRoom] = useState<Room | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState<string[]>([]);
  const [error, setError] = useState<string>("");

  const analyserRef = useRef<AudioAnalyser | null>(null);
  const animationFrameRef = useRef<number>();

  // Track if agent is active (speaking or listening)
  const isActive = isSpeaking || isListening;

  // Get LiveKit connection token from backend
  const getToken = async () => {
    try {
      const response = await fetch("/api/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identity: "user-" + Date.now() }),
      });

      if (!response.ok) {
        throw new Error("Failed to get token");
      }

      const data = await response.json();
      return data.token;
    } catch (err) {
      console.error("Token fetch error:", err);
      throw err;
    }
  };

  // Connect to LiveKit room
  const connectToRoom = async () => {
    try {
      setError("");
      const token = await getToken();

      const newRoom = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      // Set up event listeners
      newRoom.on(RoomEvent.Connected, () => {
        console.log("Connected to room");
        setIsConnected(true);
      });

      newRoom.on(RoomEvent.Disconnected, () => {
        console.log("Disconnected from room");
        setIsConnected(false);
      });

      newRoom.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
        console.log("Track subscribed:", track.kind);

        if (track.kind === Track.Kind.Audio) {
          // Agent is speaking
          setIsSpeaking(true);

          // Attach audio element for playback (hidden so it doesn't affect layout)
          const audioElement = track.attach();
          audioElement.style.display = 'none';
          audioElement.style.position = 'fixed';
          audioElement.style.pointerEvents = 'none';
          document.body.appendChild(audioElement);

          // Set up audio analysis
          if (track.mediaStreamTrack) {
            const audioContext = new AudioContext();
            const source = audioContext.createMediaStreamSource(
              new MediaStream([track.mediaStreamTrack])
            );
            analyserRef.current = new AudioAnalyser(source, audioContext);
            startAudioLevelMonitoring();
          }

          track.on(TrackEvent.Ended, () => {
            setIsSpeaking(false);
            audioElement.remove();
            stopAudioLevelMonitoring();
          });
        }
      });

      newRoom.on(RoomEvent.TrackUnsubscribed, (track) => {
        if (track.kind === Track.Kind.Audio) {
          setIsSpeaking(false);
        }
      });

      // Connect to LiveKit Cloud
      const livekitUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL || "ws://localhost:7880";
      await newRoom.connect(livekitUrl, token);

      setRoom(newRoom);

      // Enable microphone
      await newRoom.localParticipant.setMicrophoneEnabled(true);
      setIsListening(true);

    } catch (err: any) {
      console.error("Connection error:", err);
      setError(err.message || "Failed to connect to voice agent");
    }
  };

  // Monitor audio levels for visualization
  const startAudioLevelMonitoring = () => {
    const updateLevel = () => {
      if (analyserRef.current) {
        const level = analyserRef.current.getAudioLevel();
        setAudioLevel(level);
      }
      animationFrameRef.current = requestAnimationFrame(updateLevel);
    };
    updateLevel();
  };

  const stopAudioLevelMonitoring = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    setAudioLevel(0);
  };

  // Disconnect from room
  const disconnect = async () => {
    if (room) {
      await room.disconnect();
      setRoom(null);
      setIsConnected(false);
      setIsListening(false);
      setIsSpeaking(false);
      stopAudioLevelMonitoring();
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, []);

  // Check if running in Electron
  const isElectron = typeof window !== 'undefined' &&
    ((window as any).electron?.isElectron === true ||
     window.navigator.userAgent.includes('Electron') ||
     (window as any).process?.type === 'renderer');

  return (
    <main
      className={isElectron ? 'fixed inset-0 w-full h-full m-0 p-0 overflow-hidden' : 'relative w-full h-screen overflow-hidden'}
      style={{
        background: isElectron ? 'transparent' : '#0a0a0a',
      }}
    >
      {/* Floating Voice Assistant Window */}
      <div
        className={`overflow-hidden backdrop-blur-2xl no-drag ${
          isElectron
            ? ''
            : 'absolute top-8 right-8 rounded-3xl border border-white/10'
        }`}
        style={{
          ...(isElectron ? {
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            width: '100vw',
            height: '100vh',
            margin: 0,
            padding: 0,
          } : {
            width: '380px',
            height: '480px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05)',
          }),
          background: 'linear-gradient(135deg, rgba(10, 10, 10, 0.95) 0%, rgba(20, 20, 30, 0.95) 100%)',
        }}
      >
        {/* Header */}
        <div className="absolute top-0 left-0 right-0 flex items-center justify-between px-4 py-2.5 z-20 drag-region">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50"></div>
            <h1 className="text-[10px] font-semibold text-white/95 tracking-wider">TURING</h1>
          </div>
          <div className="flex gap-1.5 no-drag">
            <div className="w-2.5 h-2.5 rounded-full bg-zinc-700/60 hover:bg-yellow-500/60 transition-colors cursor-pointer"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-zinc-700/60 hover:bg-red-500/60 transition-colors cursor-pointer"></div>
          </div>
        </div>

        {/* Voice Orb - Clickable to toggle session */}
        <div className="absolute inset-0 flex items-center justify-center no-drag">
          <button
            onClick={isConnected ? disconnect : connectToRoom}
            className="transition-transform duration-200 active:scale-95 cursor-pointer focus:outline-none"
            style={{ width: '220px', height: '220px' }}
            aria-label={isConnected ? "End voice session" : "Start voice session"}
          >
            <VoiceOrb
              audioLevel={audioLevel}
              isListening={isListening}
              isSpeaking={isSpeaking}
            />
          </button>
        </div>

        {/* Status Text */}
        <div className="absolute bottom-8 left-0 right-0 flex justify-center z-20">
          <motion.div
            className="px-3.5 py-1.5 rounded-full bg-white/5 backdrop-blur-sm border border-white/10"
            animate={{
              scale: isActive ? [1, 1.02, 1] : 1,
            }}
            transition={{
              duration: 1.5,
              repeat: isActive ? Infinity : 0,
            }}
          >
            <p className="text-[11px] font-medium text-gray-300 tracking-wide">
              {isSpeaking ? "Speaking..." : isListening ? "Listening..." : "Click to start"}
            </p>
          </motion.div>
        </div>

        {/* Error message if any */}
        {error && (
          <div className="absolute bottom-2 left-0 right-0 px-4 z-20">
            <div className="text-red-400 text-xs text-center bg-red-900/20 border border-red-500/30 rounded-lg px-3 py-1.5">
              {error}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
