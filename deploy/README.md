# Deployment (server: EC2 induction.wcma.work)

Scripts live in `app-src/` and operate on the parent app dir (`/home/ssm-user/apps/induction/`), which holds `compose.yaml` and `.env`. All three scripts copy `deploy/compose.server.yaml` into `../compose.yaml`, so the compose file has a single source of truth in git.

## Scripts

| Script | When | Cost/time | Re-ingest? |
|---|---|---|---|
| `m1_update.sh` | ONCE, first M1 cutover (after `git pull`) | ~8-12 min | Yes (first ingest) |
| `update.sh` | Small backend/frontend code changes | seconds | No |
| `hard_update.sh` | Documents or KB/parsing/chunking logic changed | ~8-12 min | Yes (asks first) |

Run from `/home/ssm-user/apps/induction/app-src/`, e.g. `git pull && bash m1_update.sh`.

## Required server .env keys (M1)

`OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`, `COHERE_API_KEY`, `COHERE_RERANK_MODEL`, `QDRANT_COLLECTION`, `DOCUMENTS_DIR`, `FRONTEND_ORIGIN=https://induction.wcma.work`, `JWT_SECRET`, `POSTGRES_PASSWORD`, `COOKIE_SECURE=true`, `ALLOWED_EMAIL_DOMAIN=wcma.vic.gov.au`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`.

`DATABASE_URL` and `QDRANT_URL` are set by compose (point at the `induction-postgres` / `induction-qdrant` containers); do not hardcode localhost values in the server `.env`.

## nginx (one-time, manual)

The shared `nginx-reverse-proxy` config is at `/home/ssm-user/apps/reverse-proxy/nginx/conf.d/default.conf`. In the `induction.wcma.work` HTTPS (443) server block, the API used to be only `location /chat`. Broaden it to all M1 API paths by changing that one matcher line:

```nginx
location ~ ^/(chat|auth|users|sessions|kb|admin/|health) {
    resolver 127.0.0.11 valid=30s;
    set $induction_api http://induction:8000;
    proxy_pass $induction_api;
    proxy_http_version 1.1;
    proxy_buffering off;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Then validate and reload: `docker exec nginx-reverse-proxy nginx -t && docker exec nginx-reverse-proxy nginx -s reload`. Without this, login/admin/sessions return 404.

IMPORTANT — the `admin/` token has a trailing slash on purpose. `/admin` is ALSO a frontend (Next.js) page, while `/admin/users`, `/admin/prompt`, `/admin/kb` are backend APIs. Matching bare `admin` routes the `/admin` PAGE to the backend, which has no `GET /admin` route and returns `{"detail":"Not Found"}`. The trailing slash sends only the `/admin/...` APIs to the backend and lets the `/admin` page fall through to the frontend. Consider also adding `proxy_read_timeout 300s; proxy_send_timeout 300s;` to this block so a slow streamed `/chat` turn is not cut by nginx's 60s idle timeout.

## Why the backend runs with a kb_index volume

The backend image is `read_only`. The hybrid-retrieval BM25 index is written to `/app/kb_index` at ingest time, so compose mounts a writable named volume (`induction_kb_index`) there. The ingest runs inside the backend container, so the index persists across rebuilds.
