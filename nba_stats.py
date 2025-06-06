"""
Módulo para manejar la obtención y visualización de datos de la NBA.
"""

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import pandas as pd
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import time


class NBAStats:
    # Constantes para tipos de temporada
    REGULAR_SEASON = "Regular Season"
    PLAYOFFS = "Playoffs"
    PRE_SEASON = "Pre Season"
    ALL_STAR = "All Star"
    
    # Lista de temporadas disponibles
    TEMPORADAS = [
        "2024-25",  # Incluye proyecciones y datos de pretemporada
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
    
    def _validate_season(self, season: str) -> bool:
        """Valida si una temporada es válida y está disponible."""
        try:
            if season not in self.TEMPORADAS:
                print(f"Advertencia: La temporada {season} no está en la lista de temporadas conocidas")
                # Verificar si el formato es correcto (YYYY-YY)
                if not (len(season) == 7 and season[4] == '-' and season[:4].isdigit() and season[5:].isdigit()):
                    print(f"Error: Formato de temporada inválido. Debe ser YYYY-YY")
                    return False
                # Si el formato es correcto, permitir la temporada aunque no esté en la lista
                print("Sin embargo, el formato es correcto, se intentará obtener los datos")
                return True
            return True
        except Exception as e:
            print(f"Error al validar la temporada: {str(e)}")
            return False
    
    def __init__(self):
        self.base_url = "https://stats.nba.com/stats/"
        # Obtener la temporada actual basada en la fecha
        self.current_season = self._get_current_season()
        
        # Configurar reintentos
        retry_strategy = Retry(
            total=3,  # número total de reintentos
            backoff_factor=1,  # tiempo de espera entre reintentos
            status_forcelist=[429, 500, 502, 503, 504]  # códigos HTTP para reintentar
        )
        
        # Crear sesión con la estrategia de reintentos
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Headers para las peticiones
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nba.com/',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
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
        """
        Determina la temporada actual basada en la fecha.
        La temporada NBA comienza en octubre y termina en junio del siguiente año.
        """
        current_date = datetime.now()
        year = current_date.year
        month = current_date.month
        
        # Si estamos entre julio y diciembre, la temporada es el año actual + siguiente
        if month >= 7:
            return f"{year}-{str(year + 1)[2:]}"
        # Si estamos entre enero y junio, la temporada es el año anterior + actual
        else:
            return f"{year-1}-{str(year)[2:]}"

    def _make_request(self, url: str, params: Dict = None, timeout: int = 60) -> Dict:
        """Realiza una petición a la API con reintentos y manejo de errores."""
        max_retries = 3
        retry_delay = 2  # segundos
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=timeout
                )
                response.raise_for_status()
                
                # Esperar un poco entre llamadas para evitar límites de velocidad
                time.sleep(1)
                
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:  # último intento
                    raise Exception(f"Error después de {max_retries} intentos: {str(e)}")
                print(f"Intento {attempt + 1} falló, reintentando en {retry_delay} segundos...")
                time.sleep(retry_delay)
                retry_delay *= 2  # aumentar el tiempo de espera exponencialmente

    def get_player_stats(self, season: str = None, season_type: str = REGULAR_SEASON, vs_team_id: str = None) -> pd.DataFrame:
        """Obtiene estadísticas de jugadores."""
        if season is None:
            season = self._get_current_season()  # Usar el método para determinar la temporada actual
            print(f"Usando temporada actual: {season}")
            
        if not self._validate_season(season):
            print(f"Advertencia: La temporada {season} podría no tener datos completos")
        
        endpoint = "leaguedashplayerstats"
        params = {
            "DateFrom": "",
            "DateTo": "",
            "GameScope": "",
            "GameSegment": "",
            "LastNGames": "0",
            "LeagueID": "00",
            "Location": "",
            "MeasureType": "Base",
            "Month": "0",
            "OpponentTeamID": vs_team_id if vs_team_id else "0",
            "Outcome": "",
            "PORound": "0",
            "PaceAdjust": "N",
            "PerMode": "PerGame",
            "Period": "0",
            "PlayerExperience": "",
            "PlayerPosition": "",
            "PlusMinus": "N",
            "Rank": "N",
            "Season": season,
            "SeasonSegment": "",
            "SeasonType": season_type,
            "ShotClockRange": "",
            "StarterBench": "",
            "TeamID": "0",
            "TwoWay": "0",
            "VsConference": "",
            "VsDivision": ""
        }
        
        try:
            print(f"\nObteniendo estadísticas de jugadores para {season} ({season_type})...")
            
            # Intentar con un timeout más corto primero
            for timeout in [20, 30, 45, 60]:
                try:
                    data = self._make_request(
                        f"{self.base_url}{endpoint}",
                        params=params,
                        timeout=timeout
                    )
                    
                    if data and 'resultSets' in data:
                        print(f"✓ Datos obtenidos exitosamente con timeout de {timeout}s")
                        break
                    else:
                        print(f"× Intento con timeout={timeout}s falló, probando con timeout más largo...")
                except Exception as e:
                    print(f"× Error con timeout={timeout}s: {str(e)}")
                    if timeout == 60:  # último intento
                        raise
                    time.sleep(2)  # esperar antes del siguiente intento
            
            if not data or 'resultSets' not in data:
                print("No se encontró la estructura esperada en los datos")
                return pd.DataFrame()
            
            # Obtener los datos y encabezados
            headers = data['resultSets'][0]['headers']
            rows = data['resultSets'][0]['rowSet']
            
            # Verificar que hay datos
            if not rows:
                print("No se encontraron datos de jugadores")
                return pd.DataFrame()
            
            # Crear DataFrame
            df = pd.DataFrame(rows, columns=headers)
            
            return self._process_player_stats(df)
            
        except Exception as e:
            print(f"Error al obtener estadísticas de jugadores: {str(e)}")
            print("Intentando con configuración alternativa...")
            
            try:
                # Intentar con una configuración más básica
                alt_params = {
                    "LeagueID": "00",
                    "Season": season,
                    "SeasonType": season_type,
                    "PerMode": "PerGame"
                }
                
                data = self._make_request(
                    f"{self.base_url}{endpoint}",
                    params=alt_params,
                    timeout=60
                )
                
                if data and 'resultSets' in data:
                    df = pd.DataFrame(
                        data['resultSets'][0]['rowSet'],
                        columns=data['resultSets'][0]['headers']
                    )
                    return self._process_player_stats(df)
                    
            except Exception as e2:
                print(f"Error en intento alternativo: {str(e2)}")
            
            return pd.DataFrame()

    def get_team_stats(self, season: str = None, season_type: str = "Regular Season", vs_team_id: str = None) -> pd.DataFrame:
        """Obtiene estadísticas de equipos."""
        if season is None:
            season = self.current_season
            
        if not self._validate_season(season):
            print(f"Error: Temporada {season} inválida")
            return pd.DataFrame()
            
        endpoint = "leaguedashteamstats"
        params = {
            "MeasureType": "Base",
            "PerMode": "PerGame",
            "Season": season,  # Usar la temporada proporcionada o la actual
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
            print("\nObteniendo estadísticas de equipos...")
            response = self._make_request(
                f"{self.base_url}{endpoint}",
                params=params
            )
            
            if response.get('resultSets') is None:
                print("No se encontró la estructura esperada en los datos")
                return pd.DataFrame()
            
            df = pd.DataFrame(
                response['resultSets'][0]['rowSet'],
                columns=response['resultSets'][0]['headers']
            )
            
            return self._process_team_stats(df)
            
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            return pd.DataFrame()

    def _process_player_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Procesa las estadísticas de jugadores."""
        if df.empty:
            print("DataFrame vacío en _process_player_stats")
            return df
            
        try:
            print("\nProcesando estadísticas de jugadores")
            print("Dimensiones del DataFrame:", df.shape)
            print("Columnas antes del procesamiento:", df.columns.tolist())
            
            # Verificar que tenemos las columnas necesarias
            required_columns = ['PLAYER_ID', 'TEAM_ABBREVIATION']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"Faltan columnas requeridas: {missing_columns}")
                return df
            
            # Asegurarnos de que tenemos una columna de nombres
            if 'PLAYER_NAME' not in df.columns:
                print("Obteniendo nombres de jugadores...")
                try:
                    # Intentar obtener nombres de jugadores
                    endpoint_players = "commonallplayers"
                    params_players = {
                        "LeagueID": "00",
                        "Season": df['SEASON'].iloc[0] if 'SEASON' in df.columns else self.current_season,
                        "IsOnlyCurrentSeason": "1"
                    }
                    
                    response_players = self._make_request(
                        f"{self.base_url}commonallplayers",
                        params=params_players
                    )
                    
                    if response_players.get('resultSets') is not None:
                        df_players = pd.DataFrame(
                            response_players['resultSets'][0]['rowSet'],
                            columns=response_players['resultSets'][0]['headers']
                        )
                        # Crear diccionario de mapeo ID -> Nombre
                        player_names = dict(zip(df_players['PERSON_ID'], df_players['DISPLAY_FIRST_LAST']))
                        # Añadir columna de nombres
                        df['PLAYER_NAME'] = df['PLAYER_ID'].map(player_names)
                        print("Nombres de jugadores agregados correctamente")
                except Exception as e:
                    print(f"Error al obtener nombres de jugadores: {str(e)}")
            
            # Asegurarnos de que los nombres sean strings
            if 'PLAYER_NAME' in df.columns:
                df['PLAYER_NAME'] = df['PLAYER_NAME'].astype(str)
                df['PLAYER_NAME'] = df['PLAYER_NAME'].apply(lambda x: x.strip() if isinstance(x, str) else x)
            
            # Convertir columnas numéricas
            numeric_columns = ['MIN', 'PTS', 'AST', 'REB', 'STL', 'BLK', 'TOV', 'FG3M']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Crear estadísticas combinadas
            try:
                # Puntos + Asistencias
                if 'PTS' in df.columns and 'AST' in df.columns:
                    df['PTS_AST'] = df['PTS'] + df['AST']
                
                # Puntos + Rebotes
                if 'PTS' in df.columns and 'REB' in df.columns:
                    df['PTS_REB'] = df['PTS'] + df['REB']
                
                # Asistencias + Rebotes
                if 'AST' in df.columns and 'REB' in df.columns:
                    df['AST_REB'] = df['AST'] + df['REB']
                
                # Puntos + Asistencias + Rebotes
                if all(col in df.columns for col in ['PTS', 'AST', 'REB']):
                    df['PTS_AST_REB'] = df['PTS'] + df['AST'] + df['REB']
                
                # Robos + Bloqueos
                if 'STL' in df.columns and 'BLK' in df.columns:
                    df['STL_BLK'] = df['STL'] + df['BLK']
                
                print("\nEstadísticas combinadas creadas:")
                print("Nuevas columnas:", [col for col in df.columns if '_' in col])
                
            except Exception as e:
                print(f"Error al crear estadísticas combinadas: {str(e)}")
            
            print("\nDimensiones finales del DataFrame:", df.shape)
            return df
            
        except Exception as e:
            print(f"Error en _process_player_stats: {str(e)}")
            import traceback
            print("Traceback completo:")
            print(traceback.format_exc())
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
            "VsConference": "",
            "VsDivision": "",
            "PlayerID": player_id
        }
        
        try:
            # Usar el nuevo método _make_request
            data = self._make_request(
                f"{self.base_url}/{endpoint}",
                params=params
            )
            
            if not data or 'resultSets' not in data:
                print(f"No se encontraron datos para el jugador {player_id}")
                return pd.DataFrame()
                
            df = pd.DataFrame(
                data['resultSets'][0]['rowSet'],
                columns=data['resultSets'][0]['headers']
            )
            
            # Agregar columnas de temporada y tipo usando arrays del tamaño correcto
            df['SEASON'] = [season] * len(df)
            df['SEASON_TYPE'] = [season_type] * len(df)
            
            return df
            
        except Exception as e:
            print(f"Error al obtener logs de partidos: {str(e)}")
            return pd.DataFrame()

    def obtener_estadisticas_jugador_por_partido(self, equipo: str, jugador: str, temporada: Optional[str] = None, tipo_temporada: str = REGULAR_SEASON) -> pd.DataFrame:
        """
        Obtiene las estadísticas partido a partido de un jugador específico.
        
        Args:
            equipo: Nombre completo del equipo
            jugador: Nombre del jugador
            temporada: Temporada (ej: "2023-24")
            tipo_temporada: Tipo de temporada (Regular Season, Playoffs, etc)
        """
        print(f"\nBuscando estadísticas para {jugador} de {equipo}")
        
        # Primero obtenemos los datos del jugador
        df_equipo = self.obtener_estadisticas_jugadores_equipo(
            equipo=equipo,
            temporada=temporada,
            tipo_temporada=tipo_temporada
        )
        
        if df_equipo.empty:
            print("No se encontraron datos del equipo")
            return pd.DataFrame()
        
        # Buscar al jugador
        if 'PLAYER_NAME' not in df_equipo.columns:
            print("No se encontró la columna de nombres de jugadores")
            return pd.DataFrame()
        
        df_jugador = df_equipo[df_equipo['PLAYER_NAME'] == jugador]
        if df_jugador.empty:
            print(f"No se encontró al jugador {jugador}")
            return pd.DataFrame()
        
        # Obtener el ID del jugador
        if 'PLAYER_ID' not in df_jugador.columns:
            print("No se encontró el ID del jugador")
            return pd.DataFrame()
        
        player_id = str(df_jugador['PLAYER_ID'].iloc[0])
        print(f"ID del jugador encontrado: {player_id}")
        
        # Obtener los logs de partidos
        df = self.get_player_game_logs(
            player_id=player_id,
            season=temporada,
            season_type=tipo_temporada
        )
        
        if df.empty:
            print("No se encontraron logs de partidos")
            return df
        
        # Asegurarnos de que las columnas base sean numéricas
        columnas_base = ['PTS', 'AST', 'REB', 'STL', 'BLK']
        for col in columnas_base:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Crear columnas compuestas si no existen
        print("\nVerificando columnas compuestas...")
        
        # Puntos + Asistencias
        if 'PTS_AST' not in df.columns and all(col in df.columns for col in ['PTS', 'AST']):
            df['PTS_AST'] = df['PTS'] + df['AST']
            print("✓ Creada columna PTS_AST")
        
        # Puntos + Rebotes
        if 'PTS_REB' not in df.columns and all(col in df.columns for col in ['PTS', 'REB']):
            df['PTS_REB'] = df['PTS'] + df['REB']
            print("✓ Creada columna PTS_REB")
        
        # Asistencias + Rebotes
        if 'AST_REB' not in df.columns and all(col in df.columns for col in ['AST', 'REB']):
            df['AST_REB'] = df['AST'] + df['REB']
            print("✓ Creada columna AST_REB")
        
        # Puntos + Asistencias + Rebotes
        if 'PTS_AST_REB' not in df.columns and all(col in df.columns for col in ['PTS', 'AST', 'REB']):
            df['PTS_AST_REB'] = df['PTS'] + df['AST'] + df['REB']
            print("✓ Creada columna PTS_AST_REB")
        
        # Robos + Bloqueos
        if 'STL_BLK' not in df.columns and all(col in df.columns for col in ['STL', 'BLK']):
            df['STL_BLK'] = df['STL'] + df['BLK']
            print("✓ Creada columna STL_BLK")
        
        print("\nColumnas disponibles después de procesar:")
        print(df.columns.tolist())
        
        return df

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