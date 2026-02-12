# 🔧 ВИРІШЕННЯ ПРОБЛЕМ З ДОСТУПОМ ДО KUBECOST

**Проблема:** Не можу зайти на KubeCost  
**URL:** https://kubecost.bestrongteam2.duckdns.org  
**Дата:** 12 лютого 2026

---

## ✅ ЩО ПРАЦЮЄ

### 1. Pods (всі працюють):
```bash
$ kubectl get pods -n kubecost

NAME                                          READY   STATUS    RESTARTS   AGE
kubecost-cost-analyzer-5dd588d476-zxdhm       4/4     Running   0          12h
kubecost-forecasting-55b7f568d6-mbhfw         1/1     Running   0          12h
kubecost-grafana-cdf4bcb74-rl7z7              2/2     Running   0          12h
kubecost-prometheus-server-7798b98874-w4sm4   1/1     Running   0          12h
```
✅ Всі pods Running, no restarts

### 2. Service:
```bash
$ kubectl get svc -n kubecost kubecost-cost-analyzer

NAME                     TYPE        CLUSTER-IP    PORT(S)
kubecost-cost-analyzer   ClusterIP   10.0.180.19   9003/TCP,9090/TCP
```
✅ Service існує

### 3. Ingress:
```bash
$ kubectl get ingress -n kubecost

NAME               CLASS     HOSTS                                ADDRESS        PORTS
kubecost-ingress   traefik   kubecost.bestrongteam2.duckdns.org   20.87.244.28   80, 443
```
✅ Ingress створено  
✅ External IP: 20.87.244.28

### 4. DNS:
```bash
$ nslookup kubecost.bestrongteam2.duckdns.org

Name:    kubecost.bestrongteam2.duckdns.org
Address: 20.87.244.28
```
✅ DNS резолвиться правильно

### 5. Certificate:
```bash
$ kubectl get certificate -n kubecost kubecost-bestrong-cert

NAME                     READY   SECRET
kubecost-bestrong-cert   True    kubecost-tls-duckdns
```
✅ Certificate valid (до May 13, 2026)

### 6. Basic Auth:
```bash
$ kubectl get secret -n kubecost kubecost-basic-auth
$ kubectl get middleware -n kubecost basic-auth
```
✅ Secret існує  
✅ Middleware налаштований

### 7. KubeCost UI (локально працює):
```bash
$ kubectl port-forward -n kubecost svc/kubecost-cost-analyzer 9090:9090
$ curl -I http://localhost:9090

HTTP/1.1 200 OK
Server: nginx/1.20.1
```
✅ UI працює!

---

## 🔍 МОЖЛИВІ ПРИЧИНИ ПРОБЛЕМИ

### Причина 1: Middleware not attached properly ⚠️

**Симптом:** Ingress не застосовує basic auth middleware

**Перевірка:**
```bash
kubectl get ingress -n kubecost kubecost-ingress -o yaml | grep middleware
```

**Очікується:**
```yaml
traefik.ingress.kubernetes.io/router.middlewares: kubecost-basic-auth@kubernetescrd
```

**Рішення:** Якщо annotation відсутня, застосуйте ingress знову:
```bash
kubectl apply -f kubecost-ingress.yaml
```

---

### Причина 2: Middleware в неправильному namespace ⚠️

**Симптом:** Traefik annotation format неправильний

**Правильний format:**
```
<namespace>-<middleware-name>@kubernetescrd
```

**Для KubeCost:**
```yaml
annotations:
  traefik.ingress.kubernetes.io/router.middlewares: "kubecost-basic-auth@kubernetescrd"
```

**⚠️ ВАЖЛИВО:** Middleware має бути в тому ж namespace що і Ingress (kubecost)

**Рішення:** Перевірте що middleware є в namespace kubecost:
```bash
kubectl get middleware -n kubecost basic-auth
```

---

### Причина 3: Browser кешує старий response ⚠️

**Симптом:** Browser показує старий error або не просить credentials

**Рішення:**
1. **Відкрийте Incognito/Private window**
2. Або **очистіть cache:**
   - Chrome: `Ctrl+Shift+Delete` → Clear cache
   - Firefox: `Ctrl+Shift+Delete` → Clear cache
3. **Hard refresh:** `Ctrl+F5`

---

### Причина 4: DNS propagation delay ⚠️

**Симптом:** DNS не резолвиться або резолвиться в старий IP

**Перевірка:**
```bash
# Flush DNS cache (Windows)
ipconfig /flushdns

# Test DNS
nslookup kubecost.bestrongteam2.duckdns.org
ping kubecost.bestrongteam2.duckdns.org
```

**Очікується:** 20.87.244.28

---

### Причина 5: Certificate not trusted ⚠️

**Симптом:** Browser показує SSL warning

**Рішення:**
1. Перевірте що certificate valid:
```bash
kubectl get certificate -n kubecost kubecost-bestrong-cert
# READY: True ✅
```

2. Якщо False, дочекайтесь генерації (2-5 хвилин)

3. Або тимчасово використайте HTTP:
```
http://kubecost.bestrongteam2.duckdns.org
```

---

### Причина 6: Firewall блокує доступ 🔥

**Симптом:** Connection timeout або refused

**Перевірка:**
```bash
# Test connection
curl -I https://kubecost.bestrongteam2.duckdns.org
```

**Можливі помилки:**
- `Connection timeout` → Firewall блокує
- `Connection refused` → Service не слухає
- `Could not resolve host` → DNS проблема

**Рішення:** Перевірте Azure Network Security Group (NSG):
```bash
# Check if port 443 is open
az network nsg rule list \
  --resource-group rg-bestrong-demo \
  --nsg-name <nsg-name> \
  --query "[?destinationPortRange=='443']"
```

---

### Причина 7: Traefik не бачить Ingress ⚠️

**Симптом:** Traefik не створює route

**Перевірка:**
```bash
# Check Traefik logs
kubectl logs -n kube-system traefik-5c85cdf89d-2fsl2 --tail=50 | grep kubecost
```

**Рішення:** Restart Traefik:
```bash
kubectl delete pod -n kube-system traefik-5c85cdf89d-2fsl2
# Traefik буде автоматично перестворено
```

---

## 🔧 ШВИДКЕ ВИРІШЕННЯ

### Варіант 1: Port-Forward (100% працює)

```bash
# 1. Port-forward
kubectl port-forward -n kubecost svc/kubecost-cost-analyzer 9090:9090

# 2. Відкрийте браузер
http://localhost:9090

# 3. Логін НЕ потрібен (без basic auth)
```

✅ **Це працює завжди!** Якщо не працює інтернет доступ, використовуйте цей метод.

---

### Варіант 2: Перезастосуйте ресурси

```bash
# 1. Видаліть ingress
kubectl delete ingress -n kubecost kubecost-ingress

# 2. Застосуйте знову
kubectl apply -f kubecost-ingress.yaml

# 3. Дочекайтесь (30 секунд)
kubectl get ingress -n kubecost -w

# 4. Перевірте
curl -u admin:KubeCost123! https://kubecost.bestrongteam2.duckdns.org
```

---

### Варіант 3: Використайте існуючий DuckDNS domain

**Я бачу в логах доступ до:** `kubecost-bestrongteam2.duckdns.org` (з дефісом!)

```bash
# Перевірте чи цей domain працює:
curl -I https://kubecost-bestrongteam2.duckdns.org
```

**Якщо працює**, можливо ingress налаштований на інший domain!

**Перевірка:**
```bash
kubectl get ingress --all-namespaces | grep kubecost
```

---

## 📋 ПОКРОКОВА ДІАГНОСТИКА

### Крок 1: Перевірте основи
```bash
# Pods працюють?
kubectl get pods -n kubecost
# Очікується: All Running ✅

# Ingress існує?
kubectl get ingress -n kubecost
# Очікується: ADDRESS 20.87.244.28 ✅

# DNS працює?
nslookup kubecost.bestrongteam2.duckdns.org
# Очікується: 20.87.244.28 ✅
```

### Крок 2: Test з curl
```bash
# Test without auth (має бути 401)
curl -I https://kubecost.bestrongteam2.duckdns.org
# Очікується: HTTP/2 401 Unauthorized

# Test with auth (має бути 200)
curl -I -u admin:KubeCost123! https://kubecost.bestrongteam2.duckdns.org
# Очікується: HTTP/2 200 OK
```

### Крок 3: Test з browser
```bash
# 1. Відкрийте Incognito window
# 2. Перейдіть: https://kubecost.bestrongteam2.duckdns.org
# 3. Має з'явитися popup: "Authentication Required"
# 4. Введіть: admin / KubeCost123!
# 5. Має відкритися KubeCost UI
```

### Крок 4: Якщо все ще не працює
```bash
# 1. Port-forward
kubectl port-forward -n kubecost svc/kubecost-cost-analyzer 9090:9090 &

# 2. Test locally
curl -I http://localhost:9090
# Має бути: HTTP/1.1 200 OK

# 3. Відкрийте в браузері
http://localhost:9090
```

**Якщо localhost працює → проблема з Ingress/DNS/Certificate**  
**Якщо localhost НЕ працює → проблема з KubeCost pod**

---

## 🎯 НАЙПОШИРЕНІШІ РІШЕННЯ

### Рішення A: Очистити cache та спробувати знову
```bash
# 1. Flush DNS (Windows)
ipconfig /flushdns

# 2. Відкрийте Incognito window
# 3. Перейдіть на URL
https://kubecost.bestrongteam2.duckdns.org

# 4. Введіть credentials
Username: admin
Password: KubeCost123!
```

### Рішення B: Використати port-forward
```bash
kubectl port-forward -n kubecost svc/kubecost-cost-analyzer 9090:9090
# Open: http://localhost:9090
```

### Рішення C: Restart Traefik
```bash
kubectl delete pod -n kube-system traefik-5c85cdf89d-2fsl2
# Wait 30 seconds
kubectl get pods -n kube-system | grep traefik
# Try again: https://kubecost.bestrongteam2.duckdns.org
```

### Рішення D: Recreate Ingress
```bash
kubectl delete ingress -n kubecost kubecost-ingress
kubectl apply -f kubecost-ingress.yaml
# Wait 30 seconds
# Try again
```

---

## 📞 ЯКЩО НІЧОГО НЕ ДОПОМОГЛО

### Зберіть діагностичну інформацію:

```bash
# 1. Pods status
kubectl get pods -n kubecost -o wide > kubecost-pods.txt

# 2. Ingress details
kubectl describe ingress -n kubecost kubecost-ingress > kubecost-ingress.txt

# 3. Service details
kubectl describe svc -n kubecost kubecost-cost-analyzer > kubecost-svc.txt

# 4. Middleware details
kubectl describe middleware -n kubecost basic-auth > kubecost-middleware.txt

# 5. Certificate details
kubectl describe certificate -n kubecost > kubecost-certs.txt

# 6. Traefik logs
kubectl logs -n kube-system traefik-5c85cdf89d-2fsl2 --tail=100 > traefik-logs.txt

# 7. KubeCost logs
kubectl logs -n kubecost deployment/kubecost-cost-analyzer --all-containers --tail=100 > kubecost-logs.txt
```

---

## ✅ УСПІШНИЙ ДОСТУП

**Якщо все працює, ви побачите:**

1. **Browser popup:** "Authentication Required"
2. **Після входу:** KubeCost Dashboard
3. **URL bar:** 🔒 Secure | https://kubecost.bestrongteam2.duckdns.org

**Dashboard показує:**
- Cluster Cost Overview
- Cost Allocation
- Savings Recommendations
- Daily/Monthly Trends

---

## 🎉 ВИСНОВОК

**Найпростіший спосіб перевірити що KubeCost працює:**

```bash
kubectl port-forward -n kubecost svc/kubecost-cost-analyzer 9090:9090
```

Потім відкрийте: http://localhost:9090

**Якщо це працює** → проблема з Ingress/DNS/Certificate  
**Якщо це НЕ працює** → проблема з KubeCost самим собою

---

**Created:** 12 лютого 2026  
**Last Updated:** 12 лютого 2026, 16:00
