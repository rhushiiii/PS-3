"use client";

import { motion, useReducedMotion } from "framer-motion";

export function HeroTelemetry() {
  const reduce = useReducedMotion();

  const floatTransition = (delay: number) => ({
    duration: 3.8,
    repeat: Infinity,
    repeatType: "mirror" as const,
    ease: "easeInOut" as const,
    delay,
  });

  return (
    <div className="hero-telemetry-layer" aria-hidden="true">
      {/* Floating Card 1: Deterministic Engine */}
      <motion.div
        className="telemetry-card telemetry-card-left"
        initial={reduce ? undefined : { opacity: 0, x: -30, y: 10 }}
        animate={
          reduce
            ? { opacity: 1 }
            : {
                opacity: 1,
                x: 0,
                y: [-6, 6, -6],
              }
        }
        transition={
          reduce
            ? { duration: 0.4 }
            : {
                opacity: { duration: 0.6, delay: 0.2 },
                x: { duration: 0.6, delay: 0.2 },
                y: floatTransition(0),
              }
        }
      >
        <div className="telemetry-header">
          <span className="telemetry-pulse-dot" />
          <span className="telemetry-title">Deterministic Engine</span>
        </div>
        <div className="telemetry-value">12-Digit APAAR Format</div>
        <div className="telemetry-sub">Local Syntax Verification Active</div>
      </motion.div>

      {/* Floating Card 2: Immutable Snapshots */}
      <motion.div
        className="telemetry-card telemetry-card-right"
        initial={reduce ? undefined : { opacity: 0, x: 30, y: -10 }}
        animate={
          reduce
            ? { opacity: 1 }
            : {
                opacity: 1,
                x: 0,
                y: [6, -6, 6],
              }
        }
        transition={
          reduce
            ? { duration: 0.4 }
            : {
                opacity: { duration: 0.6, delay: 0.35 },
                x: { duration: 0.6, delay: 0.35 },
                y: floatTransition(0.8),
              }
        }
      >
        <div className="telemetry-header">
          <span className="telemetry-badge-icon">🛡️</span>
          <span className="telemetry-title">Provenance Tracking</span>
        </div>
        <div className="telemetry-value">0 Overwritten Records</div>
        <div className="telemetry-sub">SHA-256 Fingerprinted Batches</div>
      </motion.div>

      {/* Floating Card 3: Evidence-Linked Leads */}
      <motion.div
        className="telemetry-card telemetry-card-bottom"
        initial={reduce ? undefined : { opacity: 0, y: 20 }}
        animate={
          reduce
            ? { opacity: 1 }
            : {
                opacity: 1,
                y: [-4, 5, -4],
              }
        }
        transition={
          reduce
            ? { duration: 0.4 }
            : {
                opacity: { duration: 0.6, delay: 0.5 },
                y: floatTransition(1.4),
              }
        }
      >
        <div className="telemetry-header">
          <span className="telemetry-badge-icon">📋</span>
          <span className="telemetry-title">Regulatory Dossiers</span>
        </div>
        <div className="telemetry-value">Evidence-Linked Leads</div>
        <div className="telemetry-sub">Officer Discretion · No Auto-Bans</div>
      </motion.div>
    </div>
  );
}

