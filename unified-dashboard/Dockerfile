# CBSC Unified Dashboard Dockerfile (Vite + React SPA)
# Multi-stage build: build static assets with Vite, serve with nginx

# ---- Build stage ----
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files and install deps (npm — matches package-lock.json)
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# ---- Production stage ----
FROM nginx:alpine AS runner

# Copy built static assets to nginx html dir
COPY --from=builder /app/dist /usr/share/nginx/html

# Custom nginx config for SPA routing (fallback to index.html)
RUN printf 'server {\n\
    listen 3000;\n\
    server_name _;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q --spider http://localhost:3000/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
