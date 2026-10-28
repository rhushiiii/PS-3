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
    body: "An institution administrator submits a complete admissions snapshot as a structured CSV. The upload is stored as an immutable candidate.",
  },
  {
    title: "Validate Rules",
    body: "Local APAAR format checks and configured intake rules run against the candidate, producing a deterministic, repeatable result.",
  },
  {
    title: "Flag Exceptions",
    body: "Missing fields, format issues and potential cross-institution duplicates are surfaced as evidence-linked findings — leads, not verdicts.",
  },
  {
    title: "Review & Resolve",
    body: "An officer reviews findings in context, can request verification or open a case, and the institution's correction becomes a new version.",
  },
];

const features = [
  {
    title: "APAAR format validation",
    body: "Structural checks run locally against configured rules. Explicitly labeled as local format checking, never official government identity verification.",
  },
  {
    title: "Admission record management",
    body: "Every uploaded batch is stored as a permanent, append-only version, with full provenance of who submitted what and when.",
  },
  {
    title: "Intake rule checks",
    body: "Declared admissions are compared against configured category and seat-capacity rules, with missing configuration surfaced rather than assumed.",
  },
  {
    title: "Evidence-linked review",
    body: "Findings carry rule codes and redacted evidence. A finding is a lead for officer review, never an automatic determination.",
  },
  {
    title: "Exception tracking",
    body: "Officers can open a case against specific records, request a correction, and track its resolution on an append-only timeline.",
  },
  {
    title: "Audit trails and accountability",
    body: "Snapshot activation requires explicit review and acknowledgment. Every state-changing action is recorded with actor and timestamp.",
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
      viewport={{ once: true, amount: 0.25 }}
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
      <section className="landing-hero">
        <TricolorCanvas className="landing-hero-canvas" />
        <motion.div
          className="landing-hero-content"
          initial={reduce ? undefined : { opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
        >
          <p className="eyebrow hero-eyebrow">APAAR-AWARE ADMISSIONS REVIEW</p>
          <h1 className="hero-headline">
            <span className="gradient-text">Smarter Admissions.</span>
            <br />
            Stronger Trust.
          </h1>
          <p className="landing-lede hero-lede">
            A deterministic, evidence-linked workflow for validating local APAAR
            format and intake rules, reviewing exceptions, and keeping an
            auditable trail — for AICTE-approved institutions.
          </p>
          <div className="landing-cta">
            <a className="button primary" href="#overview">
              Explore Platform
            </a>
            <a className="button secondary ghost" href="#how-it-works">
              How It Works
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

      <HowItWorks />

      <section className="landing-section" id="features">
        <div className="page-heading landing-section-heading">
          <p className="eyebrow">CAPABILITIES</p>
          <h2>Built around evidence, not assumptions</h2>
          <p>
            All data shown anywhere in this platform is synthetic. Nothing here
            is, or claims to be, connected to a real government system.
          </p>
        </div>
        <Reveal className="feature-grid">
          {features.map((feature) => (
            <motion.article
              key={feature.title}
              className="feature-card"
              variants={item}
              whileHover={reduce ? undefined : { y: -4 }}
              transition={{ duration: 0.3 }}
            >
              <h3>{feature.title}</h3>
              <p>{feature.body}</p>
            </motion.article>
          ))}
        </Reveal>
      </section>

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

      <section className="landing-final-cta">
        <motion.div
          initial={reduce ? undefined : { opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.4 }}
          transition={{ duration: 0.5 }}
        >
          <h2>Bring Clarity to Every Admission.</h2>
          <p>
            Sign in to open your permitted workspace and see the review flow end
            to end.
          </p>
          <Link className="button primary large" href="/login">
            Sign In / Access Workspace
          </Link>
        </motion.div>
      </section>

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
