"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Icon } from "@/components/ui/icon";
import { useSession } from "@/features/auth/session";
import type { components } from "@/lib/api/generated";

type Unread = components["schemas"]["UnreadCountResponse"];

export const NOTIFICATION_ROLES = ["INSTITUTION_ADMIN", "AICTE_OFFICER"];

/** Topbar bell. Polls every minute; TanStack pauses polling in hidden tabs. */
export function NotificationBell() {
  const { session, request } = useSession();
  const allowed = !!session && NOTIFICATION_ROLES.includes(session.user.role);
  const count = useQuery({
    queryKey: [
      "private",
      session?.generation,
      session?.user.id,
      "notifications",
      "unread-count",
    ],
    enabled: allowed,
    refetchInterval: 60_000,
    refetchIntervalInBackground: false,
    queryFn: ({ signal }) =>
      request<Unread>("/notifications/unread-count", { signal }),
  });
  if (!allowed) return null;
  const unread = count.data?.unread ?? 0;
  return (
    <Link
      className="bell-link"
      href="/notifications"
      aria-label={
        count.isError
          ? "Notifications (unread count unavailable)"
          : `Notifications, ${unread} unread`
      }
    >
      <Icon name="bell" />
      {unread > 0 && (
        <span className="bell-count" aria-hidden="true">
          {unread > 99 ? "99+" : unread}
        </span>
      )}
    </Link>
  );
}
