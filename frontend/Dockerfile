# Stage 1: Build React/Vite production application
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies using clean install
COPY package.json package-lock.json ./
RUN npm ci

# Copy application source code and compile production assets
COPY . .
RUN npm run build

# Stage 2: Serve production assets with Nginx
FROM nginx:alpine

# Copy custom Nginx configuration with reverse proxy and SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
