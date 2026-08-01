import type { Metadata } from "next";
import { Inter, Newsreader } from "next/font/google";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const newsreader = Newsreader({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Ask Lucas — Grounded AI portfolio",
  description:
    "Ask about Lucas Mori's work through answers grounded in reviewed public sources.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${newsreader.variable}`}>
      <body>{children}</body>
    </html>
  );
}
