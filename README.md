- `NOTION_API_KEY` – token de acesso à API do Notion.
- `NOTION_DATABASE_ID` – ID do banco de dados onde os leads serão armazenados.
- `ZAPI_INSTANCE_ID` – ID da instância para envio de mensagens pelo Z-API (opcional se `ZAPI_URL` for usado).
- `ZAPI_TOKEN` – token da instância no Z-API (opcional se `ZAPI_URL` for usado).
- `ZAPI_SECURITY_TOKEN` – token de segurança usado no cabeçalho **Client-Token** (opcional).
- `ZAPI_URL` – endpoint completo para envio de mensagens pelo Z-API (use esta variável se preferir configurar a URL diretamente).
- `ALERT_PHONE` – número que receberá alertas via WhatsApp quando o lead for classificado como **Alto**.
- `OPENAI_API_KEY` – chave da OpenAI para classificar leads e gerar mensagens (opcional).

Além dos campos básicos (`nome`, `email` e `whatsapp`), o webhook pode receber a `idade` do lead. Esse valor será registrado no Notion e usado para personalizar mensagens enviadas a leads **Alto**.

Se as credenciais do Z-API estiverem configuradas (via `ZAPI_URL` ou pelo trio `ZAPI_INSTANCE_ID` + `ZAPI_TOKEN` + `ZAPI_SECURITY_TOKEN`) **e** o lead for classificado como **Alto**, uma mensagem será enviada ao número definido em `ALERT_PHONE`.  
Quando `OPENAI_API_KEY` estiver presente, o texto da mensagem será gerado pelo ChatGPT explicando por que o contato tem alta probabilidade de fechar negócio.

Se `OPENAI_API_KEY` não estiver configurada, a classificação de leads será feita apenas por regras de palavras-chave.
