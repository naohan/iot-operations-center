# Build Angular
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/angular-app/package*.json ./
RUN npm ci
COPY frontend/angular-app/ ./
ARG NG_CONFIGURATION=production
RUN npm run build -- --configuration=${NG_CONFIGURATION}

# Serve with Nginx (+ reverse proxy a FastAPI)
FROM nginx:1.27-alpine
COPY --from=build /app/dist/angular-app/browser /usr/share/nginx/html
COPY infrastructure/nginx/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
