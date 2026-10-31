"use client";

import { motion, useReducedMotion } from "framer-motion";

const comparisons = [
  {
    dimension: "Data Ingestion & Storage",
    legacy: "Unverified Excel files emailed across departments; rows overwritten directly.",
    pravya: "Immutable candidate snapshots with cryptographic SHA-256 batch fingerprints.",
  },
  {
    dimension: "APAAR ID Verification",
    legacy: "Values accepted blindly without format checks or conflated with government verification.",
    pravya: "Local 12-digit structural validation with transparent distinction from external identity verification.",
  },
  {
    dimension: "Intake & Seat Quotas",
    legacy: "All quotas summed blindly into a single cap; category breaches noticed months after admission.",
    pravya: "Deterministic category-level tracking (GEN, OBC-NCL, SC/ST, EWS, NRI) with instant breach alerts.",
  },
  {
    dimension: "Revision History & Audit",
    legacy: "Prior submissions deleted or modified in place with no timestamp or actor trail.",
    pravya: "Every submission preserved as an immutable revision; tamper-evident audit trail for every action.",
  },
  {
    dimension: "Regulatory Exceptions",
    legacy: "Black-box accusations and silent discards without context or bilateral feedback.",
    pravya: "Evidence-linked findings with rule IDs and severity chips empowering officer review.",
  },
];

export function ComparisonMatrix() {
  const reduce = useReducedMotion();

  return (
    <section className="landing-section comparison-section" id="comparison">
      <div className="page-heading landing-section-heading">
        <p className="eyebrow">THE ARCHITECTURAL DIFFERENCE</p>
        <h2>Why Legacy Spreadsheets Fall Short</h2>
        <p>
          See how PRAVYA replaces ad-hoc spreadsheets with a structured, auditable admissions
          operating system for AICTE institutions.
        </p>
      </div>

      <div className="comparison-table-wrapper">
        <div className="comparison-table" role="table" aria-label="Comparison between legacy approach and PRAVYA">
          <div className="comparison-row comparison-header-row" role="row">
            <div className="comp-col comp-col-dim" role="columnheader">
              Compliance Dimension
            </div>
            <div className="comp-col comp-col-legacy" role="columnheader">
              <span className="badge-legacy">Legacy Spreadsheets & Ad-Hoc ERP</span>
            </div>
            <div className="comp-col comp-col-pravya" role="columnheader">
              <span className="badge-pravya">PRAVYA Platform (SIH26263)</span>
            </div>
          </div>

          {comparisons.map((item, idx) => (
            <motion.div
              key={item.dimension}
              className="comparison-row"
              role="row"
              initial={reduce ? undefined : { opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.35, delay: idx * 0.05 }}
            >
              <div className="comp-col comp-col-dim" role="rowheader">
                <strong>{item.dimension}</strong>
              </div>
              <div className="comp-col comp-col-legacy" role="cell">
                <span className="comp-icon comp-icon-bad">✕</span>
                <span>{item.legacy}</span>
              </div>
              <div className="comp-col comp-col-pravya" role="cell">
                <span className="comp-icon comp-icon-good">✓</span>
                <span>{item.pravya}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

