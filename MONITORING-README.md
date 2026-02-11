# 🚀 ШВИДКИЙ СТАРТ - BeStrong API Monitoring

> Повний звіт: [MONITORING-FINAL-REPORT.md](./MONITORING-FINAL-REPORT.md)

---

## 📊 ЩО ВСТАНОВЛЕНО

✅ **Prometheus + Grafana Stack** в AKS кластері  
✅ **Алерти** для CPU > 70% та Memory > 70%  
✅ **Grafana UI** доступна з інтернету через HTTPS  
✅ **Prometheus metrics** інтегровано в .NET API  

---

## 🌐 ШВИДКИЙ ДОСТУП

| Сервіс | URL | Credentials |
|--------|-----|-------------|
| **Grafana** | https://grafana.bestrongteam2.duckdns.org | admin / Admin123! |
| **Prometheus** | https://prometheus.bestrongteam2.duckdns.org | - |
| **BeStrong API** | https://bestrongteam2.duckdns.org | - |
| **Metrics** | https://bestrongteam2.duckdns.org/metrics | - |

---

## ⚡ ШВИДКА ПЕРЕВІРКА

### 1. Перевірка що все працює
```bash
# Pods
kubectl get pods -n monitoring
kubectl get pods -n default

# ServiceMonitors
kubectl get servicemonitors -n monitoring | grep bestrong

# Alerts
kubectl get prometheusrules -n monitoring | grep bestrong
```

### 2. Перевірка метрик
```bash
# Відкрийте Prometheus
https://prometheus.bestrongteam2.duckdns.org

# Перейдіть в Status → Targets
# Знайдіть: bestrong-prod-metrics → має бути UP (зелений)
```

### 3. Перевірка Grafana
```bash
# Відкрийте
https://grafana.bestrongteam2.duckdns.org

# Login: admin / Admin123!
# Перейдіть в Explore
# Data Source: Prometheus
# Query: process_working_set_bytes{job="bestrong-prod"}
# Має показати графік з даними
```

---

## 📊 ПРИКЛАДИ PROMQL ЗАПИТІВ

### Memory Usage
```promql
process_working_set_bytes{job="bestrong-prod"}
```

### CPU Usage
```promql
rate(process_cpu_seconds_total{job="bestrong-prod"}[5m]) * 100
```

### HTTP Requests per second
```promql
rate(http_requests_received_total{job="bestrong-prod"}[5m])
```

### HTTP Error Rate
```promql
sum(rate(http_requests_received_total{job="bestrong-prod",code=~"5.."}[5m])) 
/ 
sum(rate(http_requests_received_total{job="bestrong-prod"}[5m]))
```

---

## 🔥 TROUBLESHOOTING

### Немає даних в Grafana?

1. **Перевірте Prometheus targets:**
   ```
   https://prometheus.bestrongteam2.duckdns.org/targets
   ```
   Знайдіть `bestrong-prod-metrics` → має бути UP ✅

2. **Перевірте Service labels:**
   ```bash
   kubectl get svc -n default bestrong-prod --show-labels
   # Має бути: app=bestrong-prod
   ```

3. **Перевірте metrics endpoint:**
   ```bash
   kubectl port-forward -n default svc/bestrong-prod 8080:80
   curl http://localhost:8080/metrics
   # Має повернути метрики
   ```

### Grafana не відкривається?

1. **Перевірте pod:**
   ```bash
   kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana
   # Має бути Running
   ```

2. **Перевірте certificate:**
   ```bash
   kubectl get certificate -n monitoring grafana-tls
   # READY має бути True
   ```

---

## 📚 ДОКУМЕНТАЦІЯ

| Файл | Опис |
|------|------|
| **MONITORING-FINAL-REPORT.md** | Повний детальний звіт (100+ сторінок) |
| **MONITORING-SETUP.md** | Детальна документація по Prometheus/Grafana |
| **METRICS-SETUP.md** | Інструкції по .NET metrics integration |
| **COMPLETE-MONITORING-GUIDE.md** | Загальний guide з прикладами |

---

## ✅ СТАТУС

**Всі компоненти:** ✅ Running  
**Дані збираються:** ✅ Yes  
**Алерти працюють:** ✅ Yes  
**SSL certificates:** ✅ Valid  
**Production ready:** ✅ 95%

---

## 🎯 НАСТУПНІ КРОКИ

1. ⚠️ **ЗМІНІТЬ** Grafana password (admin / Admin123!)
2. Створіть custom dashboard для вашого API
3. Налаштуйте email/Slack notifications
4. Імпортуйте додаткові .NET дашборди

---

**Готово до використання! 🎉**

Детальна інформація: [MONITORING-FINAL-REPORT.md](./MONITORING-FINAL-REPORT.md)
