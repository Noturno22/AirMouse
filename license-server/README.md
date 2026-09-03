# Mãouse — License Server

Serviço de licenciamento (FastAPI + SQLite) que serve o desktop (chaves `MAO-`, trial,
ativação por fingerprint, leases JWT ES256) e o **mobile** (validação de compra Google Play
→ lease Pro).

## Variáveis de ambiente

| Var | Obrigatório | Descrição |
|-----|-------------|-----------|
| `AIRMOUSE_DB_PATH` | não | Caminho do SQLite (default `license.db`) |
| `AIRMOUSE_PADDLE_WEBHOOK_SECRET` | se usar Paddle | HMAC dos webhooks Paddle |
| `AIRMOUSE_PADDLE_VENDOR_ID` / `AIRMOUSE_PADDLE_API_KEY` | se usar Paddle | API Paddle (produtos/checkout) |
| `AIRMOUSE_SMTP_*` | se email | Transmissão de chave MAO- por email |
| `AIRMOUSE_GOOGLE_PLAY_CREDENTIALS_JSON` | IAP real | JSON da conta de serviço com permissão **Android Publisher API**. Sem isto, `mobile/entitle` só funciona em modo dev |
| `AIRMOUSE_MOBILE_DEV_ALLOW=1` | **nunca em produção** | Aceita tokens de teste prefixados `test_` |
| `AIRMOUSE_MOBILE_PRODUCT_ID` | não | Product ID do Pro (default `maouse_mobile_pro`) |

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check |
| POST | `/admin/keys` | Emite chaves `MAO-` (admin) |
| POST | `/api/v1/activate` | Ativa por chave + fingerprint |
| POST | `/api/v1/trial/start` | Inicia trial server-authoritative |
| POST | `/api/v1/trial/report` | Report de execução do trial |
| POST | `/api/v1/revalidate` | Revalida lease |
| POST | `/api/v1/revoke` | Revoga chave/lease |
| POST | `/webhooks/paddle` | Webhook de pagamento Paddle (emite MAO- + email) |
| **POST** | **`/api/v1/mobile/entitle`** | **Valida compra Google Play e emite lease `tier=mobile_pro`** |

### POST /api/v1/mobile/entitle

Corpo:

```json
{
  "purchase_token": "<Google Play purchaseToken>",
  "product_id": "maouse_mobile_pro",
  "package_name": "com.airmouse.mobile",
  "device_id": "<uuid persistente do dispositivo>"
}
```

Resposta (200):

```json
{ "tier": "mobile_pro", "lease": "<JWT ES256>", "session_id": "...", "first_time": true }
```

Erros:
- `422` — corpo inválido (`ValueError`).
- `403` — validação Google Play falhou (`PlayValidationError`); mensagens curtas:
  `play_nao_configurado`, `token_invalido_dev`, `token_invalido`, `compra_nao_concluida`,
  `permissao_play`, `play_api_erro`, `credenciais_invalidas`.

Comportamento:
- **Dedup por `purchase_token`** antes de chamar a API Google → sem chamadas duplicadas, reutiliza o lease.
- `key_hash = "MOB:" + hash(purchase_token)` → bucket próprio, imune ao bucket das chaves desktop.
- Em modo dev (`AIRMOUSE_MOBILE_DEV_ALLOW=1`) aceita tokens `test_<qualquer coisa>`.

## Segurança

- Leases JWT assinados **ES256** com keypair real (gerado em `keys.py`).
- Não guarda/compara `purchase_token` com a API Google duas vezes para a mesma compra.
- A conta de serviço Google exige apenas o scope `androidpublisher` (permissão mínima).

## Testes e lint

```bash
.venv\Scripts\python -m pytest license-server/tests -q
ruff check license-server
```
