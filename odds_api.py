"""
Módulo para manejar la obtención y procesamiento de datos de apuestas deportivas.
"""

import requests
from typing import Dict, Optional

class OddsAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        
    def get_odds(self, equipo_local: str, equipo_visitante: str) -> Dict:
        """
        Obtiene las cuotas para un partido específico.
        
        Args:
            equipo_local: Abreviatura del equipo local (ej: 'LAL')
            equipo_visitante: Abreviatura del equipo visitante (ej: 'GSW')
            
        Returns:
            Dict con la información de las cuotas
        """
        endpoint = 'sports/basketball_nba/odds'
        params = {
            'apiKey': self.api_key,
            'regions': 'eu',
            'markets': 'h2h,spreads,totals',
            'oddsFormat': 'decimal',
            'bookmakers': 'betsson'
        }
        
        try:
            print("\nBuscando cuotas...")
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            # Mostrar información de créditos
            print("\nCréditos restantes:", response.headers.get('x-requests-remaining', 'No disponible'))
            print("Créditos usados:", response.headers.get('x-requests-used', 'No disponible'))
            
            data = response.json()
            
            # Buscar el partido específico
            for partido in data:
                if (partido['home_team'] == self.get_team_name(equipo_local) and 
                    partido['away_team'] == self.get_team_name(equipo_visitante)):
                    return self._format_odds(partido)
            
            print("No se encontró el partido especificado")
            return {}
                
        except Exception as e:
            print(f"Error al obtener cuotas: {str(e)}")
            return {}
    
    def _format_odds(self, partido: Dict) -> Dict:
        """Formatea las cuotas para una mejor presentación."""
        resultado = {
            'fecha': partido['commence_time'],
            'equipos': {
                'local': partido['home_team'],
                'visitante': partido['away_team']
            },
            'mercados': {}
        }
        
        for bookmaker in partido.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                tipo_mercado = self._get_market_description(market['key'])
                resultado['mercados'][tipo_mercado] = {
                    outcome['name']: outcome['price']
                    for outcome in market['outcomes']
                }
        
        return resultado
    
    def _get_market_description(self, mercado: str) -> str:
        """Retorna una descripción en español del mercado."""
        descripciones = {
            'h2h': 'Ganador del Partido',
            'spreads': 'Handicap',
            'totals': 'Puntos Totales',
            'player_points': 'Puntos por Jugador',
            'player_rebounds': 'Rebotes por Jugador',
            'player_assists': 'Asistencias por Jugador',
            'player_threes': 'Triples por Jugador'
        }
        return descripciones.get(mercado, mercado)
    
    def get_team_name(self, abreviatura: str) -> str:
        """Convierte la abreviatura del equipo en su nombre completo."""
        equipos = {
            "ATL": "Atlanta Hawks", "BOS": "Boston Celtics",
            "BKN": "Brooklyn Nets", "CHA": "Charlotte Hornets",
            "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
            "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets",
            "DET": "Detroit Pistons", "GSW": "Golden State Warriors",
            "HOU": "Houston Rockets", "IND": "Indiana Pacers",
            "LAC": "Los Angeles Clippers", "LAL": "Los Angeles Lakers",
            "MEM": "Memphis Grizzlies", "MIA": "Miami Heat",
            "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
            "NOP": "New Orleans Pelicans", "NYK": "New York Knicks",
            "OKC": "Oklahoma City Thunder", "ORL": "Orlando Magic",
            "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns",
            "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings",
            "SAS": "San Antonio Spurs", "TOR": "Toronto Raptors",
            "UTA": "Utah Jazz", "WAS": "Washington Wizards"
        }
        return equipos.get(abreviatura, abreviatura)

def print_odds(odds: Dict):
    """Imprime las cuotas de manera formateada."""
    if not odds:
        print("No hay cuotas disponibles")
        return
        
    print(f"\nCuotas para: {odds['equipos']['visitante']} @ {odds['equipos']['local']}")
    print(f"Fecha: {odds['fecha']}")
    print("\nMercados disponibles:")
    
    for mercado, cuotas in odds['mercados'].items():
        print(f"\n{mercado}:")
        for equipo, cuota in cuotas.items():
            print(f"  {equipo}: {cuota:.2f}")

if __name__ == "__main__":
    API_KEY = "0ff64327790e3509a31c7121b2a5c9a2"
    client = OddsAPI(API_KEY)
    
    print("\nBienvenido al sistema de consulta de cuotas NBA")
    print("\nEquipos disponibles:")
    equipos = {
        "ATL": "Atlanta Hawks", "BOS": "Boston Celtics",
        "BKN": "Brooklyn Nets", "CHA": "Charlotte Hornets",
        "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
        "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets",
        "DET": "Detroit Pistons", "GSW": "Golden State Warriors",
        "HOU": "Houston Rockets", "IND": "Indiana Pacers",
        "LAC": "Los Angeles Clippers", "LAL": "Los Angeles Lakers",
        "MEM": "Memphis Grizzlies", "MIA": "Miami Heat",
        "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
        "NOP": "New Orleans Pelicans", "NYK": "New York Knicks",
        "OKC": "Oklahoma City Thunder", "ORL": "Orlando Magic",
        "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns",
        "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings",
        "SAS": "San Antonio Spurs", "TOR": "Toronto Raptors",
        "UTA": "Utah Jazz", "WAS": "Washington Wizards"
    }
    
    for abrev, nombre in equipos.items():
        print(f"{abrev}: {nombre}")
    
    equipo_visitante = input("\nIngrese la abreviatura del equipo visitante (ej: LAL): ").upper()
    equipo_local = input("Ingrese la abreviatura del equipo local (ej: GSW): ").upper()
    
    if equipo_visitante not in equipos or equipo_local not in equipos:
        print("Error: Una o ambas abreviaturas de equipo no son válidas.")
    else:
        odds = client.get_odds(equipo_local, equipo_visitante)
        print_odds(odds) 