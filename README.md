# Sistema de Integração Cal.com, Notion, ChatGPT e WhatsApp

Este sistema integra várias plataformas para gerenciar agendamentos e comunicações automaticamente:

## Funcionalidades

- **Integração Cal.com**: Recebe webhooks de eventos de agendamento
- **Integração Notion**: Atualiza banco de dados com detalhes dos agendamentos
- **Integração WhatsApp**: Envia notificações via Z-API
- **Integração ChatGPT**: Gera mensagens personalizadas para a equipe de vendas
- **Link Zoom Fixo**: Utiliza um link Zoom predefinido para todas as reuniões
- **Lembretes Automáticos**: Envia lembretes 1 hora antes das reuniões

## Requisitos

- Python 3.11+
- Dependências listadas em `requirements.txt`

## Variáveis de Ambiente

Crie um arquivo `.env` com as seguintes variáveis:

```env
CAL_SECRET=seu_secret_cal
NOTION_TOKEN=seu_token_notion
NOTION_DB=seu_database_id
ZAPI_INSTANCE=seu_instance_id
ZAPI_TOKEN=seu_token
ZAPI_CLIENT_TOKEN=seu_client_token
OPENAI_API_KEY=sua_chave_api
```

## Instalação

1. Clone o repositório
```bash
git clone [URL_DO_REPOSITORIO]
cd [NOME_DO_REPOSITORIO]
```

2. Instale as dependências
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente no arquivo `.env`

4. Execute a aplicação
```bash
uvicorn app.main:app --reload
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

- `/webhook`: Recebe webhooks do Cal.com para eventos de agendamento

## Contribuição

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request 