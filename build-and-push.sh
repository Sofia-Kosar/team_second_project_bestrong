#!/bin/bash
set -e

echo "🔨 Building BeStrong API..."

# 1. Login to ACR
echo "📦 Login to ACR..."
az acr login --name acrbestrong01

# 2. Build
echo "🏗️  Building Docker image..."
docker build -t bestrong-api:latest .

# 3. Tag
echo "🏷️  Tagging for ACR..."
docker tag bestrong-api:latest acrbestrong01.azurecr.io/bestrong-api:latest

# 4. Push
echo "⬆️  Pushing to ACR..."
docker push acrbestrong01.azurecr.io/bestrong-api:latest

# 5. Verify
echo "✅ Verifying..."
az acr repository show-tags --name acrbestrong01 --repository bestrong-api -o table

echo ""
echo "🎉 Done! Now you can deploy:"
echo "   helm upgrade bestrong-api ./charts/bestrong-api -n bestrong --wait"
