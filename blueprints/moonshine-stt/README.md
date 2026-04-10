# Moonshine STT

Moonshine Voice on CPU, packaged for Dokploy.

## Features

- browser upload UI
- microphone recorder
- model picker
- hidden path routing
- Docker-friendly build

## Dokploy

This blueprint is ready for Dokploy template import.

The app is routed under a generated path like:

`/m-<random>`

## Local

To run locally with Docker Compose, use the blueprint compose file as a reference and set `MOONSHINE_PUBLIC_PATH` to the path you want.
