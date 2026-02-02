#!/bin/bash
# BeStrong API - HTTPS Deployment Commands

# 1. Підключитися до AKS
az aks get-credentials --resource-group bestrong-rg --name bestrong-aks-cluster

# 2. Встановити cert-manager
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.14.0 \
  --set installCRDs=true

# 3. Перевірити cert-manager
kubectl get pods -n cert-manager

# 4. Створити ClusterIssuer
kubectl apply -f clusterissuer-selfsigned.yaml
kubectl get clusterissuer

# 5. Lint & template Helm chart
helm lint ./charts/bestrong-api
helm template bestrong-api ./charts/bestrong-api | grep -E "kind:|ingressClassName:|tls:|cert-manager|host:"

# 6. Деплой
helm upgrade --install bestrong-api ./charts/bestrong-api \
  --namespace bestrong \
  --create-namespace \
  --wait

# 7. Валідація
kubectl get ingress -n bestrong
kubectl get certificate -n bestrong
kubectl get secret -n bestrong | grep bestrong-tls
kubectl describe ingress -n bestrong

# 8. Тестувати HTTPS
curl -vk https://20-62-153-61.nip.io/
