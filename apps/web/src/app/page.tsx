import { AnswerWorkspace } from "@/components/answer-workspace";
import { ThemeToggle } from "@/components/theme-toggle";

import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <a className={styles.skipLink} href="#main-content">
        Skip to main content
      </a>

      <header className={styles.header}>
        <div className={styles.identity}>
          <span className={styles.mark} aria-hidden="true">L</span>
          <span className={styles.identityText}>
            <span className={styles.wordmark}>Ask Lucas</span>
            <span className={styles.descriptor}>AI portfolio assistant</span>
          </span>
        </div>
        <div className={styles.headerMeta}>
          <span className={styles.availability}>
            <span aria-hidden="true" />
            Grounded in reviewed sources
          </span>
          <ThemeToggle />
          <nav aria-label="Professional links">
            <a className={styles.headerLink} href="https://www.linkedin.com/in/morilucas/">
              LinkedIn
            </a>
            <a className={styles.headerLink} href="https://github.com/morilucas">
              GitHub
            </a>
          </nav>
        </div>
      </header>

      <main id="main-content" className={styles.main}>
        <AnswerWorkspace />
      </main>
    </div>
  );
}
