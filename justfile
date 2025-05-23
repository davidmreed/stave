migrate:
    uv run manage.py makemigrations && uv run manage.py migrate

run:
    uv run manage.py collectstatic --noinput
    uv run manage.py runserver 0.0.0.0:8888

run-prod:
    docker/entrypoint.sh

reset:
    uv run manage.py flush --noinput && uv run manage.py seed


format:
    ruff check --select I --fix
    ruff format
