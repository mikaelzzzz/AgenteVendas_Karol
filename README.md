# AgenteVendas_Karol

Esta API recebe dados de um agente de vendas, registra as informações no Notion e classifica o nível de qualificação do lead.

## Variáveis de ambiente

- `NOTION_API_KEY` – token de acesso à API do Notion.
- `NOTION_DATABASE_ID` – ID do banco de dados onde os leads serão armazenados.
- `ZAPI_INSTANCE_ID` – ID da instância para envio de mensagens pelo Z-API.
- `ZAPI_TOKEN` – token da instância no Z-API.
- `ZAPI_SECURITY_TOKEN` – token de segurança da conta usado no cabeçalho `Client-Token`.

Se todas as variáveis do Z-API estiverem configuradas e o lead for classificado como **Alto**, uma mensagem é enviada para `11975578651` com os detalhes do cliente.

## Regras de qualificação

- **Alto**: cliente mencionou "perdeu o emprego", "oportunidade de emprego" ou "viagem" em sua motivação. Indicações que mencionam perda de emprego também se enquadram aqui.
- **Médio**: deseja apenas aprimorar o inglês com objetivo de manter o idioma.
- **Baixo**: quer apenas aprimorar sem objetivo claro.
