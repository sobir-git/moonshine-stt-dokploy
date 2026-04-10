# Moonshine STT Dokploy Template

[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Dokploy](https://img.shields.io/badge/Dokploy-template-111827)](https://dokploy.com/)
[![Moonshine](https://img.shields.io/badge/Moonshine-Voice%20STT-7dd3fc)](https://github.com/moonshine-ai/moonshine)
[![Deploy to Dokploy](https://img.shields.io/badge/Deploy%20to-Dokploy-0ea5e9?logo=cloudflare&logoColor=white)](https://github.com/sobir-git/moonshine-stt-dokploy#readme)

Reusable Dokploy blueprint for self-hosted CPU speech-to-text.

## What it gives you

- Moonshine Voice STT on CPU
- browser upload UI
- microphone recorder
- model picker
- hidden random path routing for Dokploy

## Dokploy Import

Import the `blueprints/moonshine-stt` folder as a template blueprint.

Dokploy will generate a hidden path like:

`/m-<random>`

If you want the Base64 import string, run:

```bash
python3 scripts/make_payload.py
```

## Included Files

- `blueprints/moonshine-stt/docker-compose.yml`
- `blueprints/moonshine-stt/template.toml`
- `blueprints/moonshine-stt/Dockerfile`
- `blueprints/moonshine-stt/app.py`
- `blueprints/moonshine-stt/requirements.txt`
- `meta.json`
- `moonshine.png`
- `scripts/make_payload.py`

## Notes

- The blueprint uses Dokploy’s built-in domain and TLS handling.
- It does not define its own reverse proxy.
- You can change the generated path by editing `blueprints/moonshine-stt/template.toml`.
