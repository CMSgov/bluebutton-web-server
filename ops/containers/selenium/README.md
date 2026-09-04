# Selenium Tests

This document describes the selenium test harness for Blue Button

---

## Overview

- Selenium tests are run inside a Docker image (`selenium-local:latest`) defined in `ops/containers/selenium/Dockerfile.selenium`.
- Locally, the compose file `ops/containers/selenium/docker-compose-selenium.yaml` starts two services:
  - `selenium-tests` — Django app / Selenium instance / do-it-all
  - `chrome` — a standalone Chrome instance for hitting local and remote
- In CI (CodeBuild), the compose file `ops/containers/docker-compose-codebuild-selenium.yaml` starts:
  - `selenium-tests` — runs the pytest Selenium suite
  - `chrome` — standalone Chrome
  - `mslsx` — the mock SLS (Medicare login) service used in place of live SLSx
- Tests are invoked via the helper Makefiles in `ops/containers/bb-api` (CI) and `ops/containers/selenium` (local).

---

## .env.selenium

`ops/containers/selenium/.env.selenium` is a small env-file used by the `selenium-tests` service. It gets the envvars from whatever script is starting the container, so set them accordingly!

Vars specific to Selenium:

- `USE_MSLSX` — whether to point at the local MSLS mock or the live SLSx endpoints
- `DEBUG_MODE` — when `true`, `start-selenium.sh` enables the Python debug server (`debugpy`) and waits for an attach on port `7890`
- `TARGET_ENV` — `dev` for local runs, change this

---

## The `dump/` directory

When a Selenium test fails, the project captures a screenshot, an HTML dump, and a stack trace so you can inspect what the browser saw at the moment of failure. This is implemented in the `screenshot_on_exception` decorator.

WARNING - This does not work on WSL, only on Macs.

---

## Socat

If running locally, the selenium container starts a socat proxy that listens on port `8000` inside the selenium container and forwards traffic to `host.docker.internal:8000`:

  `socat TCP-LISTEN:8000,fork,reuseaddr TCP:host.docker.internal:8000 &`

This is done because locally, we are running on `localhost:8000` and our redirects from SLSx are also to `localhost:8000`, so we need to map `localhost:8000` -> `host.docker.internal:8000` so that selenium can be debugged. I tried setting it to network_mode: host, which allows it to see `localhost:8000` as if it were the host, but prevents debugging.

## Testing/Debugging with Selenium

If `DEBUG_MODE` is `true`, the pytest script runs a debugpy and listens on port `7890`, This is reachable in your VSCode instance via `0.0.0.0:7890`. You will need to ensure you have your `launch.json` updated IAW with the README in `ops/containers`.

To debug selenium tests, right now we can only debug them properly using auth=mock. We can use auth=live but we consistently get the zscaler issue locally that results in an internal server error 500. Here are the steps for debugging selenium tests:

```bash
# Ensure you bring up the bb-api stack with auth=mock
make run-local auth=mock
# Build selenium
make build-selenium
# Ensure you bring up the selenium stack with auth=mock and debug=true
make run-selenium-local auth=mock debug=true
```
After running this in the terminal, navigate to the `Run and Debug` extension of VS Code and run the `Selenium Test` play button. You can set breakpoints accordingly in different selenium tests to test functionality and stop at different moments.

Additionally, if you wanted to see the tests live in the selenium container, you can set SELENIUM_GRID to true before running the selenium tests. For example:
```bash
make run-local auth=mock debug=false SELENIUM_GRID=true
```
After starting to run the tests, you can navigate to `localhost:4444` and click on the camera icon that is flashing. You can then enter in `secret` as the password to see the selenium test happening live in a browser! This is useful when you are debugging the steps and need to see what's happening one step at a time.

---

## Command Reference

All of these can be run from root.

- Build Selenium image:

  make build-selenium

- Run Selenium tests locally:

  make run-selenium-local auth=live debug=false

- Run with debugger attached (waits for debugger connect on 7890):

  make run-selenium-local auth=live debug=true

---

## CI / Pull Request Checks

The `selenium-tests` job in `.github/workflows/pull-request-checks.yml` runs the
Selenium suite inside the CodeBuild runner on every pull request against `master`
(and on new commits pushed to a PR branch). It uses the **mock SLS** (`mslsx`)
service rather than the live SLSx endpoints.

All commands are driven through the helper targets in
`ops/containers/bb-api/Makefile`. The job runs them in this order:

1. **Build MSLSX** — `cd ops/containers/mslsx && make build-local`
   Builds the `mslsx:latest` mock Medicare login image.

2. **Build BBAPI** — `cd ops/containers/bb-api && make build-codebuild`
   Builds the `bb-api:codebuild` application image.

3. **Build Selenium** — `cd ops/containers/bb-api && make build-selenium`
   Delegates to `ops/containers/selenium` to build `selenium-local:latest`.

4. **Start Stack** — `cd ops/containers/bb-api && make run-codebuild-mock`
   Brings up the CodeBuild stack with `auth=mock`, so `bb-api` points at the
   `mslsx` endpoints instead of live SLSx.

5. **Execute Selenium Tests** — `cd ops/containers/bb-api && make run-codebuild-selenium`
   Runs the `selenium-tests` service from
   `ops/containers/docker-compose-codebuild-selenium.yaml`, which also starts the
   `mslsx` and `chrome` services.

6. **Teardown Stack** — `cd ops/containers/bb-api && make teardown-codebuild-selenium`
   Tears down both the selenium and codebuild compose stacks (runs with
   `if: always()`).

### Mock SLS networking

In CodeBuild, all compose services use `network_mode: "host"`, so there is no
Docker DNS. Containers reach each other over `localhost`:

- `mslsx` listens on `localhost:8080`
- `bb-api` listens on `localhost:8000`

`configure_slsx` in
`ops/containers/bb-api/scripts/external/prepare-environment-support.bash` uses
`localhost` for the `mslsx` endpoints when `TARGET_ENV=codebuild`, and the Docker
DNS name `mslsx` when running locally.

---

