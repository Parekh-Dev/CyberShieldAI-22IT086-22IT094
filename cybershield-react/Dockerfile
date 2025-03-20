FROM node:16 AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built app from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 80

RUN sed -i 's/error_log  \/var\/log\/nginx\/error.log warn;/error_log  \/var\/log\/nginx\/error.log debug;/' /etc/nginx/nginx.conf

CMD ["nginx", "-g", "daemon off; error_log /dev/stderr debug;"]