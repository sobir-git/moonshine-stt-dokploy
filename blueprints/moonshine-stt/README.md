# Moonshine STT

CPU-friendly self-hosted speech-to-text with:

- Moonshine Voice
- a browser UI with upload + microphone recorder
- a model picker
- hidden path routing for Dokploy

## Dokploy

This blueprint is ready for Dokploy template import.

The app is routed under a generated path like:

`/m-<random>`

## Local

To run locally with Docker Compose, use the blueprint compose file as a reference and set `MOONSHINE_PUBLIC_PATH` to the path you want.
