# Rollback — checkpoint `m1-stable`

A known-good checkpoint of the induction chatbot. If a later change breaks things, return to this exact state.

## What this checkpoint is

1. Tag: `m1-stable`
2. Commit: `05afd88` ("Fix nginx matcher so the /admin page reaches the frontend")
3. Verified: `app.eval_harness` 11/11; `app.smoke` Cases 1–12 clean. Re-ingest produces ~385 chunks / ~368 clauses.
4. Config: answer lane Claude Opus 4.8; fast lane `gpt-5.4-mini`. Full final config in `.cursor/blueprint.md`.

## Local rollback

From `c:\Users\m.rahman\src\induction`:

1. Stash or discard current work:
   ```powershell
   git stash
   ```
2. Go to the checkpoint:
   ```powershell
   git checkout m1-stable
   ```
   (Detached HEAD. To keep working from here: `git checkout -b recover-from-m1-stable`.)
3. Or hard-reset `main` back to it (DESTRUCTIVE — discards commits after the tag):
   ```powershell
   git reset --hard m1-stable
   ```
4. Restart the backend (Terminal 2) and frontend (Terminal 3) per `.cursor/manual.md`.

## Decide: do you need a re-ingest?

Re-ingest is SLOW (~8–12 min), costs API, and WIPES the Qdrant collection (incl. trainer-added KB).

1. The state you are rolling back FROM only touched `app/rag/**` or `frontend/**` → NO re-ingest. Restart only.
2. The state you are rolling back FROM touched `app/kb/**`, `documents/`, or the clause/map schema → RE-INGEST after checkout:
   ```powershell
   .\.venv\Scripts\python.exe -m app.kb.ingest_kb
   ```
3. The state you are rolling back FROM changed `DEFAULT_SYSTEM_PROMPT` → re-seed the stored prompt:
   ```powershell
   .\.venv\Scripts\python.exe -m app.reset_prompt
   ```

## Server rollback (EC2, induction.wcma.work)

From `/home/ssm-user/apps/induction/app-src/` (see `.cursor/handover.md` §8 for SSH/SSM access):

1. Fetch tags and check out the checkpoint:
   ```bash
   git fetch --tags
   git checkout m1-stable
   ```
2. Redeploy:
   - Code-only change being reverted → `bash update.sh` (rebuild + restart, no re-ingest).
   - Ingestion/parsing/chunking/clause-schema or `documents/` change being reverted → `bash hard_update.sh` (rebuild + full re-ingest inside the container).
3. If `DEFAULT_SYSTEM_PROMPT` differs from what's stored:
   ```bash
   docker compose exec -T induction python -m app.reset_prompt
   ```
4. Verify:
   ```bash
   docker compose exec -T induction python -m app.eval_harness
   docker compose exec -T induction python -m app.smoke
   ```
   Expect 11/11 and no abstentions on Cases 1–12.

## Verify after any rollback

1. `app.eval_harness` → OVERALL 11/11.
2. `app.smoke` → no abstentions on Cases 1–12.
