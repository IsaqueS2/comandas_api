# 🚀 Comandas API - Guia de Uso

## 📊 Status de Segurança (Docker Scout)

✅ **Vulnerabilidades reduzidas de 23 para 16**

| Severidade | Antes | Depois | Redução |
|-----------|-------|--------|---------|
| CRITICAL | 0 | 0 | - |
| HIGH | 4 | 3 | ✓ -1 |
| MEDIUM | 15 | 11 | ✓ -4 |
| LOW | 4 | 2 | ✓ -2 |
| **TOTAL** | **23** | **16** | **✓ -7** |

### Pacotes Atualizados
- ✅ `cryptography`: 46.0.5 → ≥46.0.7
- ✅ `ecdsa`: 0.19.1 → ≥0.19.2
- ✅ `python-multipart`: 0.0.22 → ≥0.0.27 (removeu 1 HIGH CVE)
- ✅ `pytest`: 9.0.2 → ≥9.0.3
- ✅ `Pygments`: 2.19.2 → ≥2.20.0

---

## 🎯 Como Usar

### Opção 1: Script PowerShell Completo (Recomendado)

```powershell
cd "c:\Users\isaque.santos\Documents\Desenvolvimento Web\Comandas_api\comandas_api"
powershell -ExecutionPolicy Bypass -File ".\run-api.ps1" all
```

**Ações disponíveis:**
- `build` - Constrói a imagem Docker
- `scan` - Verifica vulnerabilidades
- `run-local` - Executa API localmente com Uvicorn
- `run-docker` - Executa API em container Docker
- `all` - Executa tudo + menu de seleção

### Opção 2: Executável Rápido

Duplo-clique em `start-api.bat` para iniciar tudo automaticamente.

### Opção 3: Comandos Individuais

```powershell
# Build
docker build -t comandas_api:latest .

# Scan de Segurança
docker scout cves comandas_api:latest

# Executar Localmente (HTTPS)
cd src
..\venv\Scripts\python.exe -m uvicorn main:app ^
  --host 0.0.0.0 ^
  --port 4443 ^
  --ssl-certfile "..\cert\cert.pem" ^
  --ssl-keyfile "..\cert\ecc-key.pem" ^
  --reload

# Executar em Docker
docker run --rm -p 4443:4443 -v "<cert_dir>:/cert" comandas_api:latest
```

---

## 🌐 Acessar a API

### Local
- **Swagger UI**: https://localhost:4443/docs
- **ReDoc**: https://localhost:4443/redoc
- **API**: https://localhost:4443/

### Rede (IP: 172.25.40.28)
- **Swagger UI**: https://172.25.40.28:4443/docs
- **API**: https://172.25.40.28:4443/

⚠️ **Nota**: Como usa certificado auto-assinado, aceite o aviso de segurança no navegador.

---

## 📋 Requisitos

- **Docker Desktop** ≥ 4.69.0
- **Python** 3.14+ (com venv ativado)
- **Certificados SSL**: `cert/cert.pem` e `cert/ecc-key.pem`

---

## 🔒 Segurança

### Vulnerabilidades Conhecidas Restantes

**HIGH (3):**
- CVE-2026-3805 (curl) - Sem correção disponível
- CVE-2024-23342 (ecdsa) - Sem correção disponível
- CVE-2026-27135 (nghttp2) - Atualizar para 1.68.1+

**MEDIUM (11):** Principalmente em curl e Alpine Linux

**LOW (2):** Pygments, xz

---

## 📝 Logs

Logs da API: `./logs/`
Relatório Docker Scout: Gerado no terminal

---

## 🛠️ Troubleshooting

### Porta 4443 em uso
```powershell
netstat -ano | findstr :4443
taskkill /PID <PID> /F
```

### Docker não inicia
```powershell
docker system prune -a
docker build --no-cache -t comandas_api:latest .
```

### SSL Certificate Error
```powershell
# Regenerar certificados
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -keyout ecc-key.pem -out cert.pem -days 365 -nodes
```

---

**Última atualização**: 08/05/2026
**Status**: ✅ Pronto para Produção (com ressalvas de segurança conhecidas)
