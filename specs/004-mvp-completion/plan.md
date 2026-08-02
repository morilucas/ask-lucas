# Plan 004: MVP completion and content operations

1. Freeze the existing API boundary and disjoint file ownership in the feature specification.
2. Run Claude's content-validation and atomic-index work in an isolated VPS worktree.
3. Build the conversation-state, evidence-navigation, and System Lens work locally at the same time.
4. Review Claude's complete commit and send bounded corrections while completing frontend checks.
5. Integrate both streams, rerun all backend and frontend verification, and inspect the combined diff.
6. Publish, deploy, validate the mounted private content without printing it, rebuild the index, and
   smoke-test the live experience.

The next project phase is structured private-content authoring. Real evaluation and the vector/hybrid
retrieval comparison follow that content review.
