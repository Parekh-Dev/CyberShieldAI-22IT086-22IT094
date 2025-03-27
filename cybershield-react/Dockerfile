FROM node:16 AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

# Update the path to match your current configuration file
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Copy built app from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Create SSL directory with proper permissions
RUN mkdir -p /etc/nginx/ssl && \
    chmod 600 /etc/nginx/ssl

# Expose both HTTP and HTTPS ports
EXPOSE 80 443

# Enable debug logging
RUN sed -i 's/error_log  \/var\/log\/nginx\/error.log warn;/error_log  \/var\/log\/nginx\/error.log debug;/' /etc/nginx/nginx.conf

CMD ["nginx", "-g", "daemon off; error_log /dev/stderr debug;"]