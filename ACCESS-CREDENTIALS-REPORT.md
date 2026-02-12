# 🔐 ЗВІТ: Доступи та Credentials

**Проект:** BeStrong Monitoring  
**Дата:** 12 лютого 2026  
**Team:** Team 2

---

## 🌐 ВСІ URLs

### 1. Grafana Dashboard
- **URL:** https://grafana.bestrongteam2.duckdns.org
- **Status:** ✅ Working
- **SSL:** ✅ Let's Encrypt (Valid until 2026-05-12)
- **Auth:** Username/Password

**Credentials:**
```
Username: admin
Password: Admin123!
```

**⚠️ РЕКОМЕНДАЦІЯ:** Змініть пароль після першого входу!

**Що є в Grafana:**
- ✅ Kubernetes Cluster Dashboard (ID: 7249)
- ✅ Kubernetes Pods Dashboard (ID: 6417)
- ✅ Kubernetes Views Global (ID: 15760)
- ✅ Kubernetes Pod Resources (ID: 13770)
- ✅ Prometheus Stats (ID: 3662)

**Дашборди для BeStrong API:**
- Перейдіть в Explore → Select datasource: Prometheus
- Запити:
  ```promql
  # CPU Usage
  rate(container_cpu_usage_seconds_total{pod=~"bestrong-.*"}[5m]) * 100
  
  # Memory Usage
  container_memory_working_set_bytes{pod=~"bestrong-.*"}
  
  # HTTP Requests
  rate(http_requests_total{job="bestrong-prod"}[5m])
  ```

---

### 2. Prometheus Monitoring
- **URL:** https://prometheus.bestrongteam2.duckdns.org
- **Status:** ✅ Working
- **SSL:** ✅ Let's Encrypt
- **Auth:** ❌ No authentication (internal tool)

**Що є в Prometheus:**
- ✅ 4 Alert rules для BeStrong API (CPU, Memory, Pod Down, Restarts)
- ✅ 5 Alert rules для KubeCost (Budget, Rapid Increase, Namespace Cost, etc.)
- ✅ Metrics від 50+ targets (nodes, pods, services)

**Перевірка alerts:**
```
https://prometheus.bestrongteam2.duckdns.org/alerts
```

**Корисні queries:**
```promql
# Check BeStrong pods
up{job="bestrong-prod"}

# Current CPU usage
(rate(container_cpu_usage_seconds_total{namespace="default",pod=~"bestrong-.*"}[5m]) / 
 (container_spec_cpu_quota{namespace="default",pod=~"bestrong-.*"} / 
  container_spec_cpu_period{namespace="default",pod=~"bestrong-.*"})) * 100

# Current Memory usage
(container_memory_working_set_bytes{namespace="default",pod=~"bestrong-.*"} / 
 container_spec_memory_limit_bytes{namespace="default",pod=~"bestrong-.*"}) * 100
```

---

### 3. KubeCost Dashboard
- **URL:** https://kubecost.bestrongteam2.duckdns.org
- **Status:** ⏳ 95% Ready (Certificate generating)
- **SSL:** ⏳ Let's Encrypt (2-5 minutes)
- **Auth:** ✅ Basic Authentication

**Credentials:**
```
Username: admin
Password: KubeCost123!
```

**Очікуваний час доступності:** 5-10 хвилин (certificate generation)

**Що буде в KubeCost:**
- Cost breakdown по namespaces
- Cost breakdown по pods
- Daily/Monthly cost trends
- Azure billing integration
- Cost allocation
- Savings recommendations

**Alerts налаштовані:**
- ✅ Daily budget alert (> $20)
- ✅ Rapid cost increase
- ✅ High namespace cost (> $10)
- ✅ Monthly projection alert (> $600)

---

### 4. BeStrong API
- **URL (Production):** https://bestrongteam2.duckdns.org
- **URL (Canary):** https://bestrongteam2.duckdns.org (weighted 20%)
- **Status:** ✅ Working
- **SSL:** ✅ Let's Encrypt
- **Auth:** ❌ No auth

**Endpoints:**
```
# Health check
GET https://bestrongteam2.duckdns.org/health

# Metrics (Prometheus format)
GET https://bestrongteam2.duckdns.org/metrics

# Swagger UI
GET https://bestrongteam2.duckdns.org/swagger

# API endpoints
GET https://bestrongteam2.duckdns.org/api/...
```

**Deployments:**
- Production: `bestrong-prod` (80% traffic)
- Canary: `bestrong-canary` (20% traffic)

---

### 5. Alertmanager
- **URL:** https://prometheus.bestrongteam2.duckdns.org/alertmanager
- **Status:** ✅ Working (accessible через Prometheus)
- **SSL:** ✅ Let's Encrypt
- **Auth:** ❌ No authentication

**Що є в Alertmanager:**
- ✅ Grouping alerts by alertname, service
- ✅ Routing configuration
- ✅ Silence management (для maintenance)
- ⚠️ Email notifications: REMOVED (за запитом користувача)

**Налаштування notifications (опційно):**
```yaml
# Для Slack:
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: '🚨 {{ .GroupLabels.alertname }}'
```

---

## 🔑 GitHub Secrets

**Що має бути налаштовано в GitHub:**

```
Settings → Secrets and variables → Actions → Repository secrets
```

| Secret Name | Description | Status |
|-------------|-------------|--------|
| `AZURE_CREDENTIALS` | Service Principal JSON | ❓ Перевірити |
| `ARM_CLIENT_ID` | Azure AD App Client ID | ❓ Перевірити |
| `ARM_CLIENT_SECRET` | Azure AD App Client Secret | ❓ Перевірити |
| `ARM_SUBSCRIPTION_ID` | Azure Subscription ID | ❓ Перевірити |
| `ARM_TENANT_ID` | Azure AD Tenant ID | ❓ Перевірити |
| `DB_CONNECTION_STRING` | PostgreSQL connection string | ❓ Перевірити |

**Формат AZURE_CREDENTIALS:**
```json
{
  "clientId": "xxx",
  "clientSecret": "xxx",
  "subscriptionId": "xxx",
  "tenantId": "xxx"
}
```

---

## 🗄️ Kubernetes Credentials

### Отримати kubeconfig:
```bash
az aks get-credentials \
  --resource-group rg-bestrong-demo \
  --name aks-bestrong-demo \
  --overwrite-existing
```

### Перевірити доступ:
```bash
kubectl get nodes
kubectl get pods --all-namespaces
kubectl get svc -n monitoring
```

---

## 🔐 Azure Container Registry (ACR)

**ACR Name:** acrbestrong01  
**URL:** acrbestrong01.azurecr.io

### Login до ACR:
```bash
az acr login --name acrbestrong01
```

### Docker images:
```bash
# List images
az acr repository list --name acrbestrong01

# Show tags
az acr repository show-tags \
  --name acrbestrong01 \
  --repository bestrong-api
```

---

## 📊 Namespaces та Resources

### Namespace: default (BeStrong API)
```bash
kubectl get all -n default | grep bestrong

# Очікується:
# pod/bestrong-prod-xxx        1/1 Running
# pod/bestrong-canary-xxx      1/1 Running
# service/bestrong-prod        ClusterIP
# service/bestrong-canary      ClusterIP
# deployment.apps/bestrong-prod
# deployment.apps/bestrong-canary
```

### Namespace: monitoring (Prometheus, Grafana)
```bash
kubectl get pods -n monitoring

# Очікується:
# prometheus-prometheus-xxx                      2/2 Running
# prometheus-grafana-xxx                         3/3 Running
# alertmanager-prometheus-xxx                    2/2 Running
# prometheus-kube-state-metrics-xxx              1/1 Running
# prometheus-prometheus-node-exporter-xxx        1/1 Running (на кожній ноді)
```

### Namespace: kubecost (KubeCost)
```bash
kubectl get pods -n kubecost

# Очікується:
# kubecost-cost-analyzer-xxx       4/4 Running
# kubecost-forecasting-xxx         1/1 Running
# kubecost-grafana-xxx             2/2 Running
# kubecost-prometheus-server-xxx   1/1 Running
```

### Namespace: cert-manager (Certificates)
```bash
kubectl get pods -n cert-manager

# Очікується:
# cert-manager-xxx                1/1 Running
# cert-manager-cainjector-xxx     1/1 Running
# cert-manager-webhook-xxx        1/1 Running
```

---

## 🧪 ТЕСТУВАННЯ

### 1. Перевірка Grafana
```bash
# Test connection
curl -I https://grafana.bestrongteam2.duckdns.org

# Login API
curl -X POST https://grafana.bestrongteam2.duckdns.org/api/login \
  -H "Content-Type: application/json" \
  -d '{"user":"admin","password":"Admin123!"}'

# Expected: {"message":"Logged in"} + cookie
```

### 2. Перевірка Prometheus
```bash
# Query API
curl -s 'https://prometheus.bestrongteam2.duckdns.org/api/v1/query?query=up' \
  | jq '.status'

# Expected: "success"

# Check alerts
curl -s 'https://prometheus.bestrongteam2.duckdns.org/api/v1/rules' \
  | jq '.data.groups[].rules[] | select(.name | contains("Bestrong"))'
```

### 3. Перевірка KubeCost
```bash
# Test basic auth
curl -u admin:KubeCost123! \
  https://kubecost.bestrongteam2.duckdns.org

# Expected: HTML with KubeCost UI or 302 redirect
```

### 4. Перевірка BeStrong API
```bash
# Health check
curl https://bestrongteam2.duckdns.org/health

# Metrics
curl https://bestrongteam2.duckdns.org/metrics | grep http_requests_total

# Swagger
curl -I https://bestrongteam2.duckdns.org/swagger
```

---

## 🚨 ALERTS TESTING

### Симулювати High CPU:
```bash
# Deploy stress pod
kubectl run stress --image=polinux/stress \
  --labels="app=bestrong-prod" \
  -- stress --cpu 4 --timeout 300s

# Через 2 хвилини:
# 1. Open Prometheus: https://prometheus.bestrongteam2.duckdns.org/alerts
# 2. Alert "BestrongHighCPU" має бути FIRING
# 3. В Alertmanager має з'явитися notification

# Cleanup
kubectl delete pod stress
```

### Симулювати Pod Down:
```bash
# Scale down
kubectl scale deployment bestrong-prod --replicas=0

# Через 1 хвилину:
# Alert "BestrongPodDown" має бути FIRING

# Restore
kubectl scale deployment bestrong-prod --replicas=2
```

---

## 📱 CONTACTS ДЛЯ NOTIFICATIONS

**Email для alerts:**
- kosarsofia0909@gmail.com

**Slack (опційно):**
- Можна додати webhook в Alertmanager

**PagerDuty (опційно):**
- Для critical alerts

---

## 🔄 MAINTENANCE PROCEDURES

### Weekly:
- [ ] Перевірити Grafana dashboards
- [ ] Перевірити Prometheus alerts
- [ ] Перевірити KubeCost reports
- [ ] Review cost trends

### Monthly:
- [ ] Rotate passwords (Grafana, KubeCost)
- [ ] Review and clean old metrics
- [ ] Update dashboards
- [ ] Cost optimization review

### As Needed:
- [ ] Silence alerts during maintenance
- [ ] Update Helm charts
- [ ] Scale resources if needed
- [ ] Backup Grafana dashboards

---

## 📞 SUPPORT

**Якщо щось не працює:**

1. **Перевірте pods:**
   ```bash
   kubectl get pods --all-namespaces | grep -v Running
   ```

2. **Перевірте logs:**
   ```bash
   kubectl logs -n monitoring <pod-name>
   ```

3. **Перевірте certificates:**
   ```bash
   kubectl get certificates --all-namespaces
   ```

4. **Перевірте ingress:**
   ```bash
   kubectl get ingress --all-namespaces
   ```

---

**Всі доступи зібрано!** 🎉  
**Збережіть цей файл в безпечному місці!** 🔐
