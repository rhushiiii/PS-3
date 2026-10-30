import { Protected } from "@/components/app-shell";
import { NotificationList } from "@/features/notifications/list";

export default function NotificationsPage() {
  return (
    <Protected roles={["INSTITUTION_ADMIN", "AICTE_OFFICER"]}>
      <NotificationList />
    </Protected>
  );
}
