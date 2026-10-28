import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SessionProvider } from "@/features/auth/session";

import "./globals.css";

export const metadata: Metadata = {
  title: "SIH26263 Prototype",
  description: "Synthetic institution records and local admissions workflows.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
