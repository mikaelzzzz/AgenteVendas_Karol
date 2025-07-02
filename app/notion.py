import os, httpx
from datetime import datetime

TOKEN = os.getenv("NOTION_TOKEN")
DB_ID = os.getenv("NOTION_DB")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

async def get_database_properties():
    """Busca todas as propriedades do database do Notion"""
    async with httpx.AsyncClient(timeout=10) as c:
        response = await c.get(
            f"https://api.notion.com/v1/databases/{DB_ID}",
            headers=HEADERS
        )
        if response.status_code == 200:
            return response.json().get("properties", {})
        return None

async def get_page_properties(page_id: str):
    """Busca todas as propriedades de uma página do Notion"""
    async with httpx.AsyncClient(timeout=10) as c:
        response = await c.get(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=HEADERS
        )
        return response.json()

async def update_page(page_id: str, properties: dict):
    """Atualiza uma página no Notion."""
    body = {"properties": properties}
    async with httpx.AsyncClient(timeout=10) as c:
        response = await c.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            json=body,
            headers=HEADERS
        )
        return response.json()

async def upsert_page(uid, title, start, name, email, meet):
    """Cria ou atualiza uma página no Notion"""
    # Converte a data UTC para objeto datetime
    dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    # Formata a data no padrão brasileiro
    formatted_date = dt.strftime("%d-%m-%Y às %H:%M")

    # Busca por uma página existente com o número de telefone (uid)
    search_results = await query_database(filter_property="Telefone", filter_value=uid)
    
    if search_results and search_results.get("results"):
        # Página encontrada, vamos atualizá-la
        page_id = search_results["results"][0]["id"]
        properties_to_update = {
            "Status": {"select": {"name": "Agendado reunião"}},
            "Email": {"email": email},
            "Data Agendada pelo Lead": {"rich_text": [{"text": {"content": formatted_date}}]},
        }
        return await update_page(page_id, properties_to_update)
    
    # Página não encontrada, vamos criar uma nova
    # Busca as propriedades do database para garantir que estamos usando os tipos corretos
    db_properties = await get_database_properties()
    if not db_properties:
        raise Exception("Não foi possível obter as propriedades do database")
    
    # Inicializa as propriedades básicas que sabemos que existem
    properties = {
        "Cliente": {"title": [{"text": {"content": name}}]},
        "Email": {"email": email},
        "Status": {"select": {"name": "Agendado reunião"}},
        "Data Agendada pelo Lead": {"rich_text": [{"text": {"content": formatted_date}}]},
        "Telefone": {"rich_text": [{"text": {"content": uid}}]},
    }
    
    # Adiciona outras propriedades baseadas no schema do database
    text_properties = ["Profissão", "Objetivo", "Histórico Inglês", 
                      "Real Motivação", "Idade", "Indicação"]
    
    for prop_name in text_properties:
        if prop_name in db_properties and prop_name not in properties:
            prop_type = db_properties[prop_name]["type"]
            if prop_type == "rich_text":
                properties[prop_name] = {"rich_text": [{"text": {"content": ""}}]}
            elif prop_type == "select":
                properties[prop_name] = {"select": None}
            elif prop_type == "multi_select":
                properties[prop_name] = {"multi_select": []}
            elif prop_type == "number":
                properties[prop_name] = {"number": None}
            # Adicione outros tipos conforme necessário
    
    body = {
        "parent": {"database_id": DB_ID},
        "properties": properties
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
