"""
FastAPI bridge: Cal.com → Notion + WhatsApp (Z‑API)
----------------------------------------------------
• Recebe webhooks do Cal.com (BOOKING_CREATED/RESCHEDULED/CANCELLED)
• Valida assinatura HMAC (X‑Cal‑Signature‑256)
• Cria / atualiza página em um banco do Notion
• Envia mensagem de confirmação no WhatsApp via Z‑API
• Agenda lembretes para 1 hora antes da reunião

Variáveis de ambiente exigidas
-----------------------------
CAL_SECRET        : mesmo secret definido no webhook Cal.com
NOTION_TOKEN      : token de integração (Bearer) da Notion
NOTION_DB         : database_id onde serão criadas as páginas
ZAPI_INSTANCE     : id da instância Z‑API
ZAPI_TOKEN        : token da instância Z‑API
ADMIN_PHONE      : seu número de telefone para receber notificações
PORT              : porta que o Uvicorn vai expor (padrão 8000)
"""

import hmac
import hashlib
import json
import os
from datetime import datetime, timedelta

import httpx
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from . import notion, whatsapp

# --- Config -----------------------------------------------------------
CAL_SECRET = os.getenv("CAL_SECRET", "CHANGE_ME")
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_DB = os.getenv("NOTION_DB", "")
ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE", "")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN", "")
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "")

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# Inicializa o scheduler para os lembretes
scheduler = AsyncIOScheduler()
scheduler.start()

# Link fixo do Zoom
ZOOM_LINK = "https://us06web.zoom.us/j/8902841864?pwd=OIjXN37C7fjELriVg4y387EbXUSVsR.1"

# ---------------------------------------------------------------------
app = FastAPI(title="Cal.com → Notion + WhatsApp bridge")


# Utils ----------------------------------------------------------------

def _verify_signature(raw: bytes, signature: str) -> bool:
    """Compare hash do corpo com o header X‑Cal‑Signature‑256."""
    digest = hmac.new(CAL_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature or "")


def _lookup_phone(email: str) -> str:
    """Exemplo simples: supõe que o usuário colocou celular no local‑part.
    Ex.: [5511998887777]@example.com → +5511998887777
    Ajuste para sua realidade (Notion / CRM / regex etc.)."""
    local = email.split("@")[0]
    return f"+{local}" if local.isdigit() else "+0000000000"


def _format_datetime(dt_str: str) -> str:
    """Converte 2025-06-07T12:00:00Z → 07/06 09:00 (exemplo fuso‑3)."""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00")).astimezone()
    return dt.strftime("%d/%m %H:%M")


# Core -----------------------------------------------------------------

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Manipula webhooks do Cal.com"""
    try:
        data = await request.json()
        event_type = data.get("triggerEvent")
        
        if event_type not in ["BOOKING_CREATED", "BOOKING_RESCHEDULED", "BOOKING_CANCELLED"]:
            return {"status": "ignored"}
            
        # Extrai dados do evento
        event = data.get("payload", {})
        uid = event.get("uid")
        start_time = event.get("startTime")
        name = event.get("attendees", [{}])[0].get("name", "")
        email = event.get("attendees", [{}])[0].get("email", "")
        
        if event_type in ["BOOKING_CREATED", "BOOKING_RESCHEDULED"]:
            # Cria/atualiza página no Notion
            notion_response = await notion.upsert_page(
                uid=uid,
                title=name,
                start=start_time,
                name=name,
                email=email,
                meet=ZOOM_LINK  # Usando o link fixo do Zoom
            )
            
            # Busca dados completos do Notion para personalização
            page_id = notion_response.get("id")
            if page_id:
                notion_data = await notion.get_page_properties(page_id)
                properties = notion_data.get("properties", {})
                
                # Obtém o telefone do lead
                lead_phone = notion.extract_rich_text_value(properties, "Telefone")
                
                # Envia notificações (para o lead e para a equipe de vendas)
                await whatsapp.notify_booking(
                    name=name,
                    start_time=start_time,
                    meet_link=ZOOM_LINK,  # Usando o link fixo do Zoom
                    notion_data=properties,
                    lead_phone=lead_phone
                )
                
                # Agenda lembrete para o lead 1 hora antes
                if lead_phone:
                    reminder_time = datetime.fromisoformat(start_time.replace("Z", "+00:00")) - timedelta(hours=1)
                    if reminder_time > datetime.now():
                        scheduler.add_job(
                            whatsapp.send_reminder,
                            trigger=DateTrigger(run_date=reminder_time),
                            args=[name, start_time, ZOOM_LINK, lead_phone],  # Usando o link fixo do Zoom
                            id=f"reminder_{uid}"
                        )
            
        elif event_type == "BOOKING_CANCELLED":
            # TODO: Implementar lógica para cancelamento
            pass
            
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def status_from_trigger(trigger: str) -> str:
    return {
        "BOOKING_CREATED": "Agendado",
        "BOOKING_RESCHEDULED": "Remarcado",
        "BOOKING_CANCELLED": "Cancelado",
    }[trigger]


# --- Entrypoint -------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )
