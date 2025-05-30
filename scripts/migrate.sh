#!/bin/bash
set -e

# Determine the project root directory (one level up from this script)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables from .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
  export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Help message
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
  echo "Usage: scripts/migrate.sh [COMMAND]"
  echo ""
  echo "Commands:"
  echo "  init        Initialize Alembic"
  echo "  migrate     Generate a new migration (alias for 'revision --autogenerate')"
  echo "  upgrade     Apply all migrations"
  echo "  downgrade   Revert last migration"
  echo "  current     Show current revision"
  echo "  history     Show migration history"
  echo "  --help      Show this help message"
  exit 0
fi

# Run Alembic commands in the app container
case "$1" in
  init)
    docker compose run --rm -w /app/app web alembic init -t async migrations
    ;;
  migrate)
    shift
    docker compose run --rm -w /app/app web alembic revision --autogenerate -m "${1:-migration}"
    ;;
  upgrade)
    shift
    docker compose run --rm -w /app/app web alembic upgrade "${1:-head}"
    ;;
  downgrade)
    shift
    docker compose run --rm -w /app/app web alembic downgrade "${1:-head}" 
    ;;
  current)
    docker compose run --rm -w /app/app web alembic current
    ;;
  history)
    docker compose run --rm -w /app/app web alembic history
    ;;
  *)
    echo "Unknown command: $1"
    echo "Run 'scripts/migrate.sh --help' for usage information."
    exit 1
    ;;
esac