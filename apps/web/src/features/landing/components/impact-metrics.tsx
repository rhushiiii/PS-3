"use client";

import { motion, useReducedMotion } from "framer-motion";

const metrics = [
  {
    num: "12-Digit",
    label: "Deterministic APAAR Syntax",
    detail: "Local structural validation against configured rules",
  },
  {
    num: "0",
    label: "Silent Overwrites",
    detail: "Immutable submission versioning with SHA-256 fingerprinting",
  },
  {
    num: "3-Tier",
    label: "Role-Scoped Authority",
    detail: "Institution Admin, AICTE Officer, AICTE Manager boundaries",
  },
  {
    num: "100%",
    label: "Evidence-Linked Audits",
    detail: "Actionable regulatory leads backed by immutable receipts",
  },
];

export function ImpactMetrics() {
  const reduce = useReducedMotion();

  return (
    <section className="impact-metrics-section" aria-label="Key platform guarantees">
      <div className="impact-metrics-container">
        {metrics.map((m, idx) => (
          <motion.div
            key={m.label}
            className="impact-metric-item"
            initial={reduce ? undefined : { opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.45, delay: idx * 0.08 }}
          >
            <div className="impact-metric-num">{m.num}</div>
            <div className="impact-metric-label">{m.label}</div>
            <p className="impact-metric-detail">{m.detail}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

