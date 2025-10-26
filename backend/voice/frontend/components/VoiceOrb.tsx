"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

interface VoiceOrbProps {
  audioLevel: number; // 0-1 scale
  isListening: boolean;
  isSpeaking: boolean;
}

export default function VoiceOrb({ audioLevel, isListening, isSpeaking }: VoiceOrbProps) {
  const [glowIntensity, setGlowIntensity] = useState(0);

  useEffect(() => {
    // Map audio level to glow intensity
    setGlowIntensity(audioLevel * 100);
  }, [audioLevel]);

  // Calculate orb size based on audio level
  const baseSize = 200;
  const dynamicSize = baseSize + (audioLevel * 80);

  // Color changes based on state
  const getOrbColor = () => {
    if (isSpeaking) return "rgba(16, 185, 129, 0.6)"; // Green when agent speaks
    if (isListening) return "rgba(59, 130, 246, 0.6)"; // Blue when listening
    return "rgba(99, 102, 241, 0.4)"; // Purple idle state
  };

  const orbColor = getOrbColor();

  return (
    <div className="relative flex items-center justify-center">
      {/* Outer glow rings */}
      <motion.div
        className="absolute rounded-full"
        style={{
          width: dynamicSize + 100,
          height: dynamicSize + 100,
          background: `radial-gradient(circle, ${orbColor} 0%, transparent 70%)`,
          filter: `blur(${20 + glowIntensity / 5}px)`,
        }}
        animate={{
          scale: [1, 1.1, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Middle ring */}
      <motion.div
        className="absolute rounded-full"
        style={{
          width: dynamicSize + 50,
          height: dynamicSize + 50,
          background: `radial-gradient(circle, ${orbColor} 0%, transparent 60%)`,
          filter: `blur(${15 + glowIntensity / 10}px)`,
        }}
        animate={{
          scale: [1, 1.15, 1],
          opacity: [0.4, 0.6, 0.4],
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 0.2,
        }}
      />

      {/* Core orb */}
      <motion.div
        className="relative rounded-full shadow-2xl"
        style={{
          width: dynamicSize,
          height: dynamicSize,
          background: `radial-gradient(circle at 30% 30%, ${orbColor.replace('0.6', '0.9')}, ${orbColor.replace('0.6', '0.5')})`,
          boxShadow: `0 0 ${40 + glowIntensity}px ${orbColor}, inset 0 0 ${20 + glowIntensity / 2}px rgba(255, 255, 255, 0.1)`,
        }}
        animate={{
          scale: [1, 1 + (audioLevel * 0.2), 1],
        }}
        transition={{
          duration: 0.3,
          ease: "easeOut",
        }}
      >
        {/* Inner highlight */}
        <div
          className="absolute top-1/4 left-1/4 w-1/3 h-1/3 rounded-full"
          style={{
            background: "radial-gradient(circle, rgba(255, 255, 255, 0.4), transparent)",
            filter: "blur(20px)",
          }}
        />

        {/* Animated particles */}
        {isSpeaking && (
          <>
            {[...Array(8)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute rounded-full"
                style={{
                  width: 4 + (audioLevel * 6),
                  height: 4 + (audioLevel * 6),
                  background: "rgba(255, 255, 255, 0.6)",
                  top: "50%",
                  left: "50%",
                  transform: "translate(-50%, -50%)",
                }}
                animate={{
                  x: [0, Math.cos((i * Math.PI * 2) / 8) * (50 + audioLevel * 30)],
                  y: [0, Math.sin((i * Math.PI * 2) / 8) * (50 + audioLevel * 30)],
                  opacity: [0.8, 0],
                  scale: [1, 0.5],
                }}
                transition={{
                  duration: 1,
                  repeat: Infinity,
                  ease: "easeOut",
                  delay: i * 0.1,
                }}
              />
            ))}
          </>
        )}
      </motion.div>

      {/* Status indicator */}
      <motion.div
        className="absolute bottom-[-60px] text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <p className="text-sm text-gray-400 font-medium">
          {isSpeaking ? "AgentFlow is speaking..." : isListening ? "Listening..." : "Ready"}
        </p>
      </motion.div>
    </div>
  );
}
