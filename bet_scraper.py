"""
Módulo para extraer información de props y cuotas de diferentes casas de apuestas.
"""

import re
from typing import Dict, Optional, List, Tuple
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class BetScraper:
    """Clase para extraer información de props y cuotas de casas de apuestas."""
    
    SUPPORTED_SITES = {
        'bet365.com': 'bet365',
        'betway.com': 'betway',
        'codere.com': 'codere',
        'betsson.com': 'betsson',
        'bwin.com': 'bwin'
    }

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

    def get_site_name(self, url: str) -> Optional[str]:
        """Identifica la casa de apuestas basada en la URL."""
        try:
            domain = urlparse(url).netloc.lower()
            for site_domain, site_name in self.SUPPORTED_SITES.items():
                if site_domain in domain:
                    return site_name
        except Exception:
            pass
        return None

    def extract_props(self, url: str) -> Dict:
        """
        Extrae las props y cuotas de una URL de apuestas.
        
        Args:
            url: URL de la página de apuestas
            
        Returns:
            Dict con la información extraída:
            {
                'site': nombre de la casa de apuestas,
                'player': nombre del jugador,
                'props': [
                    {
                        'type': tipo de prop (puntos, asistencias, etc),
                        'line': línea de la prop,
                        'over_odds': cuota para over,
                        'under_odds': cuota para under
                    },
                    ...
                ]
            }
        """
        site_name = self.get_site_name(url)
        if not site_name:
            return {
                'error': 'Casa de apuestas no soportada',
                'supported_sites': list(self.SUPPORTED_SITES.keys())
            }

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Llamar al método específico para cada casa de apuestas
            parser_method = getattr(self, f'parse_{site_name}', None)
            if parser_method:
                return parser_method(response.text)
            else:
                return {'error': f'Parser no implementado para {site_name}'}
                
        except requests.RequestException as e:
            return {'error': f'Error al acceder a la página: {str(e)}'}
        except Exception as e:
            return {'error': f'Error inesperado: {str(e)}'}

    def parse_bet365(self, html: str) -> Dict:
        """Parser específico para Bet365."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Implementar lógica específica para Bet365
            # Este es un ejemplo, necesitaría adaptarse a la estructura real del sitio
            return {
                'site': 'bet365',
                'player': 'Nombre del jugador',  # Extraer del HTML
                'props': []  # Extraer props del HTML
            }
        except Exception as e:
            return {'error': f'Error parseando Bet365: {str(e)}'}

    def parse_betway(self, html: str) -> Dict:
        """Parser específico para Betway."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Implementar lógica específica para Betway
            return {
                'site': 'betway',
                'player': 'Nombre del jugador',  # Extraer del HTML
                'props': []  # Extraer props del HTML
            }
        except Exception as e:
            return {'error': f'Error parseando Betway: {str(e)}'}

    def standardize_prop_type(self, prop_text: str) -> Optional[str]:
        """
        Estandariza el tipo de prop a un formato común.
        Por ejemplo: "Points O/U" -> "Puntos"
        """
        prop_mapping = {
            'point': 'Puntos',
            'points': 'Puntos',
            'assist': 'Asistencias',
            'assists': 'Asistencias',
            'rebound': 'Rebotes',
            'rebounds': 'Rebotes',
            'three': 'Triples',
            'threes': 'Triples',
            '3pt': 'Triples',
            'steal': 'Robos',
            'steals': 'Robos',
            'block': 'Tapones',
            'blocks': 'Tapones',
            'turnover': 'Pérdidas',
            'turnovers': 'Pérdidas'
        }
        
        text = prop_text.lower()
        for key, value in prop_mapping.items():
            if key in text:
                return value
        return None

    def extract_number(self, text: str) -> Optional[float]:
        """Extrae un número de un texto."""
        try:
            matches = re.findall(r'[-+]?\d*\.\d+|\d+', text)
            if matches:
                return float(matches[0])
        except Exception:
            pass
        return None

    def clean_odds(self, odds_text: str) -> Optional[float]:
        """Limpia y convierte las cuotas a formato decimal."""
        try:
            # Remover espacios y caracteres no numéricos
            odds_text = re.sub(r'[^\d./-]', '', odds_text)
            
            # Si es formato americano (ej: +150, -110)
            if '+' in odds_text or '-' in odds_text:
                odds = float(odds_text)
                if odds > 0:
                    return round(1 + (odds/100), 2)
                else:
                    return round(1 + (100/abs(odds)), 2)
            
            # Si es formato fraccionario (ej: 3/2)
            if '/' in odds_text:
                num, den = map(float, odds_text.split('/'))
                return round(1 + (num/den), 2)
            
            # Si es formato decimal
            return round(float(odds_text), 2)
            
        except Exception:
            return None 