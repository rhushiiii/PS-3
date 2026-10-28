import type { Metadata } from "next";
import { Manrope, Inter } from "next/font/google";
import type { ReactNode } from "react";

import { SessionProvider } from "@/features/auth/session";

import "./globals.css";

const heading = Manrope({
  subsets: ["latin"],
  variable: "--next-font-heading",
  display: "swap",
});
const body = Inter({
  subsets: ["latin"],
  variable: "--next-font-body",
  display: "swap",
});

export const metadata: Metadata = {
  title: "PRAVYA — Admissions Review & Compliance Platform",
  description:
    "APAAR-aware admissions validation, evidence-linked review and auditable decisions for AICTE-approved institutions.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${heading.variable} ${body.variable}`}>
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
