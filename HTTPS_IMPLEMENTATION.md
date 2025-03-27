# HTTPS Implementation with Self-Signed Certificate

## Overview
CyberShield AI implements HTTPS with self-signed certificates to secure communication between client and server.

## Implementation Details
 Access your frontend at http://localhost
### Certificate Location
- Self-signed certificates placed in ssl/ directory (placeholders in repository)
- Private keys excluded from repository for security

### Configuration
Our application serves content over HTTPS using Nginx:

\\\
ginx
server {
    listen 443 ssl;
    server_name localhost;

    # SSL certificate configuration
    ssl_certificate     /etc/nginx/ssl/server.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;
    
    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    
    # Root location
    location / {
        root   /usr/share/nginx/html;
        index  index.html index.htm;
        try_files \ \/ /index.html;
    }
}
\\\

### Certificate Generation
\\\ash
# Generate private key and certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt
\\\

## Security Benefits
1. Encrypted data transmission
2. Protection against man-in-the-middle attacks
3. Data integrity verification
