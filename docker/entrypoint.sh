#!/bin/sh
set -e

echo "Generating config.json..."

cat > /usr/share/nginx/html/config.json << EOF
{
  "apiUrl": "${API_URL}",
  "wsUrl": "${WS_URL}",
  "apiKey": "${API_KEY}"
}
EOF

echo "config.json generated successfully"
echo "Starting nginx..."

exec "$@"
