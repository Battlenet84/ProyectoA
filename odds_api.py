"""
Módulo para manejar la obtención y procesamiento de datos de apuestas deportivas.
"""

import requests
import pandas as pd
from typing import Dict, Optional, List, Tuple

class ExcelOddsLoader:
    def __init__(self, file_path: str):
        """
        Inicializa el cargador de cuotas desde Excel.
        
        Args:
            file_path: Ruta al archivo Excel
        """
        self.file_path = file_path
        
    def _process_player_name(self, sheet_name: str) -> str:
        """
        Procesa el nombre de la hoja para obtener el nombre completo del jugador.
        Formato esperado: 'Apellido, Nombre' o 'Apellido_Nombre'
        
        Args:
            sheet_name: Nombre de la hoja del Excel
            
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
                return f"{last_name}, {first_name}"
        
        # Si el nombre usa guión bajo para separar
        elif '_' in name:
            parts = name.split('_')
            if len(parts) >= 2:
                last_name = parts[0].strip()
                first_name = ' '.join(parts[1:]).strip()
                return f"{last_name}, {first_name}"
        
        # Si no hay separador, devolver el nombre tal cual
        return name
        
    def _convert_to_float(self, value) -> Optional[float]:
        """
        Convierte un valor a float, manejando diferentes formatos de números.
        """
        try:
            print(f"\nIntentando convertir valor: '{value}' (tipo: {type(value)})")
            
            if pd.isna(value):
                print("Valor es NA/NaN")
                return None
                
            if isinstance(value, (int, float)):
                print(f"Valor es numérico: {float(value)}")
                return float(value)
                
            # Limpiar el valor
            value_str = str(value).strip()
            print(f"Valor limpio: '{value_str}'")
            
            # Si está vacío, retornar None
            if not value_str:
                print("Valor está vacío")
                return None
                
            # Intentar convertir directamente
            try:
                result = float(value_str)
                print(f"Conversión directa exitosa: {result}")
                return result
            except ValueError:
                # Reemplazar coma por punto si hay coma
                if ',' in value_str:
                    value_str = value_str.replace(',', '.')
                    result = float(value_str)
                    print(f"Conversión con reemplazo de coma exitosa: {result}")
                    return result
                raise
                
        except Exception as e:
            print(f"Error al convertir valor '{value}': {str(e)}")
            return None
        
    def load_odds(self, tiene_encabezados: bool = False) -> Dict[str, List[Dict]]:
        """
        Carga y procesa las cuotas desde el archivo Excel.
        
        Args:
            tiene_encabezados: Si True, asume que la primera fila contiene encabezados.
                             Si False, asume que la primera fila ya es una prop.
                             
        Returns:
            Dict[str, List[Dict]]: Diccionario con nombres de jugadores como claves y lista de props como valores
        """
        try:
            print(f"\n{'='*50}")
            print(f"Iniciando lectura del archivo: {self.file_path}")
            print(f"Formato: {'Con encabezados' if tiene_encabezados else 'Sin encabezados'}")
            print(f"{'='*50}")
            
            # Intentar leer todas las hojas del Excel
            try:
                excel_file = pd.ExcelFile(self.file_path)
                sheet_names = excel_file.sheet_names
                print(f"\nHojas encontradas: {sheet_names}")
                
                # Diccionario para almacenar las props por jugador
                props_por_jugador = {}
                
                for sheet_name in sheet_names:
                    print(f"\nProcesando hoja: {sheet_name}")
                    
                    # Procesar el nombre del jugador
                    nombre_jugador = self._process_player_name(sheet_name)
                    print(f"Nombre procesado: {nombre_jugador}")
                    
                    # Leer la hoja actual
                    df = pd.read_excel(self.file_path, sheet_name=sheet_name, header=None)
                    print(f"Dimensiones del DataFrame: {df.shape}")
                    print("\nPrimeras 5 filas del Excel:")
                    print(df.head().to_string())
                    print("\nTipos de datos por columna:")
                    print(df.dtypes)
                    
                    # Si tiene encabezados, saltamos la primera fila
                    if tiene_encabezados and len(df) > 1:
                        df = df.iloc[1:].reset_index(drop=True)
                        print("\nSaltando fila de encabezados")
                    
                    props_list = []
                    current_prop = None
                    
                    print("\nProcesando filas:")
                    print("-" * 40)
                    
                    i = 0
                    while i < len(df):
                        try:
                            row = df.iloc[i].tolist()
                            print(f"\nFila {i+1}:")
                            print(f"Contenido: {row}")
                            print(f"Tipos de datos: {[type(x) for x in row]}")
                            
                            # Si la primera columna no está vacía, es una nueva prop
                            if pd.notna(df.iloc[i, 0]):
                                print("\nNueva prop encontrada")
                                current_prop = {
                                    'prop_name': str(df.iloc[i, 0]).strip(),
                                    'over_line': self._convert_to_float(df.iloc[i, 1]),
                                    'under_line': self._convert_to_float(df.iloc[i, 2]),
                                    'over_odds': None,
                                    'under_odds': None
                                }
                                print("Datos de la prop:")
                                print(current_prop)
                                
                                # Si hay siguiente fila, intentar obtener las cuotas
                                if i + 1 < len(df):
                                    next_row = df.iloc[i + 1].tolist()
                                    print("\nFila de cuotas encontrada:")
                                    print(f"Contenido: {next_row}")
                                    print(f"Tipos de datos: {[type(x) for x in next_row]}")
                                    
                                    current_prop['over_odds'] = self._convert_to_float(df.iloc[i + 1, 1])
                                    current_prop['under_odds'] = self._convert_to_float(df.iloc[i + 1, 2])
                                    
                                    print("Cuotas procesadas:")
                                    print(f"Over: {current_prop['over_odds']}")
                                    print(f"Under: {current_prop['under_odds']}")
                                    
                                    # Validar que tenemos al menos una línea y su cuota correspondiente
                                    if ((current_prop['over_line'] is not None and current_prop['over_odds'] is not None) or
                                        (current_prop['under_line'] is not None and current_prop['under_odds'] is not None)):
                                        props_list.append(current_prop)
                                        print("✓ Prop agregada correctamente")
                                    else:
                                        print("✗ Prop ignorada por falta de líneas o cuotas válidas")
                                    
                                    i += 2
                                else:
                                    print("✗ No hay fila de cuotas para esta prop")
                                    i += 1
                            else:
                                print("Fila ignorada (primera columna vacía)")
                                i += 1
                                
                        except Exception as e:
                            print(f"❌ Error procesando fila {i+1}: {str(e)}")
                            i += 1
                            continue
                    
                    # Si encontramos props en esta hoja, las guardamos con el nombre del jugador
                    if props_list:
                        props_por_jugador[nombre_jugador] = props_list
                        print(f"\nProps guardadas para {nombre_jugador}: {len(props_list)}")
                
                print(f"\n{'='*50}")
                print(f"Resumen del procesamiento:")
                print(f"Total de jugadores: {len(props_por_jugador)}")
                for jugador, props in props_por_jugador.items():
                    print(f"\n{jugador}: {len(props)} props")
                    for idx, prop in enumerate(props, 1):
                        print(f"\n{idx}. {prop['prop_name']}:")
                        if prop['over_line'] is not None:
                            print(f"   Más de {prop['over_line']}: {prop['over_odds']}")
                        if prop['under_line'] is not None:
                            print(f"   Menos de {prop['under_line']}: {prop['under_odds']}")
                print(f"{'='*50}")
                
                return props_por_jugador
                
            except Exception as e:
                print(f"\n❌ Error al leer el Excel: {str(e)}")
                return {}
            
        except Exception as e:
            print(f"\n❌ Error general al procesar el archivo:")
            print(f"Tipo de error: {type(e).__name__}")
            print(f"Mensaje: {str(e)}")
            import traceback
            print(f"\nTraceback completo:")
            print(traceback.format_exc())
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
        for prop in props:
            print(f"\n{prop['prop_name']}")
            if prop['over_line'] is not None and prop['over_odds'] is not None:
                print(f"  Más de {prop['over_line']}: {prop['over_odds']:.2f}")
            if prop['under_line'] is not None and prop['under_odds'] is not None:
                print(f"  Menos de {prop['under_line']}: {prop['under_odds']:.2f}")
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