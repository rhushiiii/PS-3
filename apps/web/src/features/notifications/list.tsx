"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Pagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import { errorMessage } from "@/lib/api/client";
import type { components } from "@/lib/api/generated";

type NotificationPage = components["schemas"]["Page_NotificationResponse_"];

export function NotificationList() {
  const { session, request } = useSession();
  const queryClient = useQueryClient();
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const scope = [
    "private",
    session?.generation,
    session?.user.id,
    "notifications",
  ];

  const list = useQuery({
    queryKey: [...scope, "list", unreadOnly, page],
    enabled: !!session,
    queryFn: ({ signal }) => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: "20",
      });
      if (unreadOnly) params.set("unread", "true");
      return request<NotificationPage>(`/notifications?${params}`, { signal });
    },
  });

  const mark = useMutation({
    mutationFn: (id: string | "all") =>
      request<unknown>(
        id === "all" ? "/notifications/read-all" : `/notifications/${id}/read`,
        { method: "POST" },
      ),
    onSuccess: async (_data, id) => {
      setError("");
      setNotice(
        id === "all"
          ? "All notifications marked as read."
          : "Notification marked as read.",
      );
      await queryClient.invalidateQueries({ queryKey: scope });
    },
    onError: (mutationError) => {
      setNotice("");
      setError(errorMessage(mutationError));
    },
  });

  const anyUnread = list.data?.data.some((n) => !n.read_at) ?? false;

  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">ACTIVITY</p>
        <h1>Notifications</h1>
        <p>Updates about cases that involve you or your institution.</p>
      </div>
      <section className="panel" aria-labelledby="notifications-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">INBOX</p>
            <h2 id="notifications-title">Your notifications</h2>
          </div>
          <div className="notification-actions">
            <label className="inline-filter">
              Show
              <select
                value={unreadOnly ? "unread" : "all"}
                onChange={(event) => {
                  setUnreadOnly(event.target.value === "unread");
                  setPage(1);
                }}
              >
                <option value="all">All</option>
                <option value="unread">Unread only</option>
              </select>
            </label>
            <button
              type="button"
              className="button secondary small"
              disabled={mark.isPending || !anyUnread}
              onClick={() => mark.mutate("all")}
            >
              Mark all as read
            </button>
          </div>
        </header>
        <div aria-live="polite" className="panel-padding">
          {notice && <p className="form-success">{notice}</p>}
        </div>
        {error && (
          <p className="form-error panel-padding" role="alert">
            {error}
          </p>
        )}
        {list.isPending ? (
          <Loading label="Loading notifications…" />
        ) : list.isError ? (
          <ErrorPanel error={list.error} retry={() => void list.refetch()} />
        ) : list.data.data.length === 0 ? (
          <div className="empty-state">
            <h3>
              {unreadOnly ? "No unread notifications" : "Nothing here yet"}
            </h3>
            <p>
              {unreadOnly
                ? "You are all caught up."
                : "Notifications appear when a case is assigned, a correction is requested or a case is updated."}
            </p>
          </div>
        ) : (
          <ul className="institution-list" style={{ listStyle: "none" }}>
            {list.data.data.map((item) => {
              const unread = !item.read_at;
              return (
                <li
                  key={item.id}
                  className={`notification-item ${unread ? "unread" : ""}`}
                >
                  <span
                    className={`unread-dot ${unread ? "" : "read"}`}
                    aria-hidden="true"
                  />
                  <div>
                    <h3>
                      {item.title}
                      <span className="sr-only">
                        {unread ? " (unread)" : " (read)"}
                      </span>
                    </h3>
                    <p>{item.body}</p>
                    <p>
                      <time dateTime={item.created_at}>
                        {new Date(item.created_at).toLocaleString()}
                      </time>
                    </p>
                  </div>
                  <div className="notification-actions">
                    {item.case_id && (
                      <Link
                        className="button secondary small"
                        href={`/cases/${item.case_id}`}
                      >
                        View case
                      </Link>
                    )}
                    {unread && (
                      <button
                        type="button"
                        className="button secondary small"
                        disabled={mark.isPending}
                        onClick={() => mark.mutate(item.id)}
                      >
                        Mark as read
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
        {list.data && (
          <Pagination
            page={page}
            pageSize={20}
            total={list.data.pagination.total}
            busy={list.isFetching}
            change={setPage}
            label="Notifications pagination"
          />
        )}
      </section>
    </>
  );
}
