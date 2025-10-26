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

          // Attach audio element for playback
          const audioElement = track.attach();
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

  return (
    <main className="relative w-full h-screen overflow-hidden" style={{ background: '#0a0a0a' }}>
      {/* Voice Orb - takes full screen */}
      <motion.div
        className="absolute inset-0"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
        <VoiceOrb
          audioLevel={audioLevel}
          isListening={isListening}
          isSpeaking={isSpeaking}
        />
      </motion.div>

      {/* Connection controls - centered at top */}
      <div className="absolute top-0 left-0 right-0 flex justify-center pt-12 z-20">
        <motion.div
          className="flex flex-col items-center gap-4"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
        {!isConnected ? (
          <button
            onClick={connectToRoom}
            className="group relative px-8 py-3 bg-white/10 hover:bg-white/15 rounded-full font-normal text-sm text-white/90 backdrop-blur-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] border border-white/10 hover:border-white/20"
            style={{
              boxShadow: '0 4px 24px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
            }}
          >
            <span className="relative z-10">Start Voice Session</span>
          </button>
        ) : (
          <button
            onClick={disconnect}
            className="group relative px-8 py-3 bg-white/5 hover:bg-white/10 rounded-full font-normal text-sm text-white/70 backdrop-blur-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] border border-white/5 hover:border-white/10"
            style={{
              boxShadow: '0 4px 24px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.05)'
            }}
          >
            <span className="relative z-10">End Session</span>
          </button>
        )}

        {error && (
          <div className="text-red-400 text-sm max-w-md text-center bg-red-900/20 border border-red-500/30 rounded-lg px-4 py-2 backdrop-blur-sm">
            {error}
          </div>
        )}
        </motion.div>
      </div>

      {/* Instructions - bottom overlay - hide when speaking/listening */}
      {isConnected && !isSpeaking && !isListening && (
        <motion.div
          className="absolute bottom-32 left-1/2 -translate-x-1/2 z-20 text-center max-w-lg px-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
        >
          <p className="text-gray-500 text-sm mb-3">Try saying:</p>
          <div className="flex flex-col gap-2 text-gray-600 text-sm">
            <p>"Hey AgentFlow, remember what I'm going to do now"</p>
            <p>"Send an email to John"</p>
          </div>
        </motion.div>
      )}
    </main>
  );
}
