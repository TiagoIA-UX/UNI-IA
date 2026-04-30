import requests
from datetime import datetime

def fetch_economic_events(date=None):
    """
    Consulta eventos econômicos do dia usando a API do FRED (exemplo, pode ser adaptado para outra API).
    """
    # Exemplo de endpoint público (substitua por outro se necessário)
    # Para produção, usar Investing, Yahoo Finance ou fonte mais completa
    API_URL = 'https://financialmodelingprep.com/api/v3/economic_calendar'
    params = {'from': date or datetime.now().strftime('%Y-%m-%d'), 'to': date or datetime.now().strftime('%Y-%m-%d')}
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f'Erro ao buscar calendário econômico: {e}')
        return []

if __name__ == '__main__':
    eventos = fetch_economic_events()
    for evento in eventos:
        print(evento)
