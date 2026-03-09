# ---------- Stage 1: build ----------
FROM node:20-alpine AS builder

ARG APP_VERSION=0.1.0
ENV APP_VERSION=${APP_VERSION}

WORKDIR /build

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# ---------- Stage 2: runtime ----------
FROM nginx:alpine

RUN addgroup -g 1000 -S appuser && \
    adduser -u 1000 -S appuser -G appuser && \
    chown -R appuser:appuser /var/cache/nginx /var/log/nginx && \
    touch /var/run/nginx.pid && chown appuser:appuser /var/run/nginx.pid

COPY --from=builder /build/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

USER appuser

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
