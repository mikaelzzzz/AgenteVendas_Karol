import os, httpx
from datetime import datetime

TOKEN = os.getenv("NOTION_TOKEN")
DB_ID = os.getenv("NOTION_DB")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

async def get_page_properties(page_id: str):
    """Busca todas as propriedades de uma página do Notion"""
    async with httpx.AsyncClient(timeout=10) as c:
        response = await c.get(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=HEADERS
        )
        return response.json()

async def upsert_page(uid, title, start, name, email, meet):
    """Cria ou atualiza uma página no Notion"""
    # Converte a data UTC para objeto datetime
    dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    # Formata a data no padrão brasileiro
    formatted_date = dt.strftime("%d-%m-%Y às %H:%M")
    
    body = {
        "parent": {"database_id": DB_ID},
        "properties": {
            "Cliente": {"title": [{"text": {"content": name}}]},
            "Email": {"email": email},
            "Status": {"select": {"name": "Agendado reunião"}},
            "Data Agendada pelo Lead": {"rich_text": [{"text": {"content": formatted_date}}]},
            "Telefone": {"rich_text": [{"text": {"content": ""}}]},  # Será preenchido manualmente
            "Profissão": {"rich_text": [{"text": {"content": ""}}]},  # Será preenchido manualmente
            "Objetivo": {"rich_text": [{"text": {"content": ""}}]},  # Será preenchido manualmente
            "Histórico Inglês": {"rich_text": [{"text": {"content": ""}}]},  # Será preenchido manualmente
            "Real Motivação": {"rich_text": [{"text": {"content": ""}}]},  # Será preenchido manualmente
            "Idade": {"rich_text": [{"text": {"content": ""}}]},  # Será preenchido manualmente
            "Indicação": {"rich_text": [{"text": {"content": ""}}]}  # Será preenchido manualmente
        }
    }
    
    async with httpx.AsyncClient(timeout=10) as c:
        response = await c.post(
            "https://api.notion.com/v1/pages",
            json=body,
            headers=HEADERS
        )
        return response.json()

async def query_database(filter_property: str, filter_value: str):
    """Busca páginas no banco de dados do Notion com um filtro específico"""
    body = {
        "filter": {
            "property": filter_property,
            "rich_text": {
                "equals": filter_value
            }
        }
    }
    
    async with httpx.AsyncClient(timeout=10) as c:
        response = await c.post(
            f"https://api.notion.com/v1/databases/{DB_ID}/query",
            json=body,
            headers=HEADERS
        )
        return response.json()

def extract_rich_text_value(properties: dict, property_name: str) -> str:
    """Extrai o valor de uma propriedade rich_text do Notion"""
    prop = properties.get(property_name, {})
    if prop.get("type") == "rich_text" and prop.get("rich_text"):
        return prop["rich_text"][0]["text"]["content"]
    return ""

def extract_title_value(properties: dict, property_name: str) -> str:
    """Extrai o valor de uma propriedade title do Notion"""
    prop = properties.get(property_name, {})
    if prop.get("type") == "title" and prop.get("title"):
        return prop["title"][0]["text"]["content"]
    return ""
