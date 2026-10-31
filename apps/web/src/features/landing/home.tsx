"use client";

import Link from "next/link";
import { useRef, type ReactNode } from "react";
import {
  motion,
  useReducedMotion,
  useScroll,
  useTransform,
} from "framer-motion";
import { TricolorCanvas } from "@/components/tricolor-canvas";
import {
  CategoryBars,
  MetricCard,
  StatusDonut,
} from "@/features/dashboards/components";
import { HeroTelemetry } from "./components/hero-telemetry";
import { ImpactMetrics } from "./components/impact-metrics";
import { SolutionTabs } from "./components/solution-tabs";
import { ValidationSimulator } from "./components/validation-simulator";
import { ComparisonMatrix } from "./components/comparison-matrix";

const pillars = [
  {
    title: "One workspace",
    body: "Upload, validation, review and activation live in a single traceable flow instead of scattered spreadsheets and emails.",
  },
  {
    title: "Evidence, not guesswork",
    body: "Every flag carries a rule code and redacted evidence. Officers review leads with context, not bare rejections.",
  },
  {
    title: "Nothing is overwritten",
    body: "Every submission is kept as an immutable version. A correction is a new version sitting alongside the old one, not a silent edit.",
  },
];

const steps = [
  {
    title: "Upload Records",
    body: "An institution administrator submits a complete admissions snapshot as a structured CSV. The upload is stored as an immutable candidate with SHA-256 integrity.",
  },
  {
    title: "Validate Rules",
    body: "Local APAAR format checks and configured intake capacity rules run deterministically against the candidate.",
  },
  {
    title: "Flag Exceptions",
    body: "Missing fields, format exceptions and potential cross-institution duplicates surface as evidence-linked leads — never automated penalties.",
  },
  {
    title: "Review & Activate",
    body: "An AICTE officer reviews findings in context, requests corrections if necessary, and activates approved snapshots with full audit receipts.",
  },
];

const security = [
  {
    title: "Role-based access",
    body: "Institution administrators, AICTE officers and managers each see only what their role permits — enforced on every backend request, not just hidden in the UI.",
  },
  {
    title: "Full traceability",
    body: "Immutable submission versions and append-only audit events mean every record's history can be reconstructed, not just its latest state.",
  },
  {
    title: "Reviewed, accountable decisions",
    body: "Snapshot activation requires an explicit reviewer and acknowledgment of any omissions before it can replace the current declaration.",
  },
  {
    title: "Clear limits of local validation",
    body: "Local APAAR format checks are structural only. Simulated identity verification is always labeled as such and never presented as official government verification.",
  },
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
};
const item = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0 },
};

function Reveal({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduce ? undefined : "hidden"}
      whileInView="show"
      viewport={{ once: true, amount: 0.2 }}
      variants={container}
    >
      {children}
    </motion.div>
  );
}

function HowItWorks() {
  const ref = useRef<HTMLDivElement>(null);
  const reduce = useReducedMotion();
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start 75%", "end 40%"],
  });
  const lineScale = useTransform(scrollYProgress, [0, 1], [0, 1]);
  return (
    <section className="landing-section" id="how-it-works">
      <div className="page-heading landing-section-heading">
        <p className="eyebrow">THE WORKFLOW</p>
        <h2>Four steps from upload to resolution</h2>
        <p>
          Every admissions batch follows the same deterministic path — no step
          is skipped, and nothing is resolved silently.
        </p>
      </div>
      <div className="timeline" ref={ref}>
        <div className="timeline-track">
          <motion.div
            className="timeline-progress"
            style={reduce ? { scaleY: 1 } : { scaleY: lineScale }}
          />
        </div>
        <ol>
          {steps.map((step, index) => (
            <motion.li
              key={step.title}
              initial={reduce ? undefined : { opacity: 0, x: -16 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.5 }}
              transition={{ duration: 0.4, delay: index * 0.05 }}
            >
              <span className="timeline-index">{index + 1}</span>
              <div>
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </div>
            </motion.li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function LandingPage() {
  const reduce = useReducedMotion();
  return (
    <main className="landing-page">
      {/* Hero Section */}
      <section className="landing-hero">
        <TricolorCanvas className="landing-hero-canvas" />
        <HeroTelemetry />

        <motion.div
          className="landing-hero-content"
          initial={reduce ? undefined : { opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
        >
          <div className="hero-pill-badge">
            <span className="badge-pulse-indicator" />
            <span>AICTE SIH26263 PROTOTYPE · DETERMINISTIC ADMISSION GOVERNANCE</span>
          </div>

          <h1 className="hero-headline">
            <span className="gradient-text">Smarter Admissions.</span>
            <br />
            Stronger Trust.
          </h1>
          <p className="landing-lede hero-lede">
            A deterministic, evidence-linked platform for validating local APAAR
            syntax, enforcing intake category quotas, and providing AICTE officers with
            tamper-evident audit receipts.
          </p>
          <div className="landing-cta">
            <a className="button primary" href="#solutions">
              Explore Solution Suite
            </a>
            <a className="button secondary ghost" href="#simulator">
              Try Interactive Simulator
            </a>
          </div>
        </motion.div>

        <motion.a
          href="#overview"
          className="scroll-indicator"
          aria-label="Scroll to content"
          animate={reduce ? undefined : { y: [0, 8, 0] }}
          transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
        >
          <span />
        </motion.a>
      </section>

      {/* Impact Metrics Strip */}
      <ImpactMetrics />

      {/* Overview Pillars */}
      <section className="landing-section" id="overview">
        <Reveal className="landing-section-heading page-heading">
          <motion.p variants={item} className="eyebrow">
            OVERVIEW
          </motion.p>
          <motion.h2 variants={item}>
            One Workspace. Clearer Decisions.
          </motion.h2>
          <motion.p variants={item}>
            PRAVYA brings admissions intake, local validation and officer review
            into one traceable workspace, so every decision can be explained
            after the fact.
          </motion.p>
        </Reveal>
        <Reveal className="pillar-grid">
          {pillars.map((pillar) => (
            <motion.article
              key={pillar.title}
              className="pillar-card"
              variants={item}
            >
              <h3>{pillar.title}</h3>
              <p>{pillar.body}</p>
            </motion.article>
          ))}
        </Reveal>
      </section>

      {/* Interactive Solution Suite (EduERP Style Tabs) */}
      <SolutionTabs />

      {/* Hands-On Validation Simulator */}
      <ValidationSimulator />

      {/* How It Works Timeline */}
      <HowItWorks />

      {/* Legacy vs. PRAVYA Comparison Matrix */}
      <ComparisonMatrix />

      {/* Platform Dashboard Preview */}
      <section className="landing-section" id="preview">
        <div className="page-heading landing-section-heading">
          <p className="eyebrow">PLATFORM PREVIEW</p>
          <h2>What the workspace looks like</h2>
          <p>
            An illustrative preview of the institution dashboard layout. This is
            not live data — sign in to see your own permitted workspace.
          </p>
        </div>
        <Reveal className="preview-shell">
          <div className="preview-badge">
            Illustrative preview · not live data
          </div>
          <div className="dashboard-metrics preview-metrics">
            <MetricCard
              label="Current declared records"
              value="1,248"
              note="Activated snapshots only; candidates and history excluded"
            />
            <MetricCard
              label="Active enrolments"
              value="1,102"
              note="Internal status accounting, not official policy"
            />
            <MetricCard
              label="Programme coverage"
              value="6 / 6"
              note="Illustrative; missing is not zero"
            />
          </div>
          <div className="preview-grid">
            <div className="preview-panel">
              <p className="chart-subheading">Records by admission category</p>
              <CategoryBars
                categories={[
                  { label: "Regular", value: 820 },
                  { label: "Management", value: 210 },
                  { label: "NRI", value: 96 },
                  { label: "Supernumerary", value: 122 },
                ]}
              />
            </div>
            <div className="preview-panel">
              <p className="chart-subheading">Status breakdown</p>
              <StatusDonut
                statuses={[
                  { label: "ACTIVE", value: 1102 },
                  { label: "INACTIVE", value: 146 },
                ]}
                total={1248}
              />
            </div>
          </div>
        </Reveal>
      </section>

      {/* Security & Trust */}
      <section className="landing-section" id="security">
        <div className="page-heading landing-section-heading">
          <p className="eyebrow">SECURITY & TRUST</p>
          <h2>Built to be accountable, not just functional</h2>
        </div>
        <Reveal className="security-grid">
          {security.map((entry) => (
            <motion.article
              key={entry.title}
              className="security-card"
              variants={item}
            >
              <h3>{entry.title}</h3>
              <p>{entry.body}</p>
            </motion.article>
          ))}
        </Reveal>
      </section>

      {/* Final CTA */}
      <section className="landing-final-cta">
        <motion.div
          initial={reduce ? undefined : { opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.4 }}
          transition={{ duration: 0.5 }}
        >
          <h2>Bring Clarity to Every Admission.</h2>
          <p>
            Sign in to open your permitted workspace and explore the review flow end
            to end.
          </p>
          <Link className="button primary large" href="/login">
            Sign In / Access Workspace
          </Link>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="landing-footer-brand">
          <strong>PRAVYA</strong>
          <span>Admissions Review &amp; Compliance Platform</span>
        </div>
        <p>
          Synthetic data only. No APAAR identity or government verification is
          performed by this platform.
        </p>
      </footer>
    </main>
  );
}
