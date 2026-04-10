# Moonshine STT Dokploy Template

Reusable Dokploy blueprint for self-hosted CPU speech-to-text.

Features:

- Moonshine Voice STT
- browser upload UI
- microphone recorder
- model picker
- hidden random path

## Use in Dokploy

Import the `blueprints/moonshine-stt` folder as a template blueprint.

The generated deployment will route to a hidden path under a random domain, for example:

`/m-<random>`

## What’s included

- `docker-compose.yml`
- `template.toml`
- `Dockerfile`
- `app.py`
- `requirements.txt`
- `moonshine.svg`

## Notes

The blueprint is designed for Dokploy’s built-in domain and TLS handling. It does not define its own reverse proxy.
