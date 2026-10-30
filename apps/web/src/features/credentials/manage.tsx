"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Pagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import { errorMessage } from "@/lib/api/client";
import type { components } from "@/lib/api/generated";
import {
  credentialState,
  when,
  type CredentialPage,
  type CredentialSummary,
} from "./shared";

type IssueResponse = components["schemas"]["IssueResponse"];
const PAGE_SIZE = 20;

function useCredentialScope() {
  const { session } = useSession();
  return ["private", session?.generation, session?.user.id, "credentials"];
}

function CredentialTable({
  items,
  showRecord,
  onRevoke,
}: {
  items: CredentialSummary[];
  showRecord: boolean;
  onRevoke?: (c: CredentialSummary) => void;
}) {
  return (
    <div
      className="table-scroll"
      tabIndex={0}
      role="region"
      aria-label="Issued credentials"
    >
      <table className="review-table">
        <caption>Issued credentials · SIMULATED / DEMO DATA</caption>
        <thead>
          <tr>
            <th scope="col">Credential</th>
            {showRecord && <th scope="col">Record</th>}
            <th scope="col">Issued</th>
            <th scope="col">Expires</th>
            <th scope="col">State</th>
            {onRevoke && <th scope="col">Action</th>}
          </tr>
        </thead>
        <tbody>
          {items.map((c) => {
            const state = credentialState(c);
            return (
              <tr key={c.id}>
                <th scope="row">
                  <code>{c.id.slice(0, 8)}</code>
                </th>
                {showRecord && (
                  <td>
                    <Link href={`/records/${c.record_version_id}`}>
                      Open record
                    </Link>
                  </td>
                )}
                <td>{when(c.issued_at)}</td>
                <td>{when(c.expires_at)}</td>
                <td>
                  <span className={`status-badge ${state.tone}`}>
                    {state.label}
                  </span>
                  {c.revoked && c.revoked_at && (
                    <span className="cell-note">{when(c.revoked_at)}</span>
                  )}
                </td>
                {onRevoke && (
                  <td>
                    {c.revoked ? (
                      "—"
                    ) : (
                      <button
                        className="button secondary small"
                        onClick={() => onRevoke(c)}
                      >
                        Revoke
                      </button>
                    )}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function CredentialList() {
  const { session, request } = useSession();
  const scope = useCredentialScope();
  const [page, setPage] = useState(1);
  const list = useQuery({
    queryKey: [...scope, "list", page],
    enabled: !!session,
    queryFn: ({ signal }) =>
      request<CredentialPage>(
        `/credentials?page=${page}&page_size=${PAGE_SIZE}`,
        { signal },
      ),
  });
  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">CREDENTIALS · SIMULATED / DEMO DATA</p>
        <h1>Admission credentials</h1>
        <p>
          Issued DEMO credentials. Tokens are shown only once at issue time and
          are never listed. Issue or revoke from a record&apos;s detail page.
        </p>
      </div>
      <section className="panel" aria-labelledby="cred-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">ISSUED</p>
            <h2 id="cred-title">Credentials</h2>
          </div>
        </header>
        {list.isPending ? (
          <Loading label="Loading credentials…" />
        ) : list.isError ? (
          <ErrorPanel error={list.error} retry={() => void list.refetch()} />
        ) : list.data.data.length === 0 ? (
          <div className="empty-state">
            <h3>No credentials issued</h3>
            <p>
              Open a current, active record in the{" "}
              <Link href="/records">student registry</Link> to issue one.
            </p>
          </div>
        ) : (
          <CredentialTable items={list.data.data} showRecord />
        )}
        {list.data && (
          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            total={list.data.pagination.total}
            busy={list.isFetching}
            change={setPage}
          />
        )}
      </section>
    </>
  );
}

type Pending = { kind: "issue" } | { kind: "revoke"; id: string };

/** Credential card for the record detail page (caller checks eligibility). */
export function RecordCredentialCard({
  recordVersionId,
}: {
  recordVersionId: string;
}) {
  const { session, request } = useSession();
  const queryClient = useQueryClient();
  const scope = useCredentialScope();
  const [pending, setPending] = useState<Pending | null>(null);
  const [reason, setReason] = useState("");
  const [dialogError, setDialogError] = useState("");
  const [issued, setIssued] = useState<{
    token: string;
    expires: string;
  } | null>(null);
  const [copied, setCopied] = useState<"" | "yes" | "no">("");
  const [message, setMessage] = useState("");

  const list = useQuery({
    queryKey: [...scope, "record", recordVersionId],
    enabled: !!session,
    queryFn: async ({ signal }) => {
      // The API has no record filter; fetch a page and filter client-side.
      const page = await request<CredentialPage>(
        "/credentials?page=1&page_size=100",
        { signal },
      );
      return {
        items: page.data.filter((c) => c.record_version_id === recordVersionId),
        truncated: page.pagination.total > page.data.length,
      };
    },
  });
  const refresh = () => queryClient.invalidateQueries({ queryKey: scope });

  const issue = useMutation({
    mutationFn: () =>
      request<IssueResponse>("/credentials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ record_version_id: recordVersionId }),
      }),
    onSuccess: async (data) => {
      setPending(null);
      setDialogError("");
      setMessage("");
      setCopied("");
      setIssued({
        token: data.token,
        expires: data.credential.expires_at,
      });
      await refresh();
    },
    onError: (e) => setDialogError(errorMessage(e)),
  });
  const revoke = useMutation({
    mutationFn: (v: { id: string; reason: string }) =>
      request<unknown>(`/credentials/${v.id}/revoke`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: v.reason }),
      }),
    onSuccess: async () => {
      setPending(null);
      setReason("");
      setDialogError("");
      setMessage("Credential revoked.");
      await refresh();
    },
    onError: (e) => setDialogError(errorMessage(e)),
  });

  const close = () => {
    setPending(null);
    setReason("");
    setDialogError("");
  };
  const confirm = () => {
    if (!pending) return;
    if (pending.kind === "issue") return issue.mutate();
    if (!reason.trim()) {
      setDialogError("A reason is required to revoke a credential.");
      return;
    }
    revoke.mutate({ id: pending.id, reason: reason.trim() });
  };
  async function copy() {
    if (!issued) return;
    try {
      await navigator.clipboard.writeText(issued.token);
      setCopied("yes");
    } catch {
      setCopied("no");
    }
  }

  return (
    <section className="panel" aria-labelledby="cred-card-title">
      <header className="panel-heading">
        <div>
          <p className="eyebrow">SIMULATED / DEMO DATA</p>
          <h2 id="cred-card-title">Admission credential</h2>
        </div>
        <button
          className="button secondary small"
          disabled={issue.isPending}
          onClick={() => {
            setMessage("");
            setPending({ kind: "issue" });
          }}
        >
          Issue credential
        </button>
      </header>
      {issued && (
        <div className="token-panel" role="status">
          <h3>Credential issued — copy it now</h3>
          <p className="form-error">
            This token is shown only once and is not stored. It will not be
            shown again; if lost, revoke and issue a new one.
          </p>
          <textarea
            readOnly
            rows={4}
            value={issued.token}
            aria-label="Credential token"
            onFocus={(e) => e.currentTarget.select()}
          />
          <div className="button-row">
            <button className="button primary small" onClick={copy}>
              Copy token
            </button>
            <button
              className="button secondary small"
              onClick={() => {
                setIssued(null);
                setCopied("");
              }}
            >
              Dismiss
            </button>
            <span role="status" className="cell-note">
              {copied === "yes"
                ? "Copied."
                : copied === "no"
                  ? "Copy failed — select the text and copy manually."
                  : ""}
            </span>
          </div>
          <p className="data-note">
            A QR code is only a carrier for this text; it is not proof of
            anything. Verification relies on the signature check. Expires{" "}
            {when(issued.expires)}. DEMO credential — not an official AICTE,
            APAAR or government document.
          </p>
        </div>
      )}
      {message && (
        <p className="data-note" role="status">
          {message}
        </p>
      )}
      {list.isPending ? (
        <Loading label="Loading credentials…" />
      ) : list.isError ? (
        <ErrorPanel error={list.error} retry={() => void list.refetch()} />
      ) : list.data.items.length === 0 ? (
        <div className="empty-state">
          <h3>No credentials issued for this record</h3>
        </div>
      ) : (
        <>
          <CredentialTable
            items={list.data.items}
            showRecord={false}
            onRevoke={(c) => {
              setMessage("");
              setPending({ kind: "revoke", id: c.id });
            }}
          />
          {list.data.truncated && (
            <p className="data-note">
              Showing credentials from the first 100 in your scope only.
            </p>
          )}
        </>
      )}
      <ConfirmDialog
        open={pending !== null}
        title={
          pending?.kind === "revoke"
            ? "Revoke credential?"
            : "Issue credential?"
        }
        confirmLabel={pending?.kind === "revoke" ? "Revoke" : "Issue"}
        busy={issue.isPending || revoke.isPending}
        onConfirm={confirm}
        onCancel={close}
      >
        {pending?.kind === "revoke" ? (
          <>
            <p>
              Revoked credentials fail verification immediately. This cannot be
              undone.
            </p>
            <label className="dialog-field">
              Reason (required)
              <textarea
                rows={3}
                maxLength={500}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </label>
          </>
        ) : (
          <p>
            Issue a signed DEMO credential for this record. The token is shown
            once.
          </p>
        )}
        {dialogError && (
          <p className="form-error" role="alert">
            {dialogError}
          </p>
        )}
      </ConfirmDialog>
    </section>
  );
}
