#!/bin/bash

COMMIT_MSG_FILE=$1
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Allowed prefixes
if ! echo "$COMMIT_MSG" | grep -qE "^(feat|fix|refactor|docs|style|test|chore)(\([^)]+\))?: .+"; then
  echo "❌ Commit message must start with one of: feat, fix, refactor, docs, style, test, chore"
  echo "   Example: feat(login): add Google OAuth support"
  exit 1
fi
