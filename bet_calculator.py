"""
Módulo para calcular métricas relacionadas con apuestas deportivas.
Incluye cálculos de valor esperado, probabilidad implícita y valor real.
"""
from nba_stats import NBAStats
import pandas as pd
from typing import Dict, Optional, List, Tuple

def calcular_probabilidad_implicita(cuota: float) -> float:
    """
    Calcula la probabilidad implícita a partir de una cuota decimal.
    
    Args:
        cuota: La cuota decimal (ej: 2.5 significa que por cada $1 apostado se ganan $2.5)
        
    Returns:
        float: Probabilidad implícita (entre 0 y 1)
    """
    return 1 / cuota

def calcular_valor_esperado(cuota: float, prob_real: float, monto: float) -> dict:
    """
    Calcula el valor esperado de una apuesta.
    
    Args:
        cuota: La cuota decimal ofrecida por la casa de apuestas
        prob_real: La probabilidad real estimada del evento (entre 0 y 1)
        monto: Cantidad de dinero a apostar
        
    Returns:
        dict: Diccionario con el valor esperado y métricas adicionales
    """
    prob_implicita = calcular_probabilidad_implicita(cuota)
    
    # Ganancia potencial
    ganancia_potencial = monto * (cuota - 1)
    
    # Valor esperado = (probabilidad * ganancia) - (probabilidad_perder * monto)
    valor_esperado = (prob_real * ganancia_potencial) - ((1 - prob_real) * monto)
    
    # Porcentaje de valor
    porcentaje_valor = ((prob_real - prob_implicita) / prob_implicita) * 100
    
    return {
        "valor_esperado": round(valor_esperado, 2),
        "ganancia_potencial": round(ganancia_potencial, 2),
        "prob_implicita": round(prob_implicita * 100, 2),
        "prob_real": round(prob_real * 100, 2),
        "porcentaje_valor": round(porcentaje_valor, 2)
    }

def get_column_mapping(df: pd.DataFrame) -> Dict[str, str]:
    """
    Obtiene un mapeo de nombres de columnas estándar a las columnas reales del DataFrame.
    """
    column_mapping = {}
    for col in df.columns:
        if 'PLAYER' in col or 'NAME' in col:
            column_mapping['PLAYER_NAME'] = col
        elif col == 'GP' or 'GAMES' in col:
            column_mapping['GP'] = col
        elif col == 'PTS' or 'POINTS' in col:
            column_mapping['PTS'] = col
        # Agregar más mapeos según sea necesario
    return column_mapping

def calcular_estadistica_combinada(df: pd.DataFrame, stats: List[str]) -> pd.Series:
    """
    Calcula una estadística combinada sumando varias columnas.
    
    Args:
        df: DataFrame con las estadísticas
        stats: Lista de columnas a sumar
        
    Returns:
        pd.Series: Serie con la suma de las estadísticas
    """
    # Verificar que todas las columnas existen
    for stat in stats:
        if stat not in df.columns:
            raise ValueError(f"No se encontró la columna {stat}")
    
    # Sumar las columnas
    return df[stats].sum(axis=1)

def calcular_probabilidad_historica(df: pd.DataFrame, columna: str, umbral: float, es_over: bool = True, 
                                filtro_local: str = "Todos los partidos") -> Tuple[float, int, int]:
    """
    Calcula la probabilidad histórica basada en los datos reales.
    
    Args:
        df: DataFrame con las estadísticas partido a partido
        columna: Nombre de la columna a evaluar o lista de columnas para props combinadas
        umbral: Valor que se debe superar o no superar
        es_over: Si es True, calcula probabilidad de superar el umbral. Si es False, de quedar por debajo.
        filtro_local: "Todos los partidos", "Solo Local" o "Solo Visitante"
        
    Returns:
        Tuple[float, int, int]: (probabilidad, veces_cumplido, total_partidos)
    """
    if df.empty:
        print("DataFrame vacío")
        return 0.0, 0, 0
    
    print("\nColumnas disponibles:", df.columns.tolist())
    
    # Aplicar filtro de local/visitante si es necesario
    if filtro_local != "Todos los partidos":
        if 'LOCATION' not in df.columns and 'MATCHUP' in df.columns:
            # Si no tenemos columna LOCATION pero sí MATCHUP, la creamos
            df['LOCATION'] = df['MATCHUP'].apply(lambda x: 'Home' if '@' not in x else 'Away')
        
        if 'LOCATION' in df.columns:
            es_local = filtro_local == "Solo Local"
            df = df[df['LOCATION'] == ('Home' if es_local else 'Away')]
            if df.empty:
                print(f"No hay datos para partidos {filtro_local.lower()}")
                return 0.0, 0, 0
    
    # Verificar que la columna existe
    if columna not in df.columns:
        print(f"No se encontró la columna {columna}")
        return 0.0, 0, 0
    
    # Asegurarnos de que no haya valores nulos
    # Para estadísticas acumulativas (puntos, rebotes, etc.), los nulos son 0
    # Para porcentajes, los nulos se eliminan
    if columna in ['PTS', 'AST', 'REB', 'STL', 'BLK', 'TOV', 'FG3M', 
                   'PTS_AST', 'PTS_REB', 'AST_REB', 'PTS_AST_REB', 'STL_BLK']:
        df[columna] = df[columna].fillna(0)
    else:
        df = df.dropna(subset=[columna])
    
    # Convertir la columna a numérica si no lo es
    try:
        df[columna] = pd.to_numeric(df[columna], errors='coerce')
        df = df.dropna(subset=[columna])  # Eliminar cualquier valor que no se pudo convertir
    except Exception as e:
        print(f"Error al convertir valores a numéricos: {str(e)}")
        return 0.0, 0, 0
    
    # Asegurarnos de que el umbral sea numérico
    try:
        umbral = float(umbral)
    except (TypeError, ValueError):
        print(f"Error: El umbral {umbral} no es un número válido")
        return 0.0, 0, 0
    
    # Obtener los valores válidos y asegurarnos de que son números
    valores = pd.to_numeric(df[columna], errors='coerce')
    valores = valores.dropna()
    
    # Verificar que tenemos datos
    total_partidos = len(valores)
    if total_partidos == 0:
        print("No hay datos válidos para analizar")
        return 0.0, 0, 0
    
    # Calcular veces que cumplió la condición
    try:
        if es_over:
            veces_cumplido = len(valores[valores > umbral])  # Estrictamente mayor para over
        else:
            veces_cumplido = len(valores[valores < umbral])  # Estrictamente menor para under
    except Exception as e:
        print(f"Error al comparar valores: {str(e)}")
        return 0.0, 0, 0
    
    probabilidad = veces_cumplido / total_partidos if total_partidos > 0 else 0.0
    
    # Mostrar datos históricos
    print(f"\nDatos históricos ({filtro_local}):")
    print(f"Promedio por partido: {valores.mean():.1f}")
    print(f"Partidos jugados: {total_partidos}")
    print(f"{'Línea a superar' if es_over else 'Línea a no superar'}: {umbral}")
    print(f"Veces que {'superó' if es_over else 'quedó bajo'} {umbral}: {veces_cumplido} de {total_partidos} ({probabilidad*100:.1f}%)")
    
    return probabilidad, veces_cumplido, total_partidos

def obtener_probabilidad_prop(stats: NBAStats, equipo: str, jugador: Optional[str], 
                            prop: str, umbral: float, vs_equipo: Optional[str] = None) -> Dict:
    """
    Obtiene la probabilidad histórica para una prop específica.
    
    Args:
        stats: Instancia de NBAStats
        equipo: Nombre del equipo
        jugador: Nombre del jugador (opcional)
        prop: Nombre de la estadística (ej: 'PTS', 'AST')
        umbral: Valor que se debe superar
        vs_equipo: Equipo rival (opcional)
        
    Returns:
        Dict: Diccionario con la probabilidad y detalles adicionales
    """
    if jugador:
        # Obtener estadísticas del jugador
        df = stats.obtener_estadisticas_jugadores_equipo(equipo, [vs_equipo] if vs_equipo else None)
        if df.empty:
            return {
                "probabilidad": 0.0,
                "veces_cumplido": 0,
                "total_partidos": 0,
                "tipo": "jugador",
                "nombre": jugador,
                "vs_equipo": vs_equipo,
                "prop": prop,
                "umbral": umbral
            }
            
        # Obtener mapeo de columnas
        column_mapping = get_column_mapping(df)
        player_name_col = column_mapping.get('PLAYER_NAME')
        
        if not player_name_col:
            print("No se encontró la columna con nombres de jugadores")
            return {
                "probabilidad": 0.0,
                "veces_cumplido": 0,
                "total_partidos": 0,
                "tipo": "jugador",
                "nombre": jugador,
                "vs_equipo": vs_equipo,
                "prop": prop,
                "umbral": umbral
            }
            
        df = df[df[player_name_col] == jugador]
    else:
        # Obtener estadísticas del equipo
        df = stats.obtener_estadisticas_equipo(equipo, [vs_equipo] if vs_equipo else None)
    
    prob, cumplidos, total = calcular_probabilidad_historica(df, prop, umbral)
    
    return {
        "probabilidad": prob,
        "veces_cumplido": cumplidos,
        "total_partidos": total,
        "tipo": "jugador" if jugador else "equipo",
        "nombre": jugador if jugador else equipo,
        "vs_equipo": vs_equipo,
        "prop": prop,
        "umbral": umbral
    }

def _normalize_name(name: str) -> str:
    """
    Normaliza un nombre para hacer las comparaciones más robustas.
    Elimina espacios extra, puntos, y convierte a minúsculas.
    """
    return name.lower().replace('.', '').strip()

def _find_matching_player(jugadores_disponibles: List[str], jugador_buscado: str) -> Optional[str]:
    """
    Busca un jugador en la lista de jugadores disponibles, usando coincidencia parcial si es necesario.
    """
    jugador_norm = _normalize_name(jugador_buscado)
    
    # Primero intentar coincidencia exacta
    for jugador in jugadores_disponibles:
        if _normalize_name(jugador) == jugador_norm:
            return jugador
    
    # Si no hay coincidencia exacta, buscar coincidencia parcial
    for jugador in jugadores_disponibles:
        if jugador_norm in _normalize_name(jugador):
            return jugador
        # También buscar si el nombre buscado contiene el nombre disponible
        if _normalize_name(jugador) in jugador_norm:
            return jugador
    
    return None

def evaluar_prop_bet(stats: NBAStats, equipo: str, jugador: str, 
                     prop: str, umbral: float, cuota: float,
                     temporada: Optional[str] = None, tipo_temporada: str = "Regular Season",
                     es_over: bool = True, filtro_local: str = "Todos los partidos") -> str:
    """
    Evalúa una apuesta de tipo prop usando datos históricos partido a partido.
    
    Args:
        stats: Instancia de NBAStats
        equipo: Nombre del equipo
        jugador: Nombre del jugador
        prop: Tipo de prop (Puntos, Asistencias, etc)
        umbral: Valor a superar o no superar
        cuota: Cuota ofrecida
        temporada: Temporada a analizar (ej: "2023-24")
        tipo_temporada: Tipo de temporada (Regular Season, Playoffs, etc)
        es_over: Si es True, la apuesta es a superar el umbral. Si es False, a quedar por debajo.
        filtro_local: "Todos los partidos", "Solo Local" o "Solo Visitante"
    """
    print(f"\nBuscando datos para:")
    print(f"Equipo: {equipo}")
    print(f"Jugador: {jugador}")
    print(f"Estadística: {prop}")
    print(f"Temporada: {temporada}")
    print(f"Tipo: {tipo_temporada}")
    print(f"Tipo de apuesta: {'Más de' if es_over else 'Menos de'} {umbral}")
    print(f"Filtro de localía: {filtro_local}")
    
    # Obtener datos generales primero
    df_jugadores = pd.DataFrame()
    
    # Si tipo_temporada es una lista, obtener datos para cada tipo
    tipos_temporada = tipo_temporada if isinstance(tipo_temporada, list) else [tipo_temporada]
    
    for tipo in tipos_temporada:
        df_temp = stats.obtener_estadisticas_jugadores_equipo(
            equipo=equipo,
            rivales=None,
            temporada=temporada,
            tipo_temporada=tipo
        )
        
        if not df_temp.empty:
            df_temp['TIPO_TEMPORADA'] = tipo
            df_jugadores = pd.concat([df_jugadores, df_temp], ignore_index=True)
    
    if df_jugadores.empty:
        return "No hay datos disponibles para este equipo."
    
    # Verificar que tenemos las columnas necesarias
    if 'PLAYER_NAME' not in df_jugadores.columns or 'PLAYER_ID' not in df_jugadores.columns:
        return "Error: No se encontraron las columnas PLAYER_NAME o PLAYER_ID en los datos."
    
    # Asegurarnos que los nombres sean strings y estén limpios
    df_jugadores['PLAYER_NAME'] = df_jugadores['PLAYER_NAME'].astype(str).apply(lambda x: x.strip())
    
    print(f"\nJugadores disponibles en {equipo}:")
    jugadores = sorted(df_jugadores['PLAYER_NAME'].unique().tolist())
    for idx, nombre in enumerate(jugadores, 1):
        print(f"{idx}. {nombre}")
    
    # Buscar coincidencia del jugador usando la función de coincidencia
    nombre_encontrado = _find_matching_player(jugadores, jugador)
    if not nombre_encontrado:
        return f"No se encontró al jugador '{jugador}' en el equipo {equipo}.\nJugadores disponibles:\n" + "\n".join([f"- {j}" for j in jugadores])
    
    print(f"\nJugador encontrado: {nombre_encontrado}")
    datos_jugador = df_jugadores[df_jugadores['PLAYER_NAME'] == nombre_encontrado]
    
    # Obtener el ID del jugador
    player_id = str(datos_jugador['PLAYER_ID'].iloc[0])
    
    # Inicializar DataFrame para acumular datos partido a partido
    datos_partidos = pd.DataFrame()
    
    # Obtener datos partido a partido para cada tipo de temporada
    for tipo in tipos_temporada:
        df_temp = stats.get_player_game_logs(
            player_id=player_id,
            season=temporada,
            season_type=tipo
        )
        
        if not df_temp.empty:
            df_temp['TIPO_TEMPORADA'] = tipo
            datos_partidos = pd.concat([datos_partidos, df_temp], ignore_index=True)
    
    if datos_partidos.empty:
        return f"No se encontraron datos partido a partido para {nombre_encontrado}"
    
    # Mapeo de nombres de estadísticas para datos partido a partido
    stat_mapping = {
        # Estadísticas básicas
        'Puntos': 'PTS',
        'Asistencias': 'AST',
        'Rebotes': 'REB',
        'Triples': 'FG3M',
        'Robos': 'STL',
        'Tapones': 'BLK',
        'Bloqueos': 'BLK',
        'Pérdidas': 'TOV',
        'Pérdidas de balón': 'TOV',
        
        # Props combinadas - versión española
        'Puntos + Asistencias': 'PTS_AST',
        'Puntos y Asistencias': 'PTS_AST',
        'Puntos más Asistencias': 'PTS_AST',
        
        'Puntos + Rebotes': 'PTS_REB',
        'Puntos y Rebotes': 'PTS_REB',
        'Puntos más Rebotes': 'PTS_REB',
        
        'Asistencias + Rebotes': 'AST_REB',
        'Asistencias y Rebotes': 'AST_REB',
        'Asistencias más Rebotes': 'AST_REB',
        
        'Puntos + Asistencias + Rebotes': 'PTS_AST_REB',
        'Puntos, Asistencias y Rebotes': 'PTS_AST_REB',
        'Puntos más Asistencias más Rebotes': 'PTS_AST_REB',
        
        'Tapones + Robos': 'STL_BLK',
        'Tapones y Robos': 'STL_BLK',
        'Tapones más Robos': 'STL_BLK',
        'Bloqueos + Robos': 'STL_BLK',
        'Bloqueos y Robos': 'STL_BLK',
        'Bloqueos más Robos': 'STL_BLK',
        
        # Props combinadas - versión inglesa
        'Points': 'PTS',
        'Assists': 'AST',
        'Rebounds': 'REB',
        'Threes': 'FG3M',
        'Steals': 'STL',
        'Blocks': 'BLK',
        'Turnovers': 'TOV',
        
        'Points + Assists': 'PTS_AST',
        'Points and Assists': 'PTS_AST',
        'Points & Assists': 'PTS_AST',
        
        'Points + Rebounds': 'PTS_REB',
        'Points and Rebounds': 'PTS_REB',
        'Points & Rebounds': 'PTS_REB',
        
        'Assists + Rebounds': 'AST_REB',
        'Assists and Rebounds': 'AST_REB',
        'Assists & Rebounds': 'AST_REB',
        
        'Points + Assists + Rebounds': 'PTS_AST_REB',
        'Points, Assists and Rebounds': 'PTS_AST_REB',
        'Points, Assists & Rebounds': 'PTS_AST_REB',
        
        'Blocks + Steals': 'STL_BLK',
        'Blocks and Steals': 'STL_BLK',
        'Blocks & Steals': 'STL_BLK',
        
        # Versiones cortas
        'PTS': 'PTS',
        'AST': 'AST',
        'REB': 'REB',
        'FG3M': 'FG3M',
        'STL': 'STL',
        'BLK': 'BLK',
        'TOV': 'TOV',
        'PTS+AST': 'PTS_AST',
        'PTS_AST': 'PTS_AST',
        'PTS+REB': 'PTS_REB',
        'PTS_REB': 'PTS_REB',
        'AST+REB': 'AST_REB',
        'AST_REB': 'AST_REB',
        'PTS+AST+REB': 'PTS_AST_REB',
        'PTS_AST_REB': 'PTS_AST_REB',
        'STL+BLK': 'STL_BLK',
        'STL_BLK': 'STL_BLK'
    }

    # Buscar la columna o columnas correctas para la estadística
    stat_columns = stat_mapping.get(prop)
    if not stat_columns:
        # Intentar normalizar el nombre de la prop
        prop_normalizada = prop.replace(' + ', '_').replace('+', '_').replace(' ', '_').upper()
        stat_columns = stat_mapping.get(prop_normalizada)
        
        if not stat_columns:
            # Intentar buscar coincidencia parcial
            for key in stat_mapping:
                if _normalize_name(key) == _normalize_name(prop):
                    stat_columns = stat_mapping[key]
                    break
        
        if not stat_columns:
            columnas_disponibles = datos_partidos.columns.tolist()
            return f"No se encontró la columna para la estadística {prop}. Columnas disponibles: {columnas_disponibles}"
    
    # Verificar que la columna existe
    if stat_columns not in datos_partidos.columns:
        # Si es una prop combinada, intentar crearla
        if '_' in stat_columns:
            stats_base = stat_columns.split('_')
            if all(stat in datos_partidos.columns for stat in stats_base):
                print(f"\nCreando columna combinada {stat_columns} a partir de {stats_base}")
                # Crear la columna combinada
                datos_partidos[stat_columns] = datos_partidos[stats_base].sum(axis=1)
                print(f"✓ Columna {stat_columns} creada exitosamente")
            else:
                missing_stats = [stat for stat in stats_base if stat not in datos_partidos.columns]
                return f"No se encontraron las columnas base necesarias: {missing_stats}"
        else:
            return f"No se encontró la columna {stat_columns} necesaria para {prop}"
    
    # Asegurarnos de que los valores nulos sean 0
    datos_partidos[stat_columns] = datos_partidos[stat_columns].fillna(0)
    
    probabilidad, veces_cumplido, total_partidos = calcular_probabilidad_historica(
        datos_partidos, 
        stat_columns, 
        umbral,
        es_over,
        filtro_local
    )
    
    if probabilidad == 0 and total_partidos == 0:
        return f"No hay suficientes datos para analizar {prop}"
    
    # Obtener el promedio
    promedio = datos_partidos[stat_columns].mean()
    
    # Valor esperado simple: probabilidad * ganancia - (1-probabilidad) * pérdida
    # Donde ganancia = cuota - 1, y pérdida = 1
    valor_esperado = probabilidad * (cuota - 1) - (1 - probabilidad) * 1
    
    # Obtener desglose por tipo de temporada
    desglose = ""
    for tipo in tipos_temporada:
        df_tipo = datos_partidos[datos_partidos['TIPO_TEMPORADA'] == tipo]
        if not df_tipo.empty:
            prob_tipo, cumplido_tipo, total_tipo = calcular_probabilidad_historica(
                df_tipo, 
                stat_columns, 
                umbral,
                es_over,
                filtro_local
            )
            promedio_tipo = df_tipo[stat_columns].mean()
            desglose += f"\n{tipo}:"
            desglose += f"\n- Promedio: {promedio_tipo:.1f}"
            desglose += f"\n- Cumplió: {cumplido_tipo} de {total_tipo} ({prob_tipo*100:.1f}%)"
    
    analisis = f"""
Análisis de la Apuesta:
----------------------
Jugador: {nombre_encontrado}
Estadística: {prop}
Tipo de Apuesta: {'Más' if es_over else 'Menos'} de {umbral}
Cuota: {cuota}
Temporada: {temporada if temporada else 'Actual'}
Tipos: {', '.join(tipos_temporada)}
Filtro: {filtro_local}

Datos Históricos:
---------------
Promedio por partido: {promedio:.1f}
Partidos jugados: {total_partidos}
Veces que {'superó' if es_over else 'quedó bajo'} {umbral}: {veces_cumplido} de {total_partidos} ({(veces_cumplido/total_partidos)*100:.1f}%)
Probabilidad histórica: {probabilidad:.1%}

Desglose por Tipo de Temporada:
{desglose}

Análisis de Valor:
----------------
Valor esperado por unidad apostada: {valor_esperado:.2f}
Recomendación: {'✅ APOSTAR' if valor_esperado > 0 else '❌ NO APOSTAR'}

Resumen de la apuesta:
--------------------
- Si apuestas 1 unidad:
  * Ganancia si aciertas: {cuota - 1:.2f} unidades
  * Pérdida si fallas: 1 unidad
  * Valor esperado: {valor_esperado:.2f} unidades
"""
    return analisis

if __name__ == "__main__":
    # Ejemplo de uso
    nba = NBAStats()
    
    # Ejemplo: Evaluar si Tatum anota más de 30 puntos contra los Lakers
    equipo = "Boston Celtics"
    jugador = "Jayson Tatum"
    prop = "Puntos"
    umbral = 30
    cuota = 2.5
    monto = 100
    vs_equipo = "Los Angeles Lakers"
    
    print(evaluar_prop_bet(nba, equipo, jugador, prop, umbral, cuota)) 