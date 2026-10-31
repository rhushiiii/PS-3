"use client";

import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

interface SimulationScenario {
  id: string;
  name: string;
  programme: string;
  category: string;
  apaar: string;
  expectedOutcome: "VALID" | "FORMAT_ERROR" | "CAPACITY_BREACH";
  ruleCode: string;
  summary: string;
  evidence: string;
}

const scenarios: SimulationScenario[] = [
  {
    id: "clean",
    name: "Scenario A: Compliant Admission",
    programme: "B.Tech Mechanical Engineering",
    category: "General (Approved Cap: 60)",
    apaar: "9102-4821-7734",
    expectedOutcome: "VALID",
    ruleCode: "RULE_APAAR_FORMAT_OK",
    summary: "12-digit syntax verified locally; category intake within approved ceiling (42/60).",
    evidence: "Format: 12-digit numeric match. Quota: General category declared=42, approved=60. No conflicting duplicates.",
  },
  {
    id: "format-error",
    name: "Scenario B: Malformed APAAR Syntax",
    programme: "B.Tech Computer Science",
    category: "Regular (Approved Cap: 120)",
    apaar: "9812-34A-X29",
    expectedOutcome: "FORMAT_ERROR",
    ruleCode: "RULE_APAAR_FORMAT_INVALID",
    summary: "Format mismatch: non-numeric characters and invalid length detected locally.",
    evidence: "Expected 12 numeric digits with optional hyphens. Found invalid character sequence '34A-X'. Flagged as candidate exception.",
  },
  {
    id: "quota-breach",
    name: "Scenario C: Category Intake Breach",
    programme: "B.Tech Civil Engineering",
    category: "OBC-NCL (Approved Cap: 30)",
    apaar: "8190-2341-5510",
    expectedOutcome: "CAPACITY_BREACH",
    ruleCode: "RULE_INTAKE_CAPACITY_EXCEEDED",
    summary: "Declared intake (31) exceeds approved AICTE sanction (30) for OBC-NCL category.",
    evidence: "Declared count: 31 for category 'OBC-NCL'. Configured maximum: 30. Excess: +1 candidate record flagged for officer review.",
  },
];

export function ValidationSimulator() {
  const [selectedScenario, setSelectedScenario] = useState<SimulationScenario>(scenarios[0]);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const reduce = useReducedMotion();

  const handleSelectScenario = (sc: SimulationScenario) => {
    setSelectedScenario(sc);
    setIsEvaluating(true);
    setTimeout(() => {
      setIsEvaluating(false);
    }, 450);
  };

  return (
    <section className="landing-section simulator-section" id="simulator">
      <div className="page-heading landing-section-heading">
        <p className="eyebrow">HANDS-ON SIMULATION</p>
        <h2>Test the Deterministic Engine</h2>
        <p>
          See how local APAAR format verification and intake capacity checks execute deterministically
          in real time. Select a sample scenario below:
        </p>
      </div>

      <div className="simulator-shell">
        {/* Scenario Selector Pills */}
        <div className="scenario-selector-bar" role="group" aria-label="Select Test Scenario">
          {scenarios.map((sc) => {
            const isCurrent = sc.id === selectedScenario.id;
            return (
              <button
                key={sc.id}
                onClick={() => handleSelectScenario(sc)}
                className={`scenario-btn ${isCurrent ? "active" : ""}`}
              >
                {sc.name}
              </button>
            );
          })}
        </div>

        {/* Live Playground Card */}
        <div className="simulator-content-grid">
          {/* Left: Input Parameters */}
          <div className="simulator-input-panel">
            <div className="simulator-panel-header">
              <span className="panel-dot" />
              <span>Input Candidate Record (Synthetic)</span>
            </div>

            <div className="simulator-fields">
              <div className="sim-field">
                <label>Target Programme</label>
                <div className="sim-input-mock">{selectedScenario.programme}</div>
              </div>

              <div className="sim-field">
                <label>Admission Seat Category</label>
                <div className="sim-input-mock">{selectedScenario.category}</div>
              </div>

              <div className="sim-field">
                <label>Candidate APAAR String (Local Input)</label>
                <div className="sim-input-mock sim-apaar-mono">{selectedScenario.apaar}</div>
              </div>

              <div className="sim-disclaimer">
                <small>
                  ⚠️ Synthetic test record. Local format check only. Never claims real government identity verification.
                </small>
              </div>
            </div>
          </div>

          {/* Right: Engine Pipeline & Evidence Dossier */}
          <div className="simulator-output-panel">
            <div className="simulator-panel-header">
              <span className="panel-dot green" />
              <span>Deterministic Validation Output</span>
            </div>

            <AnimatePresence mode="wait">
              {isEvaluating ? (
                <motion.div
                  key="loading"
                  className="evaluating-state"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <div className="evaluating-spinner" />
                  <p>Executing deterministic rules against configured intake caps...</p>
                </motion.div>
              ) : (
                <motion.div
                  key={selectedScenario.id}
                  className="outcome-card"
                  initial={reduce ? undefined : { opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="outcome-top-bar">
                    <span
                      className={`outcome-status-badge outcome-${selectedScenario.expectedOutcome.toLowerCase()}`}
                    >
                      {selectedScenario.expectedOutcome === "VALID"
                        ? "✓ VALID CANDIDATE"
                        : selectedScenario.expectedOutcome === "FORMAT_ERROR"
                        ? "⚠ FORMAT EXCEPTION"
                        : "🚨 INTAKE CAPACITY BREACH"}
                    </span>
                    <span className="rule-code-chip">{selectedScenario.ruleCode}</span>
                  </div>

                  <div className="outcome-summary">
                    <strong>Rule Evaluation Result:</strong>
                    <p>{selectedScenario.summary}</p>
                  </div>

                  <div className="outcome-evidence-box">
                    <div className="evidence-label">Redacted Evidence Dossier:</div>
                    <code className="evidence-code">{selectedScenario.evidence}</code>
                  </div>

                  <div className="outcome-footer">
                    <span>
                      {selectedScenario.expectedOutcome === "VALID"
                        ? "Ready for Officer Review Activation"
                        : "Requires Institution Omission Acknowledgment or Correction"}
                    </span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}

