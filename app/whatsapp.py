import os
import httpx
import logging
from datetime import datetime
from .chatgpt import generate_sales_message

# Configuração do logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('whatsapp_service')

INSTANCE_ID = os.getenv("ZAPI_INSTANCE")
TOKEN = os.getenv("ZAPI_TOKEN")
CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN")

# Números da equipe de vendas
SALES_TEAM_PHONES = ["5511975578651", "5511957708562", "5511955911993"]

HEADERS = {
    "Content-Type": "application/json",
    "Client-Token": CLIENT_TOKEN
}

BASE_URL = f"https://api.z-api.io/instances/{INSTANCE_ID}/token/{TOKEN}"

logger.info(f"WhatsApp Service initialized with instance {INSTANCE_ID}")

async def send_message(phone: str, message: str) -> dict:
    """
    Envia uma mensagem de texto via WhatsApp usando a Z-API.
    
    Args:
        phone (str): Número do telefone no formato DDI DDD NÚMERO (ex: 551199999999)
        message (str): Mensagem a ser enviada
        
    Returns:
        dict: Resposta da API contendo zaapId, messageId e id
    """
    logger.debug(f"Iniciando envio de mensagem de texto para {phone}")
    
    # Remove qualquer formatação do número de telefone
    clean_phone = ''.join(filter(str.isdigit, phone))
    logger.debug(f"Número formatado: {clean_phone}")
    
    # Endpoint para envio de mensagem de texto
    url = f"{BASE_URL}/send-text"
    
    payload = {
        "phone": clean_phone,
        "message": message,
        "delayMessage": 2,  # Delay de 2 segundos entre mensagens
        "delayTyping": 3    # Mostra "Digitando..." por 3 segundos
    }
    
    try:
        logger.debug(f"Fazendo requisição para {url}")
        logger.debug(f"Payload: {payload}")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=HEADERS)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Mensagem enviada com sucesso. messageId: {result.get('messageId')}")
            return result
    except httpx.HTTPError as e:
        logger.error(f"Erro HTTP ao enviar mensagem: {str(e)}")
        logger.error(f"Status code: {e.response.status_code if hasattr(e, 'response') else 'N/A'}")
        logger.error(f"Response body: {e.response.text if hasattr(e, 'response') else 'N/A'}")
        
        if e.response.status_code == 405:
            raise Exception("Erro 405: Método HTTP incorreto")
        elif e.response.status_code == 415:
            raise Exception("Erro 415: Content-Type não especificado corretamente")
        else:
            raise Exception(f"Erro ao enviar mensagem WhatsApp: {str(e)}")

async def send_link_message(
    phone: str,
    message: str,
    link_url: str,
    title: str = "Reunião Zoom",
    description: str = "Link para a reunião",
    add_link_to_message: bool = True,
) -> dict:
    """
    Envia uma mensagem com link clicável via WhatsApp usando a Z-API.
    
    Args:
        phone (str): Número do telefone no formato DDI DDD NÚMERO (ex: 551199999999)
        message (str): Mensagem a ser enviada (deve incluir o link no final)
        link_url (str): URL do link
        title (str): Título do link
        description (str): Descrição do link
        add_link_to_message (bool): Adiciona o link ao final da mensagem
        
    Returns:
        dict: Resposta da API contendo zaapId, messageId e id
    """
    logger.debug(f"Iniciando envio de mensagem com link para {phone}")
    
    # Remove qualquer formatação do número de telefone
    clean_phone = ''.join(filter(str.isdigit, phone))
    logger.debug(f"Número formatado: {clean_phone}")
    
    # Define a mensagem a ser enviada, evitando duplicação do link se já estiver no corpo
    full_message = f"{message}\n{link_url}" if add_link_to_message else message
    
    # Endpoint para envio de link
    url = f"{BASE_URL}/send-link"
    
    payload = {
        "phone": clean_phone,
        "message": full_message,
        "image": "https://zoom.us/favicon.ico",  # Ícone do Zoom
        "linkUrl": link_url,
        "title": title,
        "linkDescription": description,
        "linkType": "LARGE",  # Visualização grande do link
        "delayMessage": 2,
        "delayTyping": 3
    }
    
    try:
        logger.debug(f"Fazendo requisição para {url}")
        logger.debug(f"Payload: {payload}")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=HEADERS)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Mensagem com link enviada com sucesso. messageId: {result.get('messageId')}")
            return result
    except httpx.HTTPError as e:
        logger.error(f"Erro HTTP ao enviar mensagem com link: {str(e)}")
        logger.error(f"Status code: {e.response.status_code if hasattr(e, 'response') else 'N/A'}")
        logger.error(f"Response body: {e.response.text if hasattr(e, 'response') else 'N/A'}")
        
        if e.response.status_code == 405:
            raise Exception("Erro 405: Método HTTP incorreto")
        elif e.response.status_code == 415:
            raise Exception("Erro 415: Content-Type não especificado corretamente")
        else:
            raise Exception(f"Erro ao enviar mensagem com link: {str(e)}")

async def notify_booking(name: str, start_time: str, meet_link: str, notion_data: dict = None, lead_phone: str = None) -> None:
    """
    Envia notificações de agendamento via WhatsApp.
    
    Args:
        name (str): Nome do lead
        start_time (str): Horário da reunião
        meet_link (str): Link da reunião
        notion_data (dict): Dados completos do lead do Notion
        lead_phone (str): Número do telefone do lead
    """
    logger.info(f"Iniciando notificação de agendamento para {name}")
    logger.debug(f"Dados recebidos: start_time={start_time}, lead_phone={lead_phone}")
    logger.debug(f"Dados do Notion: {notion_data}")
    
    try:
        # Converte a data para formato brasileiro
        dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        formatted_date = dt.strftime("%d-%m-%Y às %H:%M")
        logger.debug(f"Data formatada: {formatted_date}")
        
        # Mensagem com link para o lead
        if lead_phone:
            logger.info(f"Enviando mensagem para o lead: {lead_phone}")
            lead_message = (
                f"Olá, {name}! 👋\n\n"
                f"✅ Sua reunião está confirmada para *{dt.strftime('%d/%m')}* às *{dt.strftime('%H:%M')}*.\n\n"
                "🖥️ Sala da reunião (Zoom):\n"
                f"👉 {meet_link}\n\n"
                "Antes disso, que tal fazer nosso teste de nivelamento?\n"
                "👉 https://student.flexge.com/v2/placement/karollinyeloica\n"
                "Faça o teste sem pressa, no seu tempo, ok? 😉\n\n"
                "Aproveite e assista a este vídeo para entender por que nosso método é diferenciado!\n"
                "👉 https://www.youtube.com/watch?v=gjNVofHX6gg\n"
            )
            await send_link_message(
                phone=lead_phone,
                message=lead_message,
                link_url=meet_link,
                title="Reunião Zoom",
                description=f"Reunião agendada para {formatted_date}",
                add_link_to_message=False,
            )
            logger.info("Mensagem enviada com sucesso para o lead")
        
        # Mensagem detalhada para a equipe de vendas
        if notion_data:
            logger.info("Gerando mensagem para equipe de vendas")
            sales_message = await generate_sales_message(notion_data)
            
            # Adiciona informações da reunião à análise
            full_sales_message = (
                f"{sales_message}\n\n"
                f"📅 *Dados da Reunião*\n"
                f"Data: {formatted_date}\n"
                f"Email: {notion_data.get('Email', 'Não informado')}\n"
                f"Telefone: {lead_phone or 'Não informado'}\n\n"
                "Link da reunião:"
            )
            
            logger.debug("Iniciando envio para equipe de vendas")
            for sales_phone in SALES_TEAM_PHONES:
                logger.debug(f"Enviando para vendedor: {sales_phone}")
                await send_link_message(
                    phone=sales_phone,
                    message=full_sales_message,
                    link_url=meet_link,
                    title="Reunião Zoom",
                    description=f"Reunião com {name} - {formatted_date}"
                )
            logger.info("Mensagens enviadas com sucesso para toda equipe de vendas")
            
    except Exception as e:
        logger.error(f"Erro ao processar notificação de agendamento: {str(e)}", exc_info=True)
        raise

async def send_reminder(name: str, start_time: str, meet_link: str, phone: str = None) -> None:
    """
    Envia lembrete 1 hora antes da reunião via WhatsApp.
    """
    logger.info(f"Iniciando envio de lembrete para {name}")
    logger.debug(f"Dados do lembrete: start_time={start_time}, phone={phone}")
    
    if not phone:
        logger.warning("Telefone não fornecido para envio do lembrete")
        return
        
    try:
        # Converte a data para formato brasileiro
        dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        logger.debug(f"Data convertida: {dt}")
        
        message = (
            f"Olá, {name}, passando para lembrar da nossa reunião hoje. "
            f"Te vejo daqui a pouco! {dt.strftime('%d-%m')} às {dt.strftime('%H:%M')}\n\n"
            "Clique no link abaixo para acessar a reunião:"
        )
        
        await send_link_message(
            phone=phone,
            message=message,
            link_url=meet_link,
            title="Reunião Zoom",
            description=f"Reunião agendada para {dt.strftime('%d-%m-%Y às %H:%M')}"
        )
        logger.info("Lembrete enviado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao enviar lembrete: {str(e)}", exc_info=True)
        raise
