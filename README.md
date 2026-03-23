# WAHA ↔ Chatwoot — Painel de Integração

## Como usar

### Opção 1 — Com Python (recomendado)

1. Instale o Python: https://python.org/downloads/ (marque "Add to PATH" na instalação)
2. Clique duas vezes em **`iniciar.bat`**
3. O navegador abrirá automaticamente em http://localhost:5000

### Opção 2 — Sem Python (modo limitado)

Abra o arquivo `dashboard.html` no Chrome com CORS desabilitado:

**Criar atalho no Windows:**
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --disable-web-security --user-data-dir="C:\ChromeNoSec" file:///C:/Users/Leonardo/.gemini/antigravity/scratch/dashboard.html
```

> ⚠️ Use esta opção SOMENTE para este painel — nunca navegue em outros sites com o Chrome com CORS desabilitado.

---

## Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| 📋 Listar sessões | Ver todas as 149+ sessões WAHA com status |
| 🔗 Integrar sessão | Conectar uma sessão WAHA a uma inbox Chatwoot |
| ✏️ Trocar inbox | Alterar a inbox Chatwoot de uma sessão existente |
| ➕ Nova sessão | Criar sessão WAHA + inbox Chatwoot automaticamente |
| ⚡ Integrar todas | Integrar em massa todas as sessões ativas pendentes |
| 🔍 Filtrar | Filtrar por: Todas / Ativas / Falha / Integradas / Pendentes |

## Configuração (.env)

O sistema utiliza variáveis de ambiente para manter as chaves de API seguras. Antes de rodar a aplicação:
1. Renomeie ou copie o arquivo `.env.example` para `.env`.
2. Edite o arquivo `.env` com as suas credenciais reais do WAHA e do Chatwoot.
3. Inicie o servidor.
