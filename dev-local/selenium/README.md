# Selenium Tests

This document describes the selenium test harness for Blue Button

---

## Overview

- Selenium tests are run inside a Docker image (`selenium-local:latest`) defined in `dev-local/selenium/Dockerfile.selenium`.
- The compose file `dev-local/selenium/docker-compose-selenium.yaml` starts two services:
  - `selenium-tests` — Django app / Selenium instance / do-it-all
  - `chrome` — a standalone Chrome instance for hitting local and remote
- Tests are invoked via the helper Makefile in `dev-local` (they should always be run from dev-local, the Makefile in `dev-local/selenium` is only a passthrough because of relative path nonsense)

---

## .env.selenium

`dev-local/selenium/.env.selenium` is a small env-file used by the `selenium-tests` service. It gets the envvars from whatever script is starting the container, so set them accordingly!

Vars specific to Selenium:

- `USE_MSLSX` — whether to point at the local MSLS mock or the live SLSx endpoints
- `DEBUG_MODE` — when `true`, `start-selenium.sh` enables the Python debug server (`debugpy`) and waits for an attach on port `6789`
- `TARGET_ENV` — `dev` for local runs, change this

---

## The `dump/` directory

When a Selenium test fails, the project captures a screenshot, an HTML dump, and a stack trace so you can inspect what the browser saw at the moment of failure. This is implemented in the `screenshot_on_exception` decorator.

TODO - improve error logging, capture stdout

---

## Socat and Debugging

If running locally, the selenium container starts a socat proxy that listens on port `8000` inside the selenium container and forwards traffic to `host.docker.internal:8000`:

  `socat TCP-LISTEN:8000,fork,reuseaddr TCP:host.docker.internal:8000 &`

This is done because locally, we are running on `localhost:8000` and our redirects from SLSx are also to `localhost:8000`, so we need to map `localhost:8000` -> `host.docker.internal:8000` so that selenium can be debugged. I tried setting it to network_mode: host, which allows it to see `localhost:8000` as if it were the host, but prevents debugging.

If `DEBUG_MODE` is `true`, the pytest script runs a debugpy and listens on port `6789`, This is reachable in your VSCode instance via `0.0.0.0:6789`

---

## Command Reference

All of these should be run via the Makefile in `dev-local`

- Build Selenium image:

  make build-selenium

- Run Selenium tests locally:

  make run-selenium auth=live debug=false

- Run with debugger attached (waits for debugger connect on 6789):

  make run-selenium auth=live debug=true

---
