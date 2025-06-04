"""
Módulo para manejar la obtención y visualización de datos de la NBA.
"""

import requests
import pandas as pd
from typing import Dict, Optional, List


class NBAStats:
    def __init__(self):
        self.base_url = "https://stats.nba.com/stats/"
        self.current_season = "2024-25"
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Host": "stats.nba.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.nba.com/",
            "x-nba-stats-origin": "stats",
            "x-nba-stats-token": "true",
            "Origin": "https://www.nba.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }
        
        # Diccionario de equipos NBA
        self.equipos_nba = {
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

    def get_player_stats(self, season_type: str = "Regular Season", vs_team_id: str = None) -> pd.DataFrame:
        """Obtiene estadísticas de jugadores."""
        endpoint = "leaguedashplayerstats"
        params = {
            "MeasureType": "Base",
            "PerMode": "PerGame",
            "Season": "2023-24",  # Temporada actual
            "SeasonType": "Regular Season",
            "DateFrom": "",
            "DateTo": "",
            "GameScope": "",
            "GameSegment": "",
            "LastNGames": "0",
            "LeagueID": "00",
            "Location": "",
            "Month": "0",
            "OpponentTeamID": vs_team_id if vs_team_id else "0",
            "Outcome": "",
            "PORound": "0",
            "PaceAdjust": "N",
            "Period": "0",
            "PlayerExperience": "",
            "PlayerPosition": "",
            "PlusMinus": "N",
            "Rank": "N",
            "SeasonSegment": "",
            "ShotClockRange": "",
            "StarterBench": "",
            "TeamID": "0",
            "VsConference": "",
            "VsDivision": ""
        }
        
        try:
            print("\nObteniendo estadísticas de jugadores...")
            print("Headers:", self.headers)
            print("URL:", f"{self.base_url}{endpoint}")
            print("Parámetros:", params)
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            print(f"URL de la solicitud: {response.url}")
            print(f"Código de estado: {response.status_code}")
            print(f"Headers de respuesta: {response.headers}")
            
            if response.status_code != 200:
                print(f"Error en la respuesta: {response.text}")
                return pd.DataFrame()
            
            try:
                data = response.json()
                print("\nEstructura de datos recibida:")
                print("Claves principales:", list(data.keys()))
                if 'resultSets' in data:
                    print("Número de conjuntos de resultados:", len(data['resultSets']))
                    print("Estructura del primer conjunto:", list(data['resultSets'][0].keys()))
            except Exception as e:
                print(f"Error al decodificar JSON: {str(e)}")
                print("Contenido de la respuesta:", response.text[:500])
                return pd.DataFrame()
            
            if 'resultSets' not in data:
                print("No se encontró la estructura esperada en los datos")
                print("Claves disponibles:", list(data.keys()))
                return pd.DataFrame()
            
            try:
                df = pd.DataFrame(
                    data['resultSets'][0]['rowSet'],
                    columns=data['resultSets'][0]['headers']
                )
                print("\nDataFrame creado exitosamente")
                print(f"Dimensiones: {df.shape}")
                print("Primeras columnas:", list(df.columns)[:5])
                print("Primeras filas:", df.head(2).to_string())
            except Exception as e:
                print(f"Error al crear DataFrame: {str(e)}")
                print("Estructura de resultSets:", data['resultSets'][0].keys())
                return pd.DataFrame()
            
            return self._process_player_stats(df)
            
        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud HTTP: {str(e)}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            return pd.DataFrame()

    def get_team_stats(self, season_type: str = "Regular Season", vs_team_id: str = None) -> pd.DataFrame:
        """Obtiene estadísticas de equipos."""
        endpoint = "leaguedashteamstats"
        params = {
            "MeasureType": "Base",
            "PerMode": "PerGame",
            "Season": "2023-24",  # Temporada actual
            "SeasonType": "Regular Season",
            "DateFrom": "",
            "DateTo": "",
            "GameScope": "",
            "GameSegment": "",
            "LastNGames": "0",
            "LeagueID": "00",
            "Location": "",
            "Month": "0",
            "OpponentTeamID": vs_team_id if vs_team_id else "0",
            "Outcome": "",
            "PORound": "0",
            "PaceAdjust": "N",
            "Period": "0",
            "PlayerExperience": "",
            "PlayerPosition": "",
            "PlusMinus": "N",
            "Rank": "N",
            "SeasonSegment": "",
            "ShotClockRange": "",
            "StarterBench": "",
            "TeamID": "0",
            "VsConference": "",
            "VsDivision": ""
        }
        
        try:
            print("\nObteniendo estadísticas de equipos...")
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"Error en la respuesta: {response.text}")
                return pd.DataFrame()
            
            try:
                data = response.json()
            except Exception as e:
                print(f"Error al decodificar JSON: {str(e)}")
                return pd.DataFrame()
            
            if 'resultSets' not in data:
                print("No se encontró la estructura esperada en los datos")
                return pd.DataFrame()
            
            df = pd.DataFrame(
                data['resultSets'][0]['rowSet'],
                columns=data['resultSets'][0]['headers']
            )
            
            return self._process_team_stats(df)
            
        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud HTTP: {str(e)}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            return pd.DataFrame()

    def _process_player_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Procesa las estadísticas de jugadores."""
        if df.empty:
            print("DataFrame vacío en _process_player_stats")
            return df
            
        print("\nProcesando estadísticas de jugadores")
        print("Columnas antes del procesamiento:", list(df.columns))
        print("Número de filas:", len(df))
        print("Muestra de datos:", df.head(1).to_string())
        
        return df

    def _process_team_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Procesa las estadísticas de equipos."""
        if df.empty:
            return df
            
        print("\nColumnas disponibles en datos de equipos:", list(df.columns))
        
        # Convertir todos los nombres de columnas a un formato más legible
        column_mapping = {}
        for col in df.columns:
            # Convertir el nombre técnico a un nombre más amigable
            readable_name = col.replace('_', ' ').title()
            column_mapping[col] = readable_name
        
        # Renombrar las columnas
        df_processed = df.rename(columns=column_mapping)
        
        return df_processed

    def obtener_lista_equipos(self) -> List[str]:
        """Retorna la lista de equipos NBA ordenada alfabéticamente."""
        return sorted(list(self.equipos_nba.values()))

    def _get_team_id(self, team_name: str) -> str:
        """Obtiene el ID del equipo a partir de su nombre completo."""
        # Diccionario de IDs de equipos de la NBA
        team_ids = {
            "Atlanta Hawks": "1610612737",
            "Boston Celtics": "1610612738",
            "Brooklyn Nets": "1610612751",
            "Charlotte Hornets": "1610612766",
            "Chicago Bulls": "1610612741",
            "Cleveland Cavaliers": "1610612739",
            "Dallas Mavericks": "1610612742",
            "Denver Nuggets": "1610612743",
            "Detroit Pistons": "1610612765",
            "Golden State Warriors": "1610612744",
            "Houston Rockets": "1610612745",
            "Indiana Pacers": "1610612754",
            "Los Angeles Clippers": "1610612746",
            "Los Angeles Lakers": "1610612747",
            "Memphis Grizzlies": "1610612763",
            "Miami Heat": "1610612748",
            "Milwaukee Bucks": "1610612749",
            "Minnesota Timberwolves": "1610612750",
            "New Orleans Pelicans": "1610612740",
            "New York Knicks": "1610612752",
            "Oklahoma City Thunder": "1610612760",
            "Orlando Magic": "1610612753",
            "Philadelphia 76ers": "1610612755",
            "Phoenix Suns": "1610612756",
            "Portland Trail Blazers": "1610612757",
            "Sacramento Kings": "1610612758",
            "San Antonio Spurs": "1610612759",
            "Toronto Raptors": "1610612761",
            "Utah Jazz": "1610612762",
            "Washington Wizards": "1610612764"
        }
        return team_ids.get(team_name)

    def obtener_estadisticas_equipo(self, equipo: str, rivales: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Obtiene las estadísticas de un equipo específico, opcionalmente filtradas por rivales.
        
        Args:
            equipo: Nombre completo del equipo
            rivales: Lista opcional de nombres completos de equipos rivales
        """
        if rivales and len(rivales) == 1:
            rival_id = self._get_team_id(rivales[0])
            df = self.get_team_stats(vs_team_id=rival_id)
        else:
            df = self.get_team_stats()
            
        if df.empty:
            return df
            
        print("\nColumnas disponibles en estadísticas de equipo:")
        print(df.columns.tolist())
        
        # Verificar si la columna existe antes de usarla
        team_column = None
        possible_team_columns = ['TEAM_NAME', 'TeamName', 'TEAM']
        for col in possible_team_columns:
            if col in df.columns:
                team_column = col
                break
                
        if team_column is None:
            print("No se encontró la columna de equipo. Columnas disponibles:", df.columns.tolist())
            return pd.DataFrame()
            
        # Filtrar por equipo seleccionado
        df_equipo = df[df[team_column] == equipo]
        return df_equipo

    def obtener_estadisticas_jugadores_equipo(self, equipo: str, rivales: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Obtiene las estadísticas de los jugadores de un equipo específico.
        
        Args:
            equipo: Nombre completo del equipo
            rivales: Lista opcional de nombres completos de equipos rivales
        """
        if rivales and len(rivales) == 1:
            rival_id = self._get_team_id(rivales[0])
            df = self.get_player_stats(vs_team_id=rival_id)
        else:
            df = self.get_player_stats()
            
        if df.empty:
            print("No se obtuvieron datos de jugadores")
            return df
            
        print("\nColumnas disponibles en el DataFrame:")
        print(df.columns.tolist())
            
        # Buscar la abreviatura del equipo
        abreviatura = None
        for abr, nombre in self.equipos_nba.items():
            if nombre == equipo:
                abreviatura = abr
                break
        
        if not abreviatura:
            print(f"No se encontró la abreviatura para el equipo {equipo}")
            return pd.DataFrame()
        
        print(f"\nBuscando jugadores del equipo {abreviatura}")
        
        # Verificar si la columna existe antes de usarla
        team_column = None
        possible_team_columns = ['TEAM_ABBREVIATION', 'Team', 'TEAM']
        for col in possible_team_columns:
            if col in df.columns:
                team_column = col
                break
                
        if team_column is None:
            print("No se encontró la columna de equipo. Columnas disponibles:", df.columns.tolist())
            return pd.DataFrame()
            
        print(f"Usando columna de equipo: {team_column}")
        print(f"Valores únicos en columna {team_column}: {df[team_column].unique()}")
        
        # Filtrar por equipo seleccionado usando la abreviatura
        df_jugadores = df[df[team_column] == abreviatura]
        
        print(f"Jugadores encontrados para {abreviatura}: {len(df_jugadores)}")
        
        if df_jugadores.empty:
            print(f"No se encontraron jugadores para el equipo {equipo}")
            
        return df_jugadores

def print_player_stats(df: pd.DataFrame, player_name: Optional[str] = None):
    """Imprime estadísticas de jugadores."""
    if df.empty:
        print("No hay estadísticas disponibles")
        return
        
    if player_name:
        df = df[df['Jugador'] == player_name]
        if df.empty:
            print(f"No se encontraron estadísticas para {player_name}")
            return
    
    print("\nEstadísticas de Jugadores")
    print("=" * 100)
    print(df.to_string(index=False))

def print_team_stats(df: pd.DataFrame, team_name: Optional[str] = None):
    """Imprime estadísticas de equipos."""
    if df.empty:
        print("No hay estadísticas disponibles")
        return
        
    if team_name:
        df = df[df['Equipo'] == team_name]
        if df.empty:
            print(f"No se encontraron estadísticas para {team_name}")
            return
    
    print("\nEstadísticas de Equipos")
    print("=" * 100)
    print(df.to_string(index=False))

def mostrar_menu_principal():
    """Muestra el menú principal de selección."""
    print("\n=== ESTADÍSTICAS NBA ===")
    print("1. Ver estadísticas de equipos")
    print("2. Ver estadísticas de jugadores")
    print("3. Salir")
    return input("\nSeleccione una opción (1-3): ")

def mostrar_menu_equipos(nba: NBAStats):
    """Muestra el menú de selección de equipos."""
    equipos = nba.obtener_lista_equipos()
    print("\n=== SELECCIONE UN EQUIPO ===")
    for i, equipo in enumerate(equipos, 1):
        print(f"{i}. {equipo}")
    
    try:
        opcion = int(input("\nSeleccione un equipo (1-30): "))
        if 1 <= opcion <= len(equipos):
            return equipos[opcion-1]
    except ValueError:
        pass
    return None

def mostrar_menu_rivales(nba: NBAStats, equipo_seleccionado: str):
    """Muestra el menú de selección de rivales."""
    equipos = [e for e in nba.obtener_lista_equipos() if e != equipo_seleccionado]
    print("\n=== SELECCIONE RIVALES (separados por comas, Enter para todos) ===")
    for i, equipo in enumerate(equipos, 1):
        print(f"{i}. {equipo}")
    
    seleccion = input("\nIngrese los números de los rivales (ej: 1,3,5): ").strip()
    if not seleccion:
        return None
        
    try:
        indices = [int(x.strip()) for x in seleccion.split(',')]
        return [equipos[i-1] for i in indices if 1 <= i <= len(equipos)]
    except (ValueError, IndexError):
        return None

if __name__ == "__main__":
    nba = NBAStats()
    
    while True:
        opcion = mostrar_menu_principal()
        
        if opcion == "3":
            print("\n¡Hasta luego!")
            break
            
        if opcion in ["1", "2"]:
            # Seleccionar equipo
            equipo = mostrar_menu_equipos(nba)
            if not equipo:
                print("\nSelección de equipo inválida")
                continue
                
            # Seleccionar rivales (opcional)
            rivales = mostrar_menu_rivales(nba, equipo)
            
            # Mostrar estadísticas según la selección
            if opcion == "1":
                df = nba.obtener_estadisticas_equipo(equipo, rivales)
                print_team_stats(df)
            else:
                df = nba.obtener_estadisticas_jugadores_equipo(equipo, rivales)
                print_player_stats(df)
        else:
            print("\nOpción inválida. Por favor, seleccione 1, 2 o 3.") 