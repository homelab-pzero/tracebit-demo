# acme-billing

Invoice rendering service for Acme. Python 3.12, deployed to AWS (ECS) with
the vendored `deploy-kit` (see `docs/DEPLOY.md`).

## Layout

- `src/` – the service
- `deploy.sh` – wraps `vendor/deploy-kit`
- `docs/DEPLOY.md` – how releases go out
