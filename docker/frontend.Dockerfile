# ── Dev stage ──────────────────────────────────────────────────────────────────
FROM node:22-alpine AS dev
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
EXPOSE 5173

# ── Build stage ─────────────────────────────────────────────────────────────────
FROM node:22-alpine AS builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Production stage ────────────────────────────────────────────────────────────
FROM nginx:alpine AS production
COPY --from=builder /app/frontend/build /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
