# AgendaKarol - Sistema de Integração de Agendamentos

Sistema de integração entre Cal.com, Notion, WhatsApp e ChatGPT para gerenciamento automatizado de agendamentos.

## Funcionalidades

- Integração com Cal.com para captura de agendamentos
- Sincronização automática com banco de dados Notion
- Notificações automáticas via WhatsApp (Z-API)
- Análise de leads com ChatGPT
- Sistema de lembretes automáticos
- Link fixo do Zoom para reuniões

## Requisitos

- Python 3.11+
- FastAPI
- Notion API
- Z-API (WhatsApp)
- OpenAI API
- APScheduler

## Variáveis de Ambiente

```env
CAL_SECRET=seu_secret_do_cal
NOTION_TOKEN=seu_token_do_notion
NOTION_DB=seu_database_id
ZAPI_INSTANCE=sua_instancia_zapi
ZAPI_TOKEN=seu_token_zapi
ZAPI_CLIENT_TOKEN=seu_client_token_zapi
OPENAI_API_KEY=sua_chave_api_openai
PORT=8000
```

## Instalação

1. Clone o repositório
```bash
git clone https://github.com/mikaelzzzz/AgendaKarol.git
cd AgendaKarol
```

2. Instale as dependências
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente em um arquivo `.env`

4. Execute o servidor
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Estrutura do Projeto

```
app/
├── __init__.py
├── main.py          # Aplicação FastAPI principal
├── notion.py        # Integração com Notion
├── whatsapp.py      # Integração com WhatsApp (Z-API)
└── chatgpt.py       # Integração com ChatGPT
```

## Endpoints

- `POST /webhook`: Recebe webhooks do Cal.com
  - Processa eventos BOOKING_CREATED, BOOKING_RESCHEDULED e BOOKING_CANCELLED
  - Atualiza Notion
  - Envia notificações WhatsApp
  - Agenda lembretes

## Deploy

O projeto está configurado para deploy no Render.com como um Web Service.

## Licença

Este projeto é privado e de uso exclusivo autorizado. 