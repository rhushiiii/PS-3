"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, type ReactNode } from "react";
import { homeFor, useSession, type Role } from "@/features/auth/session";
import { BrandMark } from "@/components/brand-mark";
import { DataNotice, Loading } from "@/components/ui/feedback";
import { Icon } from "@/components/ui/icon";
import { NotificationBell } from "@/features/notifications/bell";

const roleNames: Record<Role, string> = {
  INSTITUTION_ADMIN: "Institution administrator",
  AICTE_OFFICER: "AICTE officer",
  AICTE_MANAGER: "AICTE manager",
  AUTHORIZED_VERIFIER: "Authorized verifier",
};

export function Protected({
  roles,
  children,
}: {
  roles: readonly Role[];
  children: ReactNode;
}) {
  const { session } = useSession();
  const router = useRouter();
  const allowed = session && roles.includes(session.user.role);
  useEffect(() => {
    if (!session) router.replace("/login");
    else if (!allowed) router.replace("/access-denied");
  }, [session, allowed, router]);
  if (!allowed)
    return (
      <div className="session-loading">
        <Loading label="Checking local session…" />
      </div>
    );
  return children;
}

export function AppShell({ children }: { children: ReactNode }) {
  const { session, signOut } = useSession();
  const pathname = usePathname();
  const menu = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    menu.current?.close();
  }, [pathname]);
  if (!session) return null;
  const role = session.user.role;
  const institution = role === "INSTITUTION_ADMIN";
  const officer = role === "AICTE_OFFICER";
  const verifier = role === "AUTHORIZED_VERIFIER";
  const destination = homeFor(role);
  const label = verifier ? "Verify credential" : "Dashboard";
  const verifyLinks = [
    {
      href: "/verify",
      label: "Verify credential",
      icon: "flag" as const,
    },
    {
      href: "/verify/log",
      label: "Verification log",
      icon: "history" as const,
    },
  ];
  const links = verifier
    ? verifyLinks
    : [
        {
          href: destination,
          label,
          icon: institution ? ("grid" as const) : ("building" as const),
        },
        ...(institution
          ? [
              {
                href: "/institution/upload",
                label: "Upload candidate",
                icon: "upload" as const,
              },
            ]
          : [
              {
                href: "/aicte/institutions",
                label: "Institutions",
                icon: "building" as const,
              },
            ]),
        ...(!institution && !verifier
          ? [
              {
                href: "/analytics",
                label: "Analytics",
                icon: "grid" as const,
              },
            ]
          : []),
        {
          href: "/reports",
          label: "Reports",
          icon: "history" as const,
        },
        ...(officer
          ? [
              {
                href: "/audit",
                label: "Audit explorer",
                icon: "history" as const,
              },
            ]
          : []),
        ...(institution || officer
          ? [
              {
                href: "/submissions",
                label: "Submissions",
                icon: "history" as const,
              },
              {
                href: "/records",
                label: "Student registry",
                icon: "grid" as const,
              },
              {
                href: "/credentials",
                label: "Credentials",
                icon: "flag" as const,
              },
            ]
          : []),
        ...(officer
          ? [
              {
                href: "/verification",
                label: "APAAR verification",
                icon: "building" as const,
              },
              ...verifyLinks,
            ]
          : []),
        ...(institution || officer
          ? [
              {
                href: "/cases",
                label: "Cases",
                icon: "flag" as const,
              },
              {
                href: "/notifications",
                label: "Notifications",
                icon: "bell" as const,
              },
            ]
          : []),
      ];
  const currentLabel =
    links.find((link) => link.href === pathname)?.label ?? label;

  const navigation = (
    <>
      <Link href={destination} onClick={() => menu.current?.close()}>
        <BrandMark tagline="Admissions workspace" />
      </Link>
      <p className="nav-caption">WORKSPACE</p>
      <nav aria-label="Main navigation">
        {links.map((link) => (
          <Link
            key={link.href}
            className={`nav-link ${pathname === link.href ? "active" : ""}`}
            href={link.href}
            aria-current={pathname === link.href ? "page" : undefined}
            onClick={() => menu.current?.close()}
          >
            <Icon name={link.icon} />
            {link.label}
          </Link>
        ))}
      </nav>
      <div className="sidebar-footer">
        <span className="tiny-label">SECURE WORKSPACE</span>
        <strong>{roleNames[session.user.role]}</strong>
        <p>Synthetic accounts. Backend permissions apply to every request.</p>
        <button className="sign-out" onClick={signOut}>
          <Icon name="exit" />
          Sign out
        </button>
      </div>
    </>
  );

  return (
    <div className="portal-layout">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className="sidebar">{navigation}</aside>
      <div className="portal-main">
        <header className="topbar">
          <div className="topbar-title">
            <button
              className="icon-button mobile-only"
              aria-label="Open navigation"
              onClick={() => menu.current?.showModal()}
            >
              <Icon name="menu" />
            </button>
            <span>
              Workspace <span aria-hidden="true">/</span>{" "}
              <strong>{currentLabel}</strong>
            </span>
          </div>
          <div className="topbar-actions">
            <NotificationBell />
            <div className="account-label">
              <span className="account-dot" aria-hidden="true">
                {institution ? "IN" : "AI"}
              </span>
              <span>
                {roleNames[session.user.role]}
                <small>Direct local access</small>
              </span>
            </div>
          </div>
        </header>
        <DataNotice />
        <main id="main-content" className="page-content" tabIndex={-1}>
          {children}
        </main>
        <footer className="portal-footer">
          PRAVYA
          <span>
            Institution declarations · Local checks · Traceable history
          </span>
        </footer>
      </div>
      <dialog
        ref={menu}
        className="mobile-navigation"
        aria-label="Workspace navigation"
      >
        <button
          className="icon-button close-menu"
          aria-label="Close navigation"
          onClick={() => menu.current?.close()}
        >
          <Icon name="close" />
        </button>
        {navigation}
      </dialog>
    </div>
  );
}
