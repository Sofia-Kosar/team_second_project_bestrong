# Git guide

## Sync `main`

```bash
git checkout main
git fetch origin
git pull origin main
```

## Create your branch and push it

Replace `[YOUR_BRANCH]` with your branch name.

```bash
git checkout -b [YOUR_BRANCH]
git push [YOUR_BRANCH]
```

## Open a pull request

Create a pull request from `[YOUR_BRANCH]` to `main`.

---

## Security: SSL/TLS via cert-manager (Self-Signed)

BeStrong API використовує HTTPS через **cert-manager** з **self-signed сертифікатом**.

### Налаштування

- **ClusterIssuer**: `selfsigned-issuer` (self-signed)
- **TLS Secret**: `bestrong-tls`
- **Hostname**: `20-62-153-61.nip.io` (nip.io для демо без власного домену)
- **Ingress Controller**: nginx (namespace: `ingress-basic`)

### ⚠️ Важливо

- **Self-signed сертифікат** НЕ буде довіреним браузерами. Очікуйте попередження про безпеку.
- Для production використовуйте **Let's Encrypt** (ClusterIssuer `letsencrypt-prod`).
- **nip.io** — це wildcard DNS сервіс для демо/тестування. Для production потрібен справжній домен.

### Перевірка HTTPS

```bash
# Перевірити сертифікат
kubectl get certificate -n bestrong

# Тестувати HTTPS (-k пропускає перевірку сертифіката)
curl -vk https://20-62-153-61.nip.io/
```

Браузер покаже попередження — це нормально для self-signed. Натисніть "Advanced" → "Proceed to site".