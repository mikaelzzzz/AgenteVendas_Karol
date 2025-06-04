from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# --- Notion -----------------------------------------------------------
NOTION_API_KEY     = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_URL     = "https://api.notion.com/v1/pages"
NOTION_VERSION     = "2022-06-28"

# --- Z-API – dois modos possíveis -------------------------------------
ZAPI_URL            = os.getenv("ZAPI_URL")            # modo 1: endpoint completo
ZAPI_INSTANCE_ID    = os.getenv("ZAPI_INSTANCE_ID")    # modo 2: instância + token
ZAPI_TOKEN          = os.getenv("ZAPI_TOKEN")
ZAPI_SECURITY_TOKEN = os.getenv("ZAPI_SECURITY_TOKEN")

# --- Alertas e OpenAI -------------------------------------------------
ALERT_PHONES = [
    os.getenv("ALERT_PHONE", "5511975578651"),  # principal (pode vir do .env)
    "5511957708562",                             # novo número 1
    "5511955911993",                             # novo número 2
]

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Cliente OpenAI (SDK >=1.0)
client = OpenAI() if OPENAI_API_KEY else None

app = FastAPI()

# ---------------------------------------------------------------------
# 1) CLASSIFICAÇÃO DO LEAD
# ---------------------------------------------------------------------

def classificar_lead_basico(indicacao: str, motivo: str) -> str:
    texto_motivo    = (motivo or "").lower()
    texto_indicacao = (indicacao or "").lower()

    alto_keywords = ["perdeu o emprego", "oportunidade de emprego", "viagem"]
    if any(kw in texto_motivo for kw in alto_keywords):
        return "Alto"

    if texto_indicacao and "perdeu" in texto_motivo and "emprego" in texto_motivo:
        return "Alto"

    if "aprimorar" in texto_motivo:
        return "Médio" if "manter" in texto_motivo else "Baixo"

    return "Baixo"


def classificar_lead(indicacao: str, motivo: str) -> str:
    """Tenta usar ChatGPT; se falhar ou não houver chave, recorre às regras simples."""
    if client:
        prompt = (
            "Você é um agente de vendas experiente. "
            "Classifique o lead como Alto, Médio ou Baixo seguindo as regras: "
            "Alto quando mencionou perda de emprego, oportunidade ou viagem; "
            "Alto também se houve indicação + perda de emprego; "
            "Médio quando quer apenas manter o inglês; "
            "Baixo quando quer apenas aprimorar sem objetivo claro.\n"
            f"Indicação: {indicacao}\nMotivo: {motivo}"
        )
        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0,
            )
            resultado = resp.choices[0].message.content.strip()
            if resultado in {"Alto", "Médio", "Baixo"}:
                return resultado
        except Exception as exc:
            print(f"[WARN] Falha na classificação com ChatGPT: {exc}")

    return classificar_lead_basico(indicacao, motivo)

# ---------------------------------------------------------------------
# 2) ENVIO DE WHATSAPP (suporta URL único ou instância/token)
# ---------------------------------------------------------------------

def _build_zapi_url() -> tuple[str | None, dict]:
    if ZAPI_URL:  # Modo 1
        return ZAPI_URL, {}
    if ZAPI_INSTANCE_ID and ZAPI_TOKEN:  # Modo 2
        url = (
            f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/"
            f"token/{ZAPI_TOKEN}/send-text"
        )
        headers = {"Client-Token": ZAPI_SECURITY_TOKEN} if ZAPI_SECURITY_TOKEN else {}
        return url, headers
    return None, {}


def send_whatsapp_message(phone: str, message: str) -> None:
    url, headers = _build_zapi_url()
    if not url:
        print("[INFO] Z-API não configurado; mensagem não enviada.")
        return
    try:
        requests.post(url, json={"phone": phone, "message": message}, headers=headers, timeout=10)
    except Exception as exc:
        print(f"[WARN] Erro ao enviar WhatsApp: {exc}")

# ---------------------------------------------------------------------
# 3) MENSAGEM PARA LEADS “ALTO”
# ---------------------------------------------------------------------

def gerar_mensagem_alto(**info) -> str:
    if client:
        prompt = (
            "Crie um texto curto para o time de vendas explicando por que o lead "
            "a seguir é de alta qualificação, citando os pontos principais.\n"
            f"{info}"
        )
        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=120,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            print(f"[WARN] Falha ao gerar mensagem com ChatGPT: {exc}")

    linhas = ["Lead com alta chance de fechar negócio!"]
    for k, v in info.items():
        if v:
            linhas.append(f"{k.capitalize()}: {v}")
    return "\n".join(linhas)

# ---------------------------------------------------------------------
# 4) ROTAS FASTAPI
# ---------------------------------------------------------------------


@app.get("/")
async def root():
    return {"message": "API is running"}


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    # --- dados do lead ------------------------------------------------
    nome            = data.get("nome")
    email           = data.get("email")
    whatsapp        = data.get("whatsapp")
    profissao       = data.get("profissao")
    idade           = data.get("idade")
    indicacao       = data.get("indicacao")
    motivo          = data.get("motivo")
    historico       = data.get("historico")
    disponibilidade = data.get("disponibilidade")

    if not all([nome, email, whatsapp]):
        return {"error": "Nome, email ou WhatsApp faltando."}

    nivel = classificar_lead(indicacao, motivo)

    # --- Envia para o Notion -----------------------------------------
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }
    notion_payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Cliente": {"title": [{"text": {"content": nome}}]},
            "Email": {"email": email},
            "Profissão": {"rich_text": [{"text": {"content": profissao or ""}}]},
            "Indicação": {"rich_text": [{"text": {"content": indicacao or ""}}]},
            "Idade": {"rich_text": [{"text": {"content": str(idade or "")}}]},
            "Histórico Inglês": {"rich_text": [{"text": {"content": historico or ""}}]},
            "Disponibilidade Horário": {"rich_text": [{"text": {"content": disponibilidade or ""}}]},
            "Telefone": {"rich_text": [{"text": {"content": whatsapp}}]},
            "Real Motivação": {"rich_text": [{"text": {"content": motivo or ""}}]},
            "Nível de Qualificação": {"multi_select": [{"name": nivel}]},
        },
    }
    notion_resp = requests.post(NOTION_API_URL, headers=headers, json=notion_payload)

        # --- Se for Alto, dispara alerta no WhatsApp ----------------------
    if nivel == "Alto":
        mensagem = gerar_mensagem_alto(
            nome=nome,
            email=email,
            whatsapp=whatsapp,
            idade=idade,
            profissao=profissao,
            motivo=motivo,
            historico=historico,
        )
        for phone in ALERT_PHONES:
            send_whatsapp_message(phone, mensagem)

    if notion_resp.status_code in (200, 201):
        return {"message": "Dados enviados para o Notion com sucesso."}
    return {"error": notion_resp.text}, notion_resp.status_code
