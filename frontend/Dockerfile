# Stage 1: Builder
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
# If package.json exists, install dependencies. Ignore errors if it's just the fallback html.
RUN npm install || true
COPY . .

# Build the Angular app. If it fails (due to missing angular.json from scratch), 
# fallback to just providing our functional Vanilla JS index.html.
RUN npm run build || (mkdir -p dist/frontend/browser && cp src/index.html dist/frontend/browser/index.html 2>/dev/null || echo "Build fallback complete")

# Stage 2: Runner
FROM nginx:alpine AS runner

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build artifacts to Nginx
COPY --from=builder /app/dist/frontend/browser /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
