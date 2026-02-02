# Деплой BeStrong API з HTTPS

## 1. Підключення до AKS

```bash
az aks get-credentials --resource-group bestrong-rg --name bestrong-aks-cluster
```

## 2. Встановлення cert-manager

```bash
# Додати Helm repo
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Встановити cert-manager з CRDs
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.14.0 \
  --set installCRDs=true

# Перевірити
kubectl get pods -n cert-manager
```

Очікуваний результат: 3 pods у статусі `Running`

## 3. Створити ClusterIssuer

```bash
kubectl apply -f clusterissuer-selfsigned.yaml
```

Перевірити:

```bash
kubectl get clusterissuer
```

Очікуваний результат: `selfsigned-issuer` зі статусом `True`

## 4. Валідація Helm chart

```bash
# Lint
helm lint ./charts/bestrong-api

# Template (перевірити вивід)
helm template bestrong-api ./charts/bestrong-api
```

Що шукати в аутпуті `helm template`:
- `kind: Ingress` з `ingressClassName: nginx`
- `tls:` секція з `secretName: bestrong-tls` і `hosts: 20-62-153-61.nip.io`
- `cert-manager.io/cluster-issuer: selfsigned-issuer` в annotations
- `host: "20-62-153-61.nip.io"`
- `kind: Deployment` з `replicas: 2`

## 5. Деплой через Helm

```bash
helm upgrade --install bestrong-api ./charts/bestrong-api \
  --namespace bestrong \
  --create-namespace \
  --wait
```

## 6. Валідація (Definition of Done)

### 6.1 Перевірити Ingress

```bash
kubectl get ingress -n bestrong
```

Очікуваний результат:
```
NAME                   CLASS   HOSTS                 ADDRESS         PORTS     AGE
bestrong-api-ingress   nginx   20-62-153-61.nip.io   20.62.153.61    80, 443   XXs
```

### 6.2 Детальна інформація Ingress

```bash
kubectl describe ingress -n bestrong
```

Шукати:
- `cert-manager.io/cluster-issuer: selfsigned-issuer`
- `TLS: bestrong-tls terminates 20-62-153-61.nip.io`

### 6.3 Перевірити Certificate

```bash
kubectl get certificate -n bestrong
```

Очікуваний результат:
```
NAME            READY   SECRET          AGE
bestrong-tls    True    bestrong-tls    XXs
```

`READY` має бути `True`. Якщо `False`, почекайте 30-60 секунд.

### 6.4 Перевірити TLS Secret

```bash
kubectl get secret -n bestrong | grep bestrong-tls
```

Очікуваний результат:
```
bestrong-tls   kubernetes.io/tls   3      XXs
```

### 6.5 Тестувати HTTPS

```bash
curl -vk https://20-62-153-61.nip.io/
```

Очікуваний результат:
- `SSL connection using TLS`
- HTTP 200 або відповідь від API
- `-v` покаже TLS handshake
- `-k` пропускає перевірку self-signed сертифіката

### 6.6 Тест у браузері

Відкрити: `https://20-62-153-61.nip.io/`

**Важливо**: Браузер покаже попередження про небезпечний сертифікат (self-signed). Це нормально для демо. Натисніть "Advanced" → "Proceed to site".

## 7. Troubleshooting

### Certificate не стає Ready

```bash
kubectl describe certificate bestrong-tls -n bestrong
kubectl describe certificaterequest -n bestrong
kubectl logs -n cert-manager -l app=cert-manager
```

### Ingress не отримує ADDRESS

```bash
kubectl get svc -n ingress-basic
kubectl describe ingress -n bestrong
```

Перевірити, чи Ingress Controller працює:

```bash
kubectl get pods -n ingress-basic
```
