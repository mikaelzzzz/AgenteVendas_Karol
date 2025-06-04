from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv
import openai

load_dotenv()

NOTION_API_KEY   = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_URL   = "https://api.notion.com/v1/pages"
NOTION_VERSION   = "2022-06-28"
ZAPI_INSTANCE_ID = os.getenv("ZAPI_INSTANCE_ID")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
ZAPI_SECURITY_TOKEN = os.getenv("ZAPI_SECURITY_TOKEN")
ALERT_PHONE = os.getenv("ALERT_PHONE", "11975578651")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

app = FastAPI()


def classificar_lead_basico(indicacao: str, motivo: str) -> str:
    """Classifica o lead utilizando apenas regras simples de palavras-chave."""
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


def classificar_lead(indicacao: str, motivo: str) -> str:
    """Usa o ChatGPT para qualificar o lead ou aplica as regras básicas."""
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
        prompt = (
            "Você é um agente de vendas com muitos anos de experiência. "
            "Classifique o potencial deste lead como Alto, Médio ou Baixo seguindo as regras: "
            "Alto quando mencionou perda de emprego, oportunidade ou viagem; "
            "Alto também se houve indicação e perda de emprego; "
            "Médio quando deseja apenas manter o inglês; "
            "Baixo quando quer apenas aprimorar sem objetivo claro. "
            "Responda apenas com uma das palavras: Alto, Médio ou Baixo.\n"
            f"Indicação: {indicacao}\nMotivação: {motivo}"
        )
        try:
            resp = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0
            )
            result = resp.choices[0].message.content.strip()
            if result in {"Alto", "Médio", "Baixo"}:
                return result
        except Exception as exc:
            print(f"Erro ao classificar lead com ChatGPT: {exc}")

    return classificar_lead_basico(indicacao, motivo)


def send_whatsapp_message(phone: str, message: str) -> None:
    """Envia mensagem via Z-API se as variáveis estiverem configuradas."""
    if not all([ZAPI_INSTANCE_ID, ZAPI_TOKEN, ZAPI_SECURITY_TOKEN]):
        return
    url = (
        f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/"
        f"token/{ZAPI_TOKEN}/send-text"
    )
    headers = {"Client-Token": ZAPI_SECURITY_TOKEN}
    payload = {"phone": phone, "message": message}
    try:
        requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception as exc:
        print(f"Erro ao enviar mensagem: {exc}")


def gerar_mensagem_alto(nome: str, email: str, whatsapp: str, idade: str,
                        profissao: str, motivo: str, historico: str) -> str:
    """Gera mensagem detalhada para leads qualificados."""
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
        prompt = (
            "Crie um texto curto para o time de vendas explicando por que o lead a seguir "
            "é considerado de alta qualificação. Utilize as informações fornecidas e cite os "
            "motivos explicitamente.\n"
            f"Nome: {nome}\nEmail: {email}\nWhatsApp: {whatsapp}\n"
            f"Profissão: {profissao}\nIdade: {idade}\nMotivação: {motivo}\n"
            f"Histórico de Inglês: {historico}"
        )
        try:
            resp = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=120,
                temperature=0.7
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            print(f"Erro ao gerar mensagem com ChatGPT: {exc}")

    partes = [
        "Lead com alta chance de fechar negócio!",
        f"Nome: {nome}",
        f"Email: {email}",
        f"WhatsApp: {whatsapp}",
        f"Profissão: {profissao}",
        f"Idade: {idade}",
        f"Motivação: {motivo}",
        f"Histórico: {historico}",
    ]
    return "\n".join(partes)

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
    idade       = data.get('idade')
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
            "Idade": {
                "rich_text": [
                    { "text": { "content": str(idade or "") } }
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
        mensagem = gerar_mensagem_alto(
            nome=nome,
            email=email,
            whatsapp=whatsapp,
            idade=idade,
            profissao=profissao,
            motivo=motivo,
            historico=historico,
        )
        send_whatsapp_message(ALERT_PHONE, mensagem)

    if response.status_code in (200, 201):
        return {"message": "Dados enviados para o Notion com sucesso."}
    else:
        return {"error": response.text}, response.status_code
