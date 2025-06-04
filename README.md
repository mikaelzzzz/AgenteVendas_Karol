# AgenteVendas_Karol

Esta API recebe dados de um agente de vendas, registra as informações no Notion e classifica o nível de qualificação do lead.

## Variáveis de ambiente

- `NOTION_API_KEY` – token de acesso à API do Notion.
- `NOTION_DATABASE_ID` – ID do banco de dados onde os leads serão armazenados.
- `ZAPI_URL` – endpoint completo para envio de mensagens pelo Z-API (opcional).

Caso `ZAPI_URL` esteja configurada e o lead seja classificado como **Alto**, uma mensagem é enviada para `5511975578651` informando os detalhes do cliente.

## Regras de qualificação

- **Alto**: cliente mencionou "perdeu o emprego", "oportunidade de emprego" ou "viagem" em sua motivação. Indicações que mencionam perda de emprego também se enquadram aqui.
- **Médio**: deseja apenas aprimorar o inglês com objetivo de manter o idioma.
- **Baixo**: quer apenas aprimorar sem objetivo claro.
