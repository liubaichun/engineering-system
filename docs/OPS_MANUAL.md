# Engineering System Operations Manual

## 运维手册 v1.0
**最后更新:** 2026-03-29
**负责人:** DevOps

---

## 1. 安全配置 (Security Configuration)

### 1.1 SSL/HTTPS 配置

#### Nginx SSL 配置
- **配置文件:** `/etc/nginx/sites-enabled/engineering`
- **SSL 证书:** `/var/www/engineering_system/ssl/engineering.crt`
- **SSL 私钥:** `/var/www/engineering_system/ssl/engineering.key`
- **SSL 协议:** TLSv1.2, TLSv1.3

#### HSTS (HTTP Strict Transport Security)
| 配置项 | 值 | 说明 |
|--------|-----|------|
| `max-age` | 31536000 | 有效期1年 |
| `includeSubDomains` | true | 包含子域名 |
| `preload` | true | 允许加入HSTS预加载列表 |

#### 安全响应头
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

### 1.2 Django 安全设置

在 `settings.py` 中配置:

```python
# ===================== Security Settings =====================
# Force HTTPS/SSL
SECURE_SSL_REDIRECT = True              # Redirect all HTTP to HTTPS
SECURE_HSTS_SECONDS = 31536000          # HSTS: 1 year (31536000 seconds)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True   # Include subdomains in HSTS
SECURE_HSTS_PRELOAD = True              # Allow HSTS preload list inclusion

# Additional Security
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

---

## 2. 限流配置 (Rate Limiting)

### 2.1 DRF 默认限流策略

在 `settings.py` 的 `REST_FRAMEWORK` 配置中:

```python
REST_FRAMEWORK = {
    ...
    'DEFAULT_THROTTLE_RATES': {
        'login': '5/minute',      # 登录尝试: 每分钟5次
        'register': '3/hour',     # 注册: 每小时3次
        'user': '100/minute',     # 通用API: 每分钟100次
    },
}
```

### 2.2 限流等级说明

| 限流类型 | 速率 | 适用场景 |
|---------|------|----------|
| `login` | 5/minute | 登录接口，防止暴力破解 |
| `register` | 3/hour | 注册接口，防止批量注册 |
| `user` | 100/minute | 通用接口，普通用户限制 |

### 2.3 在 View 中使用限流

```python
from rest_framework.throttling import ThrottleByUserRateThrottle

class LoginThrottle(ThrottleByUserRateThrottle):
    rate = '5/minute'

class RegisterThrottle(ThrottleByUserRateThrottle):
    rate = '3/hour'

class GeneralThrottle(ThrottleByUserRateThrottle):
    rate = '100/minute'
```

---

## 3. Nginx 配置变更

### 3.1 HTTP 强制跳转 HTTPS
```nginx
server {
    listen 80;
    server_name 43.156.139.37;
    return 301 https://$server_name$request_uri;
}
```

### 3.2 HTTPS Server 配置
```nginx
server {
    listen 443 ssl;
    server_name 43.156.139.37;

    ssl_certificate /var/www/engineering_system/ssl/engineering.crt;
    ssl_certificate_key /var/www/engineering_system/ssl/engineering.key;
    
    # HSTS Header (由 upstream Django 提供或直接在 nginx 设置)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
}
```

---

## 4. 配置验证

### 4.1 验证 SSL 配置
```bash
# 测试 nginx 配置语法
nginx -t

# 检查 SSL 证书
openssl x509 -in /var/www/engineering_system/ssl/engineering.crt -text -noout

# 测试 HTTPS 连接
curl -v https://43.156.139.37/
```

### 4.2 验证 HSTS 配置
```bash
# 检查 HSTS 响应头
curl -I https://43.156.139.37/
```

### 4.3 重载 Nginx 配置
```bash
sudo nginx -s reload
```

### 4.4 重启 Django 服务
```bash
# 使用 gunicorn/systemd 重启
sudo systemctl restart engineering
# 或
sudo systemctl restart gunicorn
```

---

## 5. 相关文件路径

| 文件 | 路径 | 说明 |
|------|------|------|
| Nginx 配置 | `/etc/nginx/sites-enabled/engineering` | 主配置 |
| SSL 证书 | `/var/www/engineering_system/ssl/engineering.crt` | X.509 证书 |
| SSL 私钥 | `/var/www/engineering_system/ssl/engineering.key` | 私钥文件 |
| Django 设置 | `/var/www/engineering_system/engineering_system/settings.py` | 项目设置 |
| Nginx 日志 | `/var/www/engineering_system/logs/nginx_access.log` | 访问日志 |
| Nginx 错误日志 | `/var/www/engineering_system/logs/nginx_error.log` | 错误日志 |

---

## 6. 紧急情况处理

### 6.1 SSL 证书过期
1. 重新生成自签名证书或使用 Let's Encrypt
2. 更新 `/etc/nginx/sites-enabled/engineering` 中的证书路径
3. 执行 `nginx -s reload`

### 6.2 HTTPS 无法访问
1. 检查 nginx 是否正常运行: `systemctl status nginx`
2. 检查 SSL 证书是否有效: `openssl x509 -checkend 0 -in engineering.crt`
3. 验证 443 端口是否监听: `netstat -tlnp | grep 443`

### 6.3 限流误伤用户
- 临时调整 `settings.py` 中的速率限制
- 使用 Django admin 查看 throttle 日志
- 必要时临时禁用限流: 注释掉 `DEFAULT_THROTTLE_RATES`

---

**文档版本:** v1.0
**创建日期:** 2026-03-29
**下次审查:** 2026-06-29
