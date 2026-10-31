"use client";

import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

interface SolutionTab {
  id: string;
  badge: string;
  title: string;
  summary: string;
  highlights: string[];
  mockup: {
    tag: string;
    tagTone: "normal" | "accent" | "warning";
    previewHeading: string;
    details: Array<{ key: string; val: string; status?: "ok" | "warn" | "info" }>;
    note: string;
  };
}

const solutions: SolutionTab[] = [
  {
    id: "ingestion",
    badge: "MODULE 01",
    title: "Candidate Ingestion & Versioning",
    summary:
      "Institutions submit admissions datasets as immutable candidates. No submission ever modifies prior active declarations in place.",
    highlights: [
      "Cryptographic SHA-256 fingerprinting on raw CSV uploads",
      "Strict candidate vs active state machine isolation",
      "Historical revision tracking preserves all corrections as distinct versions",
      "CSV formula-injection safety and field length bounding",
    ],
    mockup: {
      tag: "IMMUTABLE CANDIDATE BATCH",
      tagTone: "normal",
      previewHeading: "Batch #2026-ENG-04 (Mechanical)",
      details: [
        { key: "Status", val: "CANDIDATE (Pending Review)", status: "info" },
        { key: "Total Rows", val: "120 Admitted Records" },
        { key: "SHA-256 Digest", val: "sha256:7f4a2e8c9...d14b" },
        { key: "Submission Actor", val: "INST_ADMIN (Registrar Office)" },
      ],
      note: "Candidate batches must pass validation & officer activation before becoming active records.",
    },
  },
  {
    id: "rules",
    badge: "MODULE 02",
    title: "Deterministic Rule & Intake Engine",
    summary:
      "A rule-based evaluation engine checks 12-digit APAAR format syntax and enforces approved category capacity quotas without guessing.",
    highlights: [
      "Local 12-digit APAAR format validation (clearly distinct from govt verification)",
      "Category capacity checks (General, OBC-NCL, SC/ST, EWS, Management, NRI)",
      "Potential cross-institution duplicate candidate detection",
      "Deterministic findings with permanent Rule IDs (e.g. RULE_INTAKE_CAPACITY)",
    ],
    mockup: {
      tag: "DETERMINISTIC EVALUATION",
      tagTone: "accent",
      previewHeading: "Rule Engine Run #RUN-8841",
      details: [
        { key: "RULE_APAAR_FORMAT", val: "118 / 120 Passed Format Check", status: "warn" },
        { key: "RULE_INTAKE_CAPACITY", val: "OBC-NCL: 30 / 30 Approved Cap", status: "ok" },
        { key: "RULE_CROSS_INSTITUTION", val: "1 Potential Duplicate Found", status: "warn" },
        { key: "Scope Coverage", val: "Academic Year 2026-27" },
      ],
      note: "Rule exceptions are surfaced as actionable findings for officers, never silent rejections.",
    },
  },
  {
    id: "review",
    badge: "MODULE 03",
    title: "AICTE Regulatory Review & Case Center",
    summary:
      "Empowers regulatory officers with evidence dossiers, redacted student PII, and bilateral correction requests rather than automated black-box penalties.",
    highlights: [
      "Evidence-linked leads: findings are investigative leads, not automated verdicts",
      "Redacted PII protection prevents unnecessary identifier exposure",
      "Bilateral omission acknowledgments and corrective re-upload workflows",
      "Audit trail records every regulatory action with timestamp and actor ID",
    ],
    mockup: {
      tag: "OFFICER DOSSIER & AUDIT",
      tagTone: "warning",
      previewHeading: "Case #CAS-2026-092 · Potential Duplicate",
      details: [
        { key: "Student ID", val: "STU-***-4921 (Redacted)" },
        { key: "Conflicting Inst.", val: "Inst. Code 1-9042 (Delhi Tech)" },
        { key: "Finding Code", val: "RULE_CROSS_INSTITUTION_DUPLICATE" },
        { key: "Officer Action", val: "Awaiting Institution Response", status: "warn" },
      ],
      note: "Officers can sign review receipts and activate candidate snapshots with full provenance.",
    },
  },
  {
    id: "abc",
    badge: "MODULE 04",
    title: "Simulated ABC Credit Reconciliation",
    summary:
      "Optional credit transfer verification against Academic Bank of Credits (ABC) architecture with deterministic simulated adapters.",
    highlights: [
      "Strict separation between local admission validity and external credit sync",
      "Simulated external adapter clearly tagged with SIMULATED / DEMO DATA",
      "Credit failure or timeout does not block core admission monitoring",
      "Prepares institutions for full NEP 2020 multiple entry-exit credit transfers",
    ],
    mockup: {
      tag: "SIMULATED / DEMO DATA",
      tagTone: "accent",
      previewHeading: "ABC Credit Ledger Verification (Prototype)",
      details: [
        { key: "Source Type", val: "SIMULATED (Prototype Adapter)" },
        { key: "Verified Credits", val: "24 Academic Credits Reconciled", status: "ok" },
        { key: "Institution Ledger", val: "Direct Match (Semester 1 & 2)" },
        { key: "Core Admission Blocked?", val: "No (Independent Status)", status: "ok" },
      ],
      note: "NEVER claimed as real government API access. Prototype uses deterministic synthetic adapters.",
    },
  },
];

export function SolutionTabs() {
  const [activeTab, setActiveTab] = useState(solutions[0].id);
  const reduce = useReducedMotion();

  const current = solutions.find((s) => s.id === activeTab) ?? solutions[0];

  return (
    <section className="landing-section solutions-section" id="solutions">
      <div className="page-heading landing-section-heading">
        <p className="eyebrow">INTELLIGENT WORKSPACE</p>
        <h2>Interactive Solution Suite</h2>
        <p>
          Explore how PRAVYA replaces fragmented spreadsheets with an end-to-end,
          evidence-linked compliance pipeline designed for AICTE institutions.
        </p>
      </div>

      {/* Tab Navigation Pill Bar */}
      <div className="solution-tabs-nav" role="tablist" aria-label="Platform Modules">
        {solutions.map((tab) => {
          const isSelected = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={isSelected}
              onClick={() => setActiveTab(tab.id)}
              className={`solution-tab-btn ${isSelected ? "active" : ""}`}
            >
              {isSelected && (
                <motion.div
                  layoutId={reduce ? undefined : "activeSolutionPill"}
                  className="solution-tab-pill-highlight"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
              <span className="tab-badge">{tab.badge}</span>
              <span className="tab-title">{tab.title.split("&")[0].trim()}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Content Display with Animated Card */}
      <div className="solution-tab-content-wrapper">
        <AnimatePresence mode="wait">
          <motion.div
            key={current.id}
            className="solution-tab-panel"
            initial={reduce ? undefined : { opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reduce ? undefined : { opacity: 0, y: -14 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
          >
            {/* Left Column: Solution Explanation */}
            <div className="solution-info-col">
              <span className="solution-badge-pill">{current.badge}</span>
              <h3 className="solution-panel-title">{current.title}</h3>
              <p className="solution-panel-summary">{current.summary}</p>
              <ul className="solution-highlights-list">
                {current.highlights.map((item) => (
                  <li key={item}>
                    <span className="highlight-icon">✓</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Right Column: Live Interactive Mockup */}
            <div className="solution-mockup-col">
              <div className="mockup-card">
                <div className="mockup-header">
                  <span className={`mockup-tag mockup-tag-${current.mockup.tagTone}`}>
                    {current.mockup.tag}
                  </span>
                  <div className="mockup-controls" aria-hidden="true">
                    <span className="mockup-dot" />
                    <span className="mockup-dot" />
                    <span className="mockup-dot" />
                  </div>
                </div>

                <div className="mockup-body">
                  <h4 className="mockup-heading">{current.mockup.previewHeading}</h4>
                  <div className="mockup-details-grid">
                    {current.mockup.details.map((detail) => (
                      <div className="mockup-row" key={detail.key}>
                        <span className="mockup-key">{detail.key}</span>
                        <span
                          className={`mockup-val ${
                            detail.status ? `val-status-${detail.status}` : ""
                          }`}
                        >
                          {detail.val}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="mockup-note">
                    <strong>Note:</strong> {current.mockup.note}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}

