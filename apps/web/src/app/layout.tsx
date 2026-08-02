import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import "./globals.css";

const themeInitializer = `
  try {
    const savedTheme = localStorage.getItem("ask-lucas-theme");
    document.documentElement.dataset.theme = savedTheme === "light" ? "light" : "dark";
  } catch {}
`;

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Ask Lucas — Grounded AI portfolio",
  description:
    "Ask about Lucas Mori's work through answers grounded in reviewed public sources.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${geist.variable} ${geistMono.variable}`}
      data-theme="dark"
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitializer }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
