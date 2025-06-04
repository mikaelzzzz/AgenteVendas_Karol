from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY   = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_URL   = "https://api.notion.com/v1/pages"
NOTION_VERSION   = "2022-06-28"
ZAPI_URL = os.getenv("ZAPI_URL")  # Full endpoint for sending WhatsApp messages

app = FastAPI()


def classificar_lead(indicacao: str, motivo: str) -> str:
    """Classifica o lead de acordo com as regras de qualificação."""
    texto_motivo = (motivo or "").lower()
    texto_indicacao = (indicacao or "").lower()

    alto_keywords = ["perdeu o emprego", "oportunidade de emprego", "viagem"]
    for kw in alto_keywords:
        if kw in texto_motivo:
            return "Alto"

    if texto_indicacao and "perdeu" in texto_motivo and "emprego" in texto_motivo:
        return "Alto"

    if "aprimorar" in texto_motivo:
        if "manter" in texto_motivo:
            return "Médio"
        return "Baixo"

    return "Baixo"


def send_whatsapp_message(phone: str, message: str) -> None:
    """Envia mensagem via Z-API se a URL estiver configurada."""
    if not ZAPI_URL:
        return
    payload = {"phone": phone, "message": message}
    try:
        requests.post(ZAPI_URL, json=payload, timeout=10)
    except Exception as exc:
        print(f"Erro ao enviar mensagem: {exc}")

@app.get("/")
async def root():
    return {"message": "API is running"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    nome        = data.get('nome')
    email       = data.get('email')
    whatsapp    = data.get('whatsapp')
    profissao   = data.get('profissao')
    indicacao   = data.get('indicacao')
    motivo      = data.get('motivo')
    historico   = data.get('historico')
    disponibilidade = data.get('disponibilidade')

    nivel_qualificacao = classificar_lead(indicacao, motivo)

    if not all([nome, email, whatsapp]):
        return {"error": "Nome, email ou WhatsApp faltando."}

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type":  "application/json",
        "Notion-Version": NOTION_VERSION
    }

    payload = {
        "parent": { "database_id": NOTION_DATABASE_ID },
        "properties": {
            "Cliente": {
                "title": [
                    { "text": { "content": nome } }
                ]
            },
            "Email": { 
                "email": email 
            },
            "Profissão": {
                "rich_text": [
                    { "text": { "content": profissao or "" } }
                ]
            },
            "Indicação": {
                "rich_text": [
                    { "text": { "content": indicacao or "" } }
                ]
            },
            "Histórico Inglês": {
                "rich_text": [
                    { "text": { "content": historico or "" } }
                ]
            },
            "Disponibilidade Horário": {
                "rich_text": [
                    { "text": { "content": disponibilidade or "" } }
                ]
            },
            "Telefone": {
                "rich_text": [
                    { "text": { "content": whatsapp or "" } }
                ]
            },
            "Real Motivação": {
                "rich_text": [
                    { "text": { "content": motivo or "" } }
                ]
            },
            "Nível de Qualificação": {
                "multi_select": [
                    {"name": nivel_qualificacao}
                ]
            }
        }
    }

    response = requests.post(NOTION_API_URL, headers=headers, json=payload)

    if nivel_qualificacao == "Alto":
        mensagem = (
            "Lead com alta chance de fechar negócio!\n"
            f"Nome: {nome}\nEmail: {email}\nWhatsApp: {whatsapp}"
        )
        send_whatsapp_message("5511975578651", mensagem)

    if response.status_code in (200, 201):
        return {"message": "Dados enviados para o Notion com sucesso."}
    else:
        return {"error": response.text}, response.status_code
