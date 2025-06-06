"""
Módulo para manejar la obtención y procesamiento de datos de apuestas deportivas.
"""

import requests
import pandas as pd
from typing import Dict, Optional, List, Tuple
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os.path
import json
import streamlit as st
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('GoogleSheetsOddsLoader')

class GoogleSheetsOddsLoader:
    # Scope necesario para leer Google Sheets
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    def __init__(self, spreadsheet_id: str):
        """
        Inicializa el cargador de cuotas desde Google Sheets.
        
        Args:
            spreadsheet_id: ID del documento de Google Sheets
        """
        self.spreadsheet_id = spreadsheet_id
        self.creds = None
        logger.info(f"Inicializando GoogleSheetsOddsLoader con spreadsheet_id: {spreadsheet_id}")
        
    def _get_credentials(self):
        """
        Obtiene las credenciales usando Service Account desde los secrets de Streamlit.
        Si no están disponibles o si está configurado para desarrollo local, intenta cargar desde archivos locales.
        """
        try:
            logger.info("Intentando obtener credenciales...")
            
            # Verificar si estamos en modo desarrollo local
            use_local = False
            if hasattr(st, 'secrets'):
                if 'gcp_service_account' in st.secrets:
                    if st.secrets.gcp_service_account.get('use_local_credentials', False):
                        logger.info("Configurado para usar credenciales locales")
                        use_local = True
                    elif len(st.secrets.gcp_service_account) > 1:  # Si tiene más campos además de use_local_credentials
                        logger.info("Usando credenciales de Streamlit Secrets")
                        credentials_dict = st.secrets["gcp_service_account"]
                        logger.info("Claves disponibles en credentials_dict: " + ", ".join(credentials_dict.keys()))
                        use_local = False
            
            # Si no hay secrets o estamos en modo desarrollo local, buscar archivos locales
            if use_local or not hasattr(st, 'secrets'):
                logger.info("Buscando credenciales en archivos locales...")
                # Fallback a archivos locales para desarrollo
                current_dir = os.path.dirname(os.path.abspath(__file__))
                possible_files = [
                    os.path.join(current_dir, 'service-account.json'),
                    os.path.join(current_dir, 'credentials.json'),
                    'service-account.json',  # Buscar en el directorio actual
                    'credentials.json'       # Buscar en el directorio actual
                ]
                
                credentials_dict = None
                for file_path in possible_files:
                    logger.info(f"Intentando cargar credenciales desde: {file_path}")
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, 'r') as f:
                                credentials_dict = json.load(f)
                            logger.info(f"Credenciales cargadas desde {file_path}")
                            break
                        except Exception as e:
                            logger.warning(f"Error al cargar {file_path}: {str(e)}")
                            continue
                
                if credentials_dict is None:
                    raise FileNotFoundError(
                        "No se encontraron credenciales. Archivos buscados:\n" + 
                        "\n".join(f"- {f}" for f in possible_files)
                    )
            
            if credentials_dict is None:
                raise ValueError("No se pudieron obtener las credenciales de ninguna fuente")
                
            try:
                # Crear credenciales desde el diccionario
                self.creds = service_account.Credentials.from_service_account_info(
                    credentials_dict, scopes=self.SCOPES)
                logger.info("Credenciales de Service Account configuradas correctamente")
                return self.creds
            except Exception as e:
                logger.error(f"Error al configurar las credenciales: {str(e)}")
                raise
                
        except Exception as e:
            logger.error(f"Error al cargar las credenciales: {str(e)}")
            raise
        
    def _process_player_name(self, sheet_name: str) -> str:
        """
        Procesa el nombre de la hoja para obtener el nombre completo del jugador.
        Formato esperado: 'Apellido, Nombre', 'Apellido_Nombre', 'Nombre Apellido' o cualquier otro formato
        
        Args:
            sheet_name: Nombre de la hoja del Google Sheets
            
        Returns:
            str: Nombre completo del jugador formateado
        """
        # Limpiar el nombre
        name = sheet_name.strip()
        
        # Si el nombre usa coma para separar
        if ',' in name:
            parts = name.split(',')
            if len(parts) == 2:
                last_name = parts[0].strip()
                first_name = parts[1].strip()
                return f"{first_name} {last_name}"  # Retornar en formato "Nombre Apellido"
        
        # Si el nombre usa guión bajo para separar
        elif '_' in name:
            parts = name.split('_')
            if len(parts) >= 2:
                last_name = parts[0].strip()
                first_name = ' '.join(parts[1:]).strip()
                return f"{first_name} {last_name}"  # Retornar en formato "Nombre Apellido"
        
        # Si el nombre ya está en formato "Nombre Apellido"
        elif ' ' in name:
            return name
        
        # Si no hay separador, devolver el nombre tal cual
        return name
        
    def _convert_to_float(self, value) -> Optional[float]:
        """
        Convierte un valor a float, manejando diferentes formatos de números.
        """
        try:
            logger.debug(f"Intentando convertir valor: '{value}' (tipo: {type(value)})")
            
            if pd.isna(value) or value == '':
                return None
                
            if isinstance(value, (int, float)):
                return float(value)
                
            # Limpiar el valor
            value_str = str(value).strip()
            
            # Si está vacío, retornar None
            if not value_str:
                return None
                
            # Reemplazar comas por puntos si hay coma
            if ',' in value_str:
                value_str = value_str.replace(',', '.')
                
            # Intentar convertir
            try:
                return float(value_str)
            except ValueError:
                # Si falla, intentar limpiar caracteres no numéricos
                import re
                numeric_str = re.sub(r'[^\d.-]', '', value_str)
                if numeric_str:
                    return float(numeric_str)
                return None
                
        except Exception as e:
            logger.error(f"Error al convertir valor '{value}': {str(e)}")
            return None
        
    def load_odds(self) -> Dict[str, List[Dict]]:
        """
        Carga y procesa las cuotas desde Google Sheets.
                             
        Returns:
            Dict[str, List[Dict]]: Diccionario con nombres de jugadores como claves y lista de props como valores
        """
        try:
            logger.info(f"\nIniciando lectura del Google Sheets: {self.spreadsheet_id}")
            
            # Obtener credenciales y construir el servicio
            creds = self._get_credentials()
            logger.info("Credenciales obtenidas correctamente")
            
            service = build('sheets', 'v4', credentials=creds)
            logger.info("Servicio de Google Sheets construido correctamente")
            
            # Obtener todas las hojas del documento
            logger.info("Obteniendo metadatos del documento...")
            sheet_metadata = service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheets = sheet_metadata.get('sheets', [])
            logger.info(f"Hojas encontradas: {len(sheets)}")
            
            # Diccionario para almacenar las props por jugador
            props_por_jugador = {}
            
            for sheet in sheets:
                sheet_name = sheet['properties']['title']
                logger.info(f"\nProcesando hoja: {sheet_name}")
                
                # Procesar el nombre del jugador
                nombre_jugador = self._process_player_name(sheet_name)
                logger.info(f"Nombre procesado: {nombre_jugador}")
                
                # Obtener los datos de la hoja
                logger.info(f"Obteniendo datos de la hoja {sheet_name}...")
                result = service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{sheet_name}!A:C"
                ).execute()
                values = result.get('values', [])
                
                if not values:
                    logger.warning(f"No se encontraron datos en la hoja {sheet_name}")
                    continue
                
                logger.info(f"Filas obtenidas: {len(values)}")
                
                props_list = []
                current_prop = None
                
                logger.info("\nProcesando filas...")
                
                i = 0
                while i < len(values):
                    try:
                        row = values[i]
                        # Asegurarse de que la fila tiene 3 columnas
                        while len(row) < 3:
                            row.append('')
                            
                        logger.debug(f"Fila {i+1}: {row}")
                        
                        # Si la primera columna no está vacía, es una nueva prop
                        prop_name = row[0].strip()
                        if prop_name:
                            logger.info(f"\nNueva prop encontrada: {prop_name}")
                            
                            # Procesar líneas y cuotas
                            over_line = self._convert_to_float(row[1])
                            under_line = self._convert_to_float(row[2])
                            over_odds = None
                            under_odds = None
                            
                            # Si hay siguiente fila, intentar obtener las cuotas
                            if i + 1 < len(values):
                                next_row = values[i + 1]
                                while len(next_row) < 3:
                                    next_row.append('')
                                    
                                over_odds = self._convert_to_float(next_row[1])
                                under_odds = self._convert_to_float(next_row[2])
                                
                            # Crear la prop solo si tiene al menos una línea válida
                            if over_line is not None or under_line is not None:
                                current_prop = {
                                    'prop_name': prop_name,
                                    'over_line': over_line,
                                    'under_line': under_line,
                                    'over_odds': over_odds,
                                    'under_odds': under_odds
                                }
                                props_list.append(current_prop)
                                logger.info("✓ Prop agregada correctamente")
                                logger.info(f"   Over: {over_line} @ {over_odds}")
                                logger.info(f"   Under: {under_line} @ {under_odds}")
                            else:
                                logger.warning("✗ Prop ignorada por falta de líneas válidas")
                            
                            i += 2  # Avanzar dos filas (prop y cuotas)
                        else:
                            i += 1  # Avanzar una fila
                            
                    except Exception as e:
                        logger.error(f"❌ Error procesando fila {i+1}: {str(e)}")
                        i += 1
                        continue
                
                # Si encontramos props en esta hoja, las guardamos con el nombre del jugador
                if props_list:
                    props_por_jugador[nombre_jugador] = props_list
                    logger.info(f"\nProps guardadas para {nombre_jugador}: {len(props_list)}")
            
            logger.info(f"\nResumen del procesamiento:")
            logger.info(f"Total de jugadores: {len(props_por_jugador)}")
            for jugador, props in props_por_jugador.items():
                logger.info(f"\n{jugador}: {len(props)} props")
                for idx, prop in enumerate(props, 1):
                    logger.info(f"\n{idx}. {prop['prop_name']}:")
                    if prop['over_line'] is not None:
                        logger.info(f"   Más de {prop['over_line']}: {prop['over_odds']}")
                    if prop['under_line'] is not None:
                        logger.info(f"   Menos de {prop['under_line']}: {prop['under_odds']}")
            
            return props_por_jugador
            
        except Exception as e:
            logger.error(f"\n❌ Error general al procesar el archivo:")
            logger.error(f"Tipo de error: {type(e).__name__}")
            logger.error(f"Mensaje: {str(e)}")
            import traceback
            logger.error(f"\nTraceback completo:")
            logger.error(traceback.format_exc())
            return {}
            
    def print_odds(self):
        """
        Imprime las cuotas de manera formateada.
        """
        props = self.load_odds()
        if not props:
            print("No se encontraron cuotas para mostrar")
            return
            
        print("\nCuotas disponibles:")
        print("-" * 80)
        for jugador, props_list in props.items():
            print(f"\n{jugador}:")
            for prop in props_list:
                print(f"\n  {prop['prop_name']}")
                if prop['over_line'] is not None and prop['over_odds'] is not None:
                    print(f"    Más de {prop['over_line']}: {prop['over_odds']:.2f}")
                if prop['under_line'] is not None and prop['under_odds'] is not None:
                    print(f"    Menos de {prop['under_line']}: {prop['under_odds']:.2f}")
        print("-" * 80)

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
    print("\nBienvenido al sistema de consulta de cuotas NBA")
    
    # Inicializar el cargador de cuotas desde Google Sheets
    SPREADSHEET_ID = "1VTn80vGKu9MbAHZoV9UoVKYyPeVkh-6_N6DMNQInKQk"  # Reemplaza esto con tu ID
    loader = GoogleSheetsOddsLoader(SPREADSHEET_ID)
    
    # Cargar y mostrar las cuotas
    print("\nCargando cuotas desde Google Sheets...")
    loader.print_odds() 