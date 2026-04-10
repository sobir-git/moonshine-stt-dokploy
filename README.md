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
- a root-level Dockerfile so Dokploy can build straight from Git for fast dev loops
- a published GHCR image so Dokploy-only users do not need the source repo at deploy time

## Two ways to use it

### 1. Fast Git deploy

Use the repo root as a normal Dokploy Git app:

- service type: Docker Compose from Git
- file: `docker-compose.yml`
- auto deploy: on
- exposed port: `8000`

That gives you the loop you want:

1. push a commit
2. Dokploy rebuilds from Git
3. click redeploy or let auto deploy do it
4. your update is live

### 2. Dokploy template import

Import the `blueprints/moonshine-stt` folder as a template blueprint.

Dokploy will generate a hidden path like:

`/m-<random>`

If you want the Base64 import string, run:

```bash
python3 scripts/make_payload.py
```

If you just want the raw string without running anything, copy it from [`payload.txt`](./payload.txt).

## Included Files

- `blueprints/moonshine-stt/docker-compose.yml`
- `blueprints/moonshine-stt/template.toml`
- `blueprints/moonshine-stt/Dockerfile`
- `blueprints/moonshine-stt/app.py`
- `blueprints/moonshine-stt/requirements.txt`
- `meta.json`
- `moonshine.png`
- `scripts/make_payload.py`
- `payload.txt`

## How it works

The Base64 payload imports the compose file into Dokploy. That compose file points to a published image in GHCR, so Dokploy does not need to see the Dockerfile during import.

For Git deploys, Dokploy uses the root `docker-compose.yml`, which builds from the root `Dockerfile` and copies the app files from `blueprints/moonshine-stt/`.

## Notes

- The blueprint uses Dokploy’s built-in domain and TLS handling.
- It does not define its own reverse proxy.
- You can change the generated path by editing `blueprints/moonshine-stt/template.toml`.
