# Secrets Policy

- **Never commit real `.env` files**. Only `.env.example` is tracked.
- Local dev: copy `.env.example` → `.env` and fill in values.
- CI/CD: inject secrets via environment variables (not files).
- Rotation: update values in `.env` locally and re-share `.env.example` if new keys are added.
- Optional: use a secret manager (Vault, Doppler, AWS/GCP/ Azure secrets) for production.
