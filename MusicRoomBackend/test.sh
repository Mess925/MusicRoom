#!/usr/bin/env bash
# Run the backend test suite.
#
# Picks a runner automatically:
#   * host       — if `uv` is installed (fastest; no containers)
#   * docker     — otherwise, through the `api` compose service
#
# Unit tests need nothing running: PostgreSQL and Redis are faked via FastAPI
# dependency overrides. Integration tests (marked `integration`) need the real
# stack and are deselected unless you ask for them.
#
# Usage:
#   ./test.sh                       # unit tests
#   ./test.sh --cov                 # unit tests + coverage report
#   ./test.sh --integration         # only the integration tests (needs the stack)
#   ./test.sh --all                 # unit + integration
#   ./test.sh --docker              # force the container runner
#   ./test.sh --host                # force the host runner (requires uv)
#   ./test.sh -- -k health -vv      # everything after `--` goes to pytest
set -euo pipefail

cd "$(dirname "$0")"

runner=auto
select_args=(-m "not integration")
needs_stack=0
pytest_args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --docker | -d) runner=docker ;;
    --host | -H) runner=host ;;
    --cov | -c)
      pytest_args+=(--cov --cov-report=term-missing)
      ;;
    --integration | -i)
      select_args=(-m integration)
      needs_stack=1
      ;;
    --all | -a)
      select_args=()
      needs_stack=1
      ;;
    -h | --help)
      sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    --)
      shift
      pytest_args+=("$@")
      break
      ;;
    *) pytest_args+=("$1") ;;
  esac
  shift
done

pytest_cmd=(pytest "${select_args[@]}" "${pytest_args[@]}")

if [[ $runner == auto ]]; then
  if command -v uv >/dev/null 2>&1; then
    runner=host
  else
    runner=docker
  fi
fi

if [[ $runner == host ]]; then
  command -v uv >/dev/null 2>&1 || {
    echo "test.sh: uv is not installed — use ./test.sh --docker" >&2
    exit 1
  }
  echo "==> pytest (host, uv)"
  exec uv run "${pytest_cmd[@]}"
fi

command -v docker >/dev/null 2>&1 || {
  echo "test.sh: neither uv nor docker found — install one of them" >&2
  exit 1
}

# Reuse the running container when there is one; otherwise start a throwaway.
if [[ -n "$(docker compose ps --status running -q api 2>/dev/null)" ]]; then
  echo "==> pytest (docker, running api container)"
  exec docker compose exec -T api "${pytest_cmd[@]}"
fi

run_flags=(--rm --build -T)
if [[ $needs_stack -eq 0 ]]; then
  # Unit tests hit no services — skip starting postgres/redis.
  run_flags+=(--no-deps)
fi

echo "==> pytest (docker, throwaway container)"
exec docker compose run "${run_flags[@]}" api "${pytest_cmd[@]}"
