import type { ReactNode } from "react";
import { PublicNav } from "@/components/public-nav";

export default function PublicLayout({ children }: { children: ReactNode }) {
  return (
    <div className="public-shell">
      <PublicNav />
      {children}
    </div>
  );
}
