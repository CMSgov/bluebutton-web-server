#!/bin/sh
# Pre-commit check: block committing Locust token files that contain actual tokens.
# A "token" is any non-blank line that does not start with #.

TOKEN_FILES="apps/tokens_non_v3.txt apps/tokens_v3.txt"
FAIL=0

for f in $TOKEN_FILES; do
  if git diff --cached --name-only | grep -q "^$f$"; then
    if grep -qE '^[^#[:space:]]' "$f"; then
      echo "ERROR: $f contains tokens. Remove them before committing."
      FAIL=1
    fi
  fi
done

exit $FAIL
