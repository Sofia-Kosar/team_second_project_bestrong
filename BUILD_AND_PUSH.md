# Build & Push BeStrong API в ACR

## Передумови

- Docker Desktop запущений
- Azure CLI залогінений (`az login`)
- Dockerfile існує в корені проєкту

## Команди

### 1. Логін в ACR

```bash
az acr login --name acrbestrong01
```

### 2. Build Docker image

```bash
# З кореня проєкту
docker build -t bestrong-api:latest .
```

### 3. Tag для ACR

```bash
docker tag bestrong-api:latest acrbestrong01.azurecr.io/bestrong-api:latest
```

### 4. Push в ACR

```bash
docker push acrbestrong01.azurecr.io/bestrong-api:latest
```

### 5. Перевірити, що image в ACR

```bash
az acr repository list --name acrbestrong01 -o table
az acr repository show-tags --name acrbestrong01 --repository bestrong-api -o table
```

### 6. Оновити Helm chart на BeStrong API

```bash
# В values.yaml змінити назад:
# image:
#   repository: acrbestrong01.azurecr.io/bestrong-api
#   tag: "latest"
#
# service:
#   targetPort: 5000

# Upgrade
helm upgrade bestrong-api ./charts/bestrong-api -n bestrong --wait
```

### 7. Перевірити

```bash
kubectl get pods -n bestrong
curl -vk https://20-62-153-61.nip.io/
```

---

## Альтернатива: CI/CD Pipeline

Замість ручного build можна налаштувати GitHub Actions:

```yaml
# .github/workflows/build-push.yaml
name: Build and Push to ACR

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to ACR
        uses: azure/docker-login@v1
        with:
          login-server: acrbestrong01.azurecr.io
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}
      
      - name: Build and push
        run: |
          docker build -t acrbestrong01.azurecr.io/bestrong-api:${{ github.sha }} .
          docker push acrbestrong01.azurecr.io/bestrong-api:${{ github.sha }}
          docker tag acrbestrong01.azurecr.io/bestrong-api:${{ github.sha }} acrbestrong01.azurecr.io/bestrong-api:latest
          docker push acrbestrong01.azurecr.io/bestrong-api:latest
```
