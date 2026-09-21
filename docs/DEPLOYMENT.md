# Deployment — BotScope

pip install; CLI `botscope`; optional GUI; optional Cloudflare Radar token.

## Minimal path

See [`acquisition/BUYER_DEMO.md`](./acquisition/BUYER_DEMO.md).

## Rollback

- Application projects: redeploy previous release tag / prior container digest.
- Documentation corpora (ETW): revert git tag; do not delete historical license tags.
