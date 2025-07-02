#!/bin/bash


set -e

echo "🚀 Setting up GitHub Issues Automation for deployment..."

if [ -z "$DEVIN_SERVICE_API_KEY" ] || [ -z "$NEON_CREDS_PGHOST" ] || [ -z "$GITHUB_PEM" ]; then
    echo "❌ Error: Required environment variables not found."
    echo "This script requires access to Devin secrets:"
    echo "  - DEVIN_SERVICE_API_KEY"
    echo "  - NEON_CREDS_* (database credentials)"
    echo "  - GITHUB_PEM (GitHub App private key)"
    echo "  - github_app_install_id"
    exit 1
fi

echo "📝 Configuring backend environment..."
cd backend

cat > .env << EOF
DEVIN_SERVICE_API_KEY=$DEVIN_SERVICE_API_KEY
NEON_DATABASE_URL=postgresql://$NEON_CREDS_PGUSER:$NEON_CREDS_PGPASSWORD@$NEON_CREDS_PGHOST/$NEON_CREDS_PGDATABASE?sslmode=$NEON_CREDS_PGSSLMODE
GITHUB_TOKEN=
GITHUB_APP_ID=1488267
GITHUB_APP_PRIVATE_KEY=$GITHUB_PEM
GITHUB_APP_INSTALLATION_ID=$github_app_install_id
GITHUB_WEBHOOK_SECRET=
EOF

echo "✅ Backend environment configured"

echo "📝 Configuring frontend for deployment..."
cd ../frontend

BACKEND_URL=""
if command -v fly &> /dev/null; then
    BACKEND_URL=$(fly status --app app-xuiczebe 2>/dev/null | grep "Hostname" | awk '{print "https://" $2}' || echo "")
fi

if [ -z "$BACKEND_URL" ]; then
    BACKEND_URL="https://app-xuiczebe.fly.dev"  # Default deployed backend URL
fi

cat > .env << EOF
VITE_API_BASE_URL=$BACKEND_URL
EOF

echo "✅ Frontend configured to use backend: $BACKEND_URL"

echo ""
echo "🎉 Deployment setup complete!"
echo ""
echo "Next steps:"
echo "1. Deploy backend: cd backend && deploy_backend ."
echo "2. Update frontend .env with actual backend URL if different"
echo "3. Build frontend: cd frontend && npm run build"
echo "4. Deploy frontend: deploy_frontend frontend/dist"
echo ""
echo "For local development:"
echo "1. Backend: cd backend && poetry run fastapi dev app/main.py"
echo "2. Frontend: cd frontend && npm run dev"
