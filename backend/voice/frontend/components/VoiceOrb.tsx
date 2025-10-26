"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import Image from "next/image";

interface VoiceOrbProps {
  audioLevel: number; // 0-1 scale
  isListening: boolean;
  isSpeaking: boolean;
}

export default function VoiceOrb({ audioLevel, isListening, isSpeaking }: VoiceOrbProps) {
  const [glowIntensity, setGlowIntensity] = useState(0);

  useEffect(() => {
    setGlowIntensity(audioLevel * 100);
  }, [audioLevel]);

  // Calculate orb size based on audio level
  const baseSize = 350;
  const dynamicSize = baseSize + (audioLevel * 100);

  // Intensity multiplier when speaking/listening
  const intensity = isSpeaking ? 1.4 : isListening ? 1.2 : 0.9;

  // Only animate when active
  const isActive = isSpeaking || isListening;

  return (
    <div className="relative flex items-center justify-center w-full h-screen">
      {/* Outer glow layer - only animates when speaking/listening */}
      <motion.div
        className="absolute rounded-full"
        style={{
          width: dynamicSize + 120,
          height: dynamicSize + 120,
          background: `radial-gradient(circle, rgba(100, 150, 255, ${0.25 * intensity}) 0%, rgba(70, 120, 200, ${0.12 * intensity}) 50%, transparent 75%)`,
          filter: `blur(${50 + glowIntensity / 2}px)`,
        }}
        animate={isActive ? {
          scale: [1, 1.08, 1],
          opacity: [0.5, 0.8, 0.5],
        } : {
          scale: 1,
          opacity: 0.4,
        }}
        transition={{
          duration: 2.5,
          repeat: isActive ? Infinity : 0,
          ease: "easeInOut",
        }}
      />

      {/* Main orb container */}
      <motion.div
        className="relative"
        style={{
          width: dynamicSize,
          height: dynamicSize,
        }}
        animate={{
          scale: isActive ? [1, 1 + (audioLevel * 0.15), 1] : 1,
        }}
        transition={{
          duration: 0.5,
          repeat: isActive ? Infinity : 0,
          ease: "easeInOut",
        }}
      >
        {/* Orb image container - circular crop */}
        <div
          className="absolute inset-0"
          style={{
            filter: `drop-shadow(0 0 ${50 + glowIntensity}px rgba(100, 150, 255, ${0.4 * intensity})) drop-shadow(0 0 ${90 + glowIntensity * 1.2}px rgba(70, 120, 200, ${0.25 * intensity}))`,
          }}
        >
          <div
            className="absolute inset-0"
            style={{
              clipPath: 'circle(40% at 50% 50%)',
            }}
          >
            {/* Scale up the image to hide dark background */}
            <div
              className="absolute"
              style={{
                top: '-20%',
                left: '-20%',
                width: '140%',
                height: '140%',
              }}
            >
              <Image
                src="/orb.png"
                alt="Voice Orb"
                fill
                className="object-contain"
                style={{
                  opacity: intensity,
                }}
                priority
              />
            </div>
          </div>
        </div>

        {/* Particles when active */}
        {isActive && (
          <>
            {[...Array(8)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute rounded-full"
                style={{
                  width: 4 + (audioLevel * 5),
                  height: 4 + (audioLevel * 5),
                  background: `rgba(180, 210, 255, ${0.8 * intensity})`,
                  top: "50%",
                  left: "50%",
                  boxShadow: `0 0 ${12 + audioLevel * 12}px rgba(150, 190, 255, 0.7)`,
                }}
                animate={{
                  x: [0, Math.cos((i * Math.PI * 2) / 8) * (dynamicSize * 0.42)],
                  y: [0, Math.sin((i * Math.PI * 2) / 8) * (dynamicSize * 0.42)],
                  opacity: [0.9, 0],
                  scale: [1, 0.2],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: "easeOut",
                  delay: i * 0.12,
                }}
              />
            ))}
          </>
        )}
      </motion.div>

      {/* Status text */}
      <motion.div
        className="absolute bottom-[12%] text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <p className="text-sm text-gray-500 font-light tracking-wide">
          {isSpeaking ? "Speaking..." : isListening ? "Listening..." : "Ready"}
        </p>
      </motion.div>
    </div>
  );
}
