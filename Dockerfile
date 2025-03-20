FROM ghcr.io/astral-sh/uv:python3.13-alpine
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/app

RUN addgroup --system app && adduser --system app --ingroup app
EXPOSE 8888

RUN mkdir -p $HOME && chown app:app $HOME
WORKDIR $HOME
USER app
COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock
RUN uv sync --frozen

COPY --chown=app:app . .

RUN uv run manage.py collectstatic --noinput
ENTRYPOINT ["/home/app/docker/entrypoint.sh"]
