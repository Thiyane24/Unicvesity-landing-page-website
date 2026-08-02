# =====================================================================
# Unicvesity Worldwide — Frontend image (static site via nginx)
# =====================================================================
# Serves index.html, admin.html, logo.webp, etc. and reverse-proxies
# /api/* to the backend service so the browser only deals with one origin.
# =====================================================================
FROM nginx:1.27-alpine

# Default points at the compose service name; override with --build-arg.
ARG API_UPSTREAM=api:8000
ENV API_UPSTREAM=${API_UPSTREAM}

# Replace the default nginx config with ours.
COPY nginx.conf /etc/nginx/nginx.conf

# Static site lives in the default html root.
COPY --chown=nginx:nginx ./index.html /usr/share/nginx/html/
COPY --chown=nginx:nginx ./admin.html /usr/share/nginx/html/

# Optional assets (logo, favicon) — Dockerfile continues to build if these
# are missing locally; the <img> tags have an `onerror` fallback to the
# placeholder PNG already shipped at the project root.
COPY --chown=nginx:nginx ./Screenshot_2026-08-02_175820-removebg-preview.png \
     /usr/share/nginx/html/ 2>/dev/null || true
COPY --chown=nginx:nginx ./logo.webp ./favicon.webp \
     /usr/share/nginx/html/ 2>/dev/null || true

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
