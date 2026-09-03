# Deploy do License Server no Render (Free Tier)

> Guia operacional para pôr o license server online e o endpoint
> `POST /api/v1/mobile/entitle` acessível ao app mobile.
> **Pré-requisito:** o código já está pronto (46 testes a passar, ruff limpo) e o
> `render.yaml` + `Dockerfile` existem. Isto requer **a tua conta Render** (execução manual aqui).

---

## 1. Organização (Blueprint vs Manual)

Há duas vias. A **Blueprint** é recomendada porque já temos `render.yaml` versionado:

| Via | Quando | Comando/UI |
|---|---|---|
| **Blueprint (recomendado)** | Primeira vez: liga o repo e aplica `render.yaml` | Dashboard Render → *New +* → *Blueprint* → escolhe o repo |
| Manual | Já tens um serviço e só queres ligar o Dockerfile | *New +* → *Web Service* → runtime Docker |

> Nota: qualquer das vias vai tentar aceder `https://github.com/Noturno22/AirMouse.git`.
> Se o repo for private, liga a conta GitHub ao Render e usa **GitHub deploy**, não a URL.

---

## 2. Variáveis a definir no painel

O `render.yaml` já define `AIRMOUSE_MOBILE_PRODUCT_ID=maouse_mobile_pro`,
`AIRMOUSE_MOBILE_DEV_ALLOW=0`, SMTP desligado, DB em `/data/license.db`.

**Tens de preencher manualmente as `sync: false`** (Render nunca as mostra/tira do git):

### Obrigatórias
| Var | Valor |
|---|---|
| `AIRMOUSE_LS_ADMIN_TOKEN` | Token forte aleatório (ex.: `openssl rand -hex 24`). Usado nos endpoints `/admin/*`. |
| `AIRMOUSE_LS_PRIVATE_KEY` | Conteúdo **PEM** de `license-server/private.pem` (ou o caminho). |
| `AIRMOUSE_LS_PUBLIC_KEY` | Conteúdo **PEM** de `license-server/public.pem`. |

### IAP mobile (endpoint `mobile/entitle`)
| Var | Valor |
|---|---|
| `AIRMOUSE_GOOGLE_PLAY_CREDENTIALS_JSON` | JSON completo da conta de serviço Google (permissão **Android Publisher API**). Sem isto o mobile/entitle só corre em modo dev. |

### Opcionais (papel/postal de chaves MAO-)
- `AIRMOUSE_PADDLE_WEBHOOK_SECRET`, `AIRMOUSE_PADDLE_VENDOR_ID`, `AIRMOUSE_PADDLE_API_KEY`
- `AIRMOUSE_SMTP_HOST/PORT/USER/PASSWORD/FROM` — e `AIRMOUSE_SMTP_ENABLED=1`

> **Cuidado:** `AIRMOUSE_GOOGLE_PLAY_CREDENTIALS_JSON` é um JSON grande (várias linhas). Cola-o
> intacto. Se o Render trunca ou foge aspas, usa Render's *Secret Files* ou*ferra o valor* num
> ficheiro `.json` montado (referência `AIRMOUSE_GOOGLE_PLAY_CREDENTIALS_JSON=/etc/secrets/gp.json`).

---

## 3. Disco persistente

- O `render.yaml` monta **1 GB** em `/data` e aponta `AIRMOUSE_LS_DB=/data/license.db`.
  Não percas isto se trocares de plano (Free tem disco único; ama ele persistente entre redeploys).

---

## 4. Confirmar o deploy

Após o deploy, no painel Render copia a URL (`https://<service>.onrender.com`).

```bash
curl https://<service>.onrender.com/health
# → {"status":"ok", ...}  (200)
```

Teste rápido do endpoint mobile em **modo dev** (só se `AIRMOUSE_MOBILE_DEV_ALLOW=1`):

```bash
curl -s -X POST https://<service>.onrender.com/api/v1/mobile/entitle \
  -H "Content-Type: application/json" \
  -d '{"purchase_token":"test_abc","product_id":"maouse_mobile_pro","package_name":"com.airmouse.mobile","device_id":"dev-1"}'
```

> Na devo a resposta `403 play_nao_configurado` se a conta de serviço ainda não existir — só
> fecha quando `AIRMOUSE_GOOGLE_PLAY_CREDENTIALS_JSON` estiver preenchido e a conta válida.

---

## 5. Guarda a URL no mobile

- `mobile/airmouse-mobile/.env` → `EXPO_PUBLIC_LICENSE_SERVER_URL=https://<service>.onrender.com`
- Sem produto Play real, deixa `AIRMOUSE_MOBILE_DEV_ALLOW=1` **só** no ambiente de teste, e
  desliga (`=0`) antes de subir produção.

---

## 6. Redeploys futuros

- Push no branch ligado → Render faz auto-deploy (build incremental da imagem Docker).
- Alterações de env var → *Manual Deploy > Clear build cache & deploy*.

---

*Operacional · Luar Studio Angola · 2026. Complementa `license-server/README.md`.*
