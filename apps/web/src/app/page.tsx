import { AnswerWorkspace } from "@/components/answer-workspace";

import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <a className={styles.skipLink} href="#main-content">
        Skip to main content
      </a>

      <header className={styles.header}>
        <div className={styles.identity}>
          <span className={styles.wordmark}>Ask Lucas</span>
          <span className={styles.descriptor}>Grounded AI portfolio</span>
        </div>
        <a className={styles.headerLink} href="https://github.com/morilucas">
          GitHub
        </a>
      </header>

      <main id="main-content" className={styles.main}>
        <section className={styles.introduction} aria-labelledby="page-title">
          <p className={styles.eyebrow}>AI engineering portfolio</p>
          <h1 id="page-title">Ask about Lucas&apos;s work.</h1>
          <p className={styles.lede}>
            Explore his experience, projects, and approach through answers grounded in reviewed
            public sources.
          </p>
        </section>

        <AnswerWorkspace />
      </main>

      <footer className={styles.footer}>
        <p>An AI representation based on reviewed public sources. Questions are not stored.</p>
        <nav aria-label="Professional links">
          <a href="https://www.linkedin.com/in/morilucas/">LinkedIn</a>
          <a href="https://github.com/morilucas">GitHub</a>
        </nav>
      </footer>
    </div>
  );
}
