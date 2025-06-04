"""
Módulo para manejar la obtención y visualización de datos de la NBA.
"""

import requests
import pandas as pd
from typing import Dict, Optional, List
from datetime import datetime


class NBAStats:
    # Constantes para tipos de temporada
    REGULAR_SEASON = "Regular Season"
    PLAYOFFS = "Playoffs"
    PRE_SEASON = "Pre Season"
    ALL_STAR = "All Star"
    
    # Lista de temporadas disponibles (últimos 5 años)
    TEMPORADAS = [
        "2024-25",
        "2023-24",
        "2022-23",
        "2021-22",
        "2020-21",
        "2019-20"
    ]
    
    # Tipos de temporada disponibles
    TIPOS_TEMPORADA = [
        REGULAR_SEASON,
        PLAYOFFS,
        PRE_SEASON,
        ALL_STAR
    ]
    
    def __init__(self):
        self.base_url = "https://stats.nba.com/stats/"
        # Obtener la temporada actual basada en la fecha
        self.current_season = self._get_current_season()
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Host": "stats.nba.com",
            "Origin": "https://www.nba.com",
            "Referer": "https://www.nba.com/",
            "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "x-nba-stats-origin": "stats",
            "x-nba-stats-token": "true"
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
        print("NBA Stats inicializado con headers actualizados")

    def _get_current_season(self) -> str:
        """Determina la temporada actual basada en la fecha."""
        now = datetime.now()
        year = now.year
        month = now.month
        
        # Si estamos entre octubre y diciembre, la temporada es year-year+1
        # Si estamos entre enero y septiembre, la temporada es year-1-year
        if month >= 10:
            return f"{year}-{str(year+1)[2:]}"
        else:
            return f"{year-1}-{str(year)[2:]}"

    def get_player_stats(self, season: str = None, season_type: str = REGULAR_SEASON, vs_team_id: str = None) -> pd.DataFrame:
        """Obtiene estadísticas de jugadores."""
        if season is None:
            season = self.current_season
            
        endpoint = "leaguedashplayerstats"
        params = {
            "MeasureType": "Base",
            "PerMode": "PerGame",
            "Season": season,
            "SeasonType": season_type,
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
            print(f"\nObteniendo estadísticas de jugadores para {season} ({season_type})...")
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"Error en la respuesta: {response.text}")
                return pd.DataFrame()
            
            data = response.json()
            if 'resultSets' not in data:
                print("No se encontró la estructura esperada en los datos")
                return pd.DataFrame()
            
            df = pd.DataFrame(
                data['resultSets'][0]['rowSet'],
                columns=data['resultSets'][0]['headers']
            )
            
            # Asegurarnos de que tenemos la columna de nombres
            if 'PLAYER_NAME' not in df.columns:
                # Intentar obtener nombres de jugadores
                endpoint_players = "commonallplayers"
                params_players = {
                    "LeagueID": "00",
                    "Season": season,
                    "IsOnlyCurrentSeason": "1"
                }
                
                response_players = requests.get(
                    f"{self.base_url}{endpoint_players}",
                    headers=self.headers,
                    params=params_players,
                    timeout=30
                )
                
                if response_players.status_code == 200:
                    data_players = response_players.json()
                    if 'resultSets' in data_players:
                        df_players = pd.DataFrame(
                            data_players['resultSets'][0]['rowSet'],
                            columns=data_players['resultSets'][0]['headers']
                        )
                        # Crear diccionario de mapeo ID -> Nombre
                        player_names = dict(zip(df_players['PERSON_ID'], df_players['DISPLAY_FIRST_LAST']))
                        # Añadir columna de nombres
                        df['PLAYER_NAME'] = df['PLAYER_ID'].map(player_names)
            
            # Agregar columnas de temporada y tipo
            df['SEASON'] = season
            df['SEASON_TYPE'] = season_type
            
            return self._process_player_stats(df)
            
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

        # Asegurarnos de que tenemos una columna de nombres
        if 'PLAYER_NAME' not in df.columns:
            if 'PLAYER' in df.columns:
                df['PLAYER_NAME'] = df['PLAYER']
            elif 'PLAYER_ID' in df.columns:
                print("Solo tenemos IDs de jugadores, necesitamos obtener los nombres")
                return df
        
        # Asegurarnos de que los nombres sean strings
        if 'PLAYER_NAME' in df.columns:
            df['PLAYER_NAME'] = df['PLAYER_NAME'].astype(str)
            # Limpiar nombres si es necesario
            df['PLAYER_NAME'] = df['PLAYER_NAME'].apply(lambda x: x.strip() if isinstance(x, str) else x)
            
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

    def obtener_lista_temporadas(self) -> List[str]:
        """Retorna la lista de temporadas disponibles."""
        return self.TEMPORADAS

    def obtener_tipos_temporada(self) -> List[str]:
        """Retorna la lista de tipos de temporada disponibles."""
        return self.TIPOS_TEMPORADA

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

    def obtener_estadisticas_equipo(self, equipo: str, rivales: Optional[List[str]] = None, 
                                temporada: Optional[str] = None, tipo_temporada: str = REGULAR_SEASON) -> pd.DataFrame:
        """
        Obtiene las estadísticas de un equipo específico, opcionalmente filtradas por rivales.
        
        Args:
            equipo: Nombre completo del equipo
            rivales: Lista opcional de nombres completos de equipos rivales
            temporada: Temporada (ej: "2023-24")
            tipo_temporada: Tipo de temporada (Regular Season, Playoffs, etc)
        """
        if rivales and len(rivales) == 1:
            rival_id = self._get_team_id(rivales[0])
            df = self.get_team_stats(season=temporada, season_type=tipo_temporada, vs_team_id=rival_id)
        else:
            df = self.get_team_stats(season=temporada, season_type=tipo_temporada)
            
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

    def obtener_estadisticas_jugadores_equipo(self, equipo: str, rivales: Optional[List[str]] = None,
                                            temporada: Optional[str] = None, tipo_temporada: str = REGULAR_SEASON) -> pd.DataFrame:
        """
        Obtiene las estadísticas de los jugadores de un equipo específico.
        
        Args:
            equipo: Nombre completo del equipo
            rivales: Lista opcional de nombres completos de equipos rivales
            temporada: Temporada (ej: "2023-24")
            tipo_temporada: Tipo de temporada (Regular Season, Playoffs, etc)
        """
        if rivales and len(rivales) == 1:
            rival_id = self._get_team_id(rivales[0])
            df = self.get_player_stats(season=temporada, season_type=tipo_temporada, vs_team_id=rival_id)
        else:
            df = self.get_player_stats(season=temporada, season_type=tipo_temporada)
            
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

    def get_player_game_logs(self, player_id: str, season: str = None, season_type: str = REGULAR_SEASON, vs_team_id: str = None) -> pd.DataFrame:
        """Obtiene estadísticas partido a partido de un jugador específico."""
        if season is None:
            season = self.current_season
            
        endpoint = "playergamelog"
        params = {
            "DateFrom": "",
            "DateTo": "",
            "GameSegment": "",
            "LastNGames": "0",
            "LeagueID": "00",
            "Location": "",
            "MeasureType": "Base",
            "Month": "0",
            "OpponentTeamID": vs_team_id if vs_team_id else "0",
            "Outcome": "",
            "PORound": "0",
            "Season": season,
            "SeasonSegment": "",
            "SeasonType": season_type,
            "TeamID": "0",
            "PlayerID": player_id,
            "VsConference": "",
            "VsDivision": ""
        }
        
        try:
            print(f"\nObteniendo logs de partidos para jugador {player_id} en {season} ({season_type})...")
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"Error en la respuesta: {response.text}")
                return pd.DataFrame()
            
            data = response.json()
            if 'resultSets' not in data:
                print("No se encontró la estructura esperada en los datos")
                return pd.DataFrame()
            
            df = pd.DataFrame(
                data['resultSets'][0]['rowSet'],
                columns=data['resultSets'][0]['headers']
            )
            
            # Agregar columnas de temporada y tipo
            df['SEASON'] = season
            df['SEASON_TYPE'] = season_type
            
            return df
            
        except Exception as e:
            print(f"Error al obtener logs de partidos: {str(e)}")
            return pd.DataFrame()

    def obtener_estadisticas_jugador_por_partido(self, equipo: str, jugador: str) -> pd.DataFrame:
        """
        Obtiene las estadísticas partido a partido de un jugador específico.
        
        Args:
            equipo: Nombre completo del equipo
            jugador: Nombre del jugador
        """
        # Primero obtenemos el ID del equipo
        team_id = self._get_team_id(equipo)
        if not team_id:
            print(f"No se encontró el ID para el equipo {equipo}")
            return pd.DataFrame()
        
        # Obtenemos los logs de partidos
        df = self.get_player_game_logs(player_id=team_id)
        
        if df.empty:
            return df
        
        # Buscamos al jugador específico
        player_name_col = None
        for col in df.columns:
            if 'PLAYER_NAME' in col:
                player_name_col = col
                break
        
        if not player_name_col:
            print("No se encontró la columna con nombres de jugadores")
            return pd.DataFrame()
        
        return df[df[player_name_col] == jugador]

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