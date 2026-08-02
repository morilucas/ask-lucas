"use client";

import { useSyncExternalStore } from "react";

import styles from "./theme-toggle.module.css";

type Theme = "dark" | "light";

const STORAGE_KEY = "ask-lucas-theme";
const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getTheme(): Theme {
  return document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

function getServerTheme(): Theme {
  return "dark";
}

export function ThemeToggle() {
  const theme = useSyncExternalStore(subscribe, getTheme, getServerTheme);

  function toggleTheme() {
    const nextTheme: Theme = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = nextTheme;
    try {
      localStorage.setItem(STORAGE_KEY, nextTheme);
    } catch {
      // The appearance still changes when browser storage is unavailable.
    }
    listeners.forEach((listener) => listener());
  }

  const isDark = theme === "dark";

  return (
    <button
      type="button"
      className={styles.toggle}
      aria-label={isDark ? "Use light theme" : "Use dark theme"}
      onClick={toggleTheme}
    >
      {isDark ? <SunIcon /> : <MoonIcon />}
      <span>{isDark ? "Light" : "Dark"}</span>
    </button>
  );
}

function SunIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <circle cx="10" cy="10" r="3.25" />
      <path d="M10 2.25v1.5M10 16.25v1.5M2.25 10h1.5M16.25 10h1.5M4.52 4.52l1.06 1.06M14.42 14.42l1.06 1.06M15.48 4.52l-1.06 1.06M5.58 14.42l-1.06 1.06" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <path d="M16.1 12.75A6.8 6.8 0 0 1 7.25 3.9a6.8 6.8 0 1 0 8.85 8.85Z" />
    </svg>
  );
}
