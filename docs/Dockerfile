FROM alpine:latest AS builder
RUN apk add --no-cache mdbook
RUN mkdir /docs
WORKDIR /docs
COPY . .
RUN mdbook build

FROM caddy:alpine
COPY Caddyfile /etc/caddy/Caddyfile
RUN mkdir /web
COPY --from=builder /docs/book/ /web
