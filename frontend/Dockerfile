# ============================================================
# Ain't Cappin — Frontend Dockerfile
# React 19 + Vite + Tailwind CSS v4 → Static Build
#
# NOTE: Cloudflare Pages deploys the static dist/ output directly.
# This Dockerfile is used for:
#   1. Building the production static bundle locally / in CI
#   2. Running a lightweight preview server for integration testing
#      before deploying to Cloudflare Pages
# ============================================================

# --- Stage 1: Builder ---
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package manifests first (layer cache optimisation)
COPY package.json package-lock.json ./

# Install ALL dependencies (dev included — needed for tsc + vite build)
RUN npm ci

# Copy the full source
COPY . .

# ---- Build-time Environment Variables ----
# VITE_ prefixed variables are inlined at build time by Vite.
# Override at build time with:  --build-arg VITE_API_BASE_URL=https://your-backend.com
#
# For Cloudflare Pages: set these as "Environment variables" in the
# Pages project settings under Settings → Environment variables (Production).
ARG VITE_API_BASE_URL=https://your-backend-api.com
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Run TypeScript check + Vite production build
RUN npm run build


# --- Stage 2: Preview / Serve ---
# A minimal nginx image to serve the static build for local testing.
# In production, Cloudflare Pages serves the dist/ directory directly —
# you do NOT need this stage on CF Pages itself.
FROM nginx:1.27-alpine AS preview

# Remove default nginx content
RUN rm -rf /usr/share/nginx/html/*

# Copy built static assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx config: serve SPA with HTML5 history fallback
RUN printf 'server {\n\
    listen 80;\n\
    server_name _;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
\n\
    # Gzip compression\n\
    gzip on;\n\
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml image/svg+xml;\n\
\n\
    # Cache static assets aggressively\n\
    location ~* \\.(js|css|png|svg|ico|woff2?)$ {\n\
        expires 1y;\n\
        add_header Cache-Control "public, immutable";\n\
    }\n\
\n\
    # SPA fallback: all unknown paths → index.html\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
