"use client";

import Link from "next/link";
import { homeFor, useSession } from "@/features/auth/session";

export default function AccessDenied() {
  const { session, signOut } = useSession();
  return (
    <section className="panel access-panel">
      <p className="eyebrow">PERMISSIONS</p>
      <h1>Access unavailable</h1>
      <p>
        Your current role does not have access to this page. Backend
        authorization remains in force.
      </p>
      <div className="button-row">
        {session && session.user.role !== "AUTHORIZED_VERIFIER" && (
          <Link className="button primary" href={homeFor(session.user.role)}>
            Return to workspace
          </Link>
        )}
        <button className="button secondary" onClick={signOut}>
          Sign out
        </button>
      </div>
    </section>
  );
}
