# RETRO-0005: GitHub connections sprint (CR-01KXAZX9): stored credentials plus five review fixes

> **Date:** 2026-07-12
> **Batch:** CR-01KXAZX9
> **Goal:** Make a GitHub credential a first-class stored entity, so adding the Nth repo is a pick-and-click.
> **Delivered:** 1 / 1   **Blocked:** 0

## Delivered

- **CR-01KXAZX9** - Stored GitHub connections. A `github_connections` table (migration 011) holding a unique
  label, the GitHub `login` resolved and validated at save time via `GET /user`, a Fernet-encrypted token and a
  `last_validated_at` stamp; CRUD + revalidate + rotate at `/api/v1/connections`; the CR-01KXAS75 browse
  endpoints now take a `connection_id` as an alternative to a raw token; `projects.connection_id` with sync
  token precedence; Settings connection management and a ProjectForm connection picker. Registering a credential
  once removes the PAT paste from every subsequent repo add.

## Blocked / deferred

- None.

## What went well

- Locking the API contract in the orchestrator's prompt let the backend and frontend halves be built
  **concurrently against a spec neither owned**, over disjoint file surfaces, and integrate first time with no
  drift. The one contract collision (an existing test asserting 422 where the contract said 400) was surfaced
  explicitly by the backend seat rather than silently bent.
- The adversarial review paid for itself many times over: it found **five real defects**, including one HIGH that
  defeated the CR's entire purpose. Every finding was reproduced with a concrete scenario before being accepted,
  and the reviewer's tautology hunt (mutating the code to prove the new tests go red) confirmed the key tests
  were honest.

## What was hard / what stalled

- **The feature worked and was still wrong.** All 698 tests passed, the contract was met, and the UX did what was
  asked - yet adopting a connection never deleted the PAT it replaced. Revoking that PAT on GitHub would not have
  removed it from the lens, and detaching the connection silently reverted to the revoked token. No test asked
  "is the secret it replaced actually *gone*?", because the CR's acceptance criteria described what the feature
  should *do*, not what it should *undo*. The lesson generalises: a criterion phrased as "the new path works"
  never catches "the old path is still live".
- **"Fernet-encrypted" was true in the code and false in the deployment.** The key was set in no compose file, no
  Dockerfile, no `.env.example` - so the shipped config stored tokens in plaintext while the model docstring and
  the commit message both asserted encryption. The claim was never checked against the artefact that actually runs.

## Lessons

- **A feature that centralises a secret must be reviewed for the secret's whole lifecycle, not just its happy
  path** - where it is written, but also what it *replaces* (is the old copy purged?), how it is *rotated*, and
  what happens when the key to it is *lost*. Four of the five defects lived in that lifecycle; none was in the
  create path everyone was looking at.
  <!-- promote the durable, cross-project ones: lessons add --global -->
- **Verify a security claim against the config that ships, not the code that implements it.** "It is encrypted" is
  a claim about the running deployment; grep the compose / env / Dockerfile, not just the module.
- **A degraded-crypto path must fail closed, not pass through.** `decrypt_token` returned the ciphertext when no
  key was configured, so the app would have sent it to a third party as a Bearer token and then blamed the user's
  credential. A decrypt that cannot decrypt must return None and say why.
- **Beware a test schema stricter than production.** `create_all` built an FK that the SQLite migration cannot
  add, so the orphan branch was unconstructable in tests and perfectly reachable in prod - the worst split,
  because the tests actively hid the live bug.
- **Lock the API contract in writing before parallelising across the stack.** It is what let two agents build
  opposite halves of one feature simultaneously and integrate clean.

## Metrics

- Units: 1/1 delivered. Backend tests 670 -> 720 (+50: 28 feature, 22 hardening). Frontend 216 -> 234 (+18).
  Alembic head 010 -> 011. tsc + eslint clean; ruff clean bar the pre-existing `SortField` hint (out of scope).
  Gate: PASS. Critic: 5 findings (1 high, 3 medium, 1 low), all confirmed real and all fixed; 0 rejected.
