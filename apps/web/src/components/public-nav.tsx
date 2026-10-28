"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { BrandMark } from "@/components/brand-mark";
import { demoAccounts } from "@/features/auth/accounts";

const sections = [
  { id: "overview", label: "Overview" },
  { id: "how-it-works", label: "How It Works" },
  { id: "features", label: "Features" },
  { id: "preview", label: "Platform Preview" },
  { id: "security", label: "Security & Trust" },
];

const groups = [
  {
    heading: "Institution administrator",
    accounts: demoAccounts.filter(
      (account) => account.role === "Institution administrator",
    ),
  },
  {
    heading: "AICTE review access",
    accounts: demoAccounts.filter(
      (account) => account.role !== "Institution administrator",
    ),
  },
];

function SignInMenu({ onNavigate }: { onNavigate?: () => void }) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    if (!open) return;
    function onClick(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node))
        setOpen(false);
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("click", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("click", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="sign-in-menu" ref={containerRef}>
      <button
        type="button"
        className="button primary small"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        Sign In
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            role="menu"
            className="sign-in-dropdown"
            initial={reduceMotion ? false : { opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.16 }}
          >
            <p className="sign-in-dropdown-title">Choose your account</p>
            {groups.map((group) => (
              <div key={group.heading} className="sign-in-group">
                <p className="sign-in-group-label">{group.heading}</p>
                {group.accounts.map((account) => (
                  <Link
                    key={account.alias}
                    role="menuitem"
                    href={`/login?alias=${account.alias}`}
                    className="sign-in-option"
                    onClick={() => {
                      setOpen(false);
                      onNavigate?.();
                    }}
                  >
                    <span className="account-monogram" aria-hidden="true">
                      {account.monogram}
                    </span>
                    <span>
                      <strong>{account.label}</strong>
                      <small>{account.role}</small>
                    </span>
                  </Link>
                ))}
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function PublicNav() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [active, setActive] = useState("overview");
  const onLanding = sections.length > 0;

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 24);
    }
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!onLanding) return;
    const elements = sections
      .map((section) => document.getElementById(section.id))
      .filter((element): element is HTMLElement => !!element);
    if (elements.length === 0) return;
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible?.target.id) setActive(visible.target.id);
      },
      { rootMargin: "-35% 0px -55% 0px", threshold: [0, 0.25, 0.5, 0.75, 1] },
    );
    for (const element of elements) observer.observe(element);
    return () => observer.disconnect();
  }, [onLanding]);

  return (
    <motion.header
      className={`public-nav ${scrolled ? "scrolled" : ""}`}
      initial={false}
      animate={{
        backgroundColor: scrolled
          ? "rgba(252, 250, 244, 0.86)"
          : "rgba(252, 250, 244, 0)",
      }}
      transition={{ duration: 0.25 }}
    >
      <Link href="/">
        <BrandMark tagline="Admissions workspace" />
      </Link>
      <nav aria-label="Primary" className="public-nav-links">
        {sections.map((section) => (
          <a
            key={section.id}
            href={`/#${section.id}`}
            className={`nav-anchor ${active === section.id ? "active" : ""}`}
          >
            {section.label}
            {active === section.id && (
              <motion.span
                className="nav-anchor-pill"
                layoutId="nav-active-pill"
                transition={{ duration: 0.25 }}
              />
            )}
          </a>
        ))}
        <SignInMenu />
      </nav>
      <button
        type="button"
        className="icon-button mobile-only"
        aria-label={menuOpen ? "Close menu" : "Open menu"}
        aria-expanded={menuOpen}
        onClick={() => setMenuOpen((value) => !value)}
      >
        <span className={`burger ${menuOpen ? "open" : ""}`} />
      </button>
      <AnimatePresence>
        {menuOpen && (
          <motion.nav
            aria-label="Mobile"
            className="mobile-nav-panel"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.22 }}
          >
            {sections.map((section) => (
              <a
                key={section.id}
                href={`/#${section.id}`}
                onClick={() => setMenuOpen(false)}
                className={active === section.id ? "active" : ""}
              >
                {section.label}
              </a>
            ))}
            <SignInMenu onNavigate={() => setMenuOpen(false)} />
          </motion.nav>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
