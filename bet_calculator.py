"""
Módulo para calcular métricas relacionadas con apuestas deportivas.
Incluye cálculos de valor esperado, probabilidad implícita y valor real.
"""
from nba_stats import NBAStats
import pandas as pd
from typing import Dict, Optional, List, Tuple
from scipy import stats

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

def calcular_probabilidad_historica(df: pd.DataFrame, columna: str, umbral: float) -> Tuple[float, int, int]:
    """
    Calcula la probabilidad histórica basada en los datos reales.
    
    Args:
        df: DataFrame con las estadísticas
        columna: Nombre de la columna a evaluar
        umbral: Valor que se debe superar
        
    Returns:
        Tuple[float, int, int]: (probabilidad, veces_cumplido, total_partidos)
    """
    if df.empty:
        print("DataFrame vacío")
        return 0.0, 0, 0
    
    print("\nColumnas disponibles:", df.columns.tolist())
    
    # Mapeo de nombres comunes de estadísticas a columnas
    stat_mapping = {
        'Puntos': 'PTS',
        'Asistencias': 'AST',
        'Rebotes': 'REB',
        'Triples': 'FG3M',
        'PTS': 'PTS',
        'AST': 'AST',
        'REB': 'REB',
        'FG3M': 'FG3M'
    }
    
    # Buscar la columna correcta para la estadística
    stat_column = stat_mapping.get(columna)
    if not stat_column or stat_column not in df.columns:
        print(f"No se encontró la columna para {columna}")
        print(f"Columna buscada: {stat_column}")
        return 0.0, 0, 0
    
    if 'GP' not in df.columns:
        print("No se encontró la columna GP (partidos jugados)")
        return 0.0, 0, 0
    
    print(f"\nDatos del jugador:")
    print(df[[stat_column, 'GP']].to_string())
    
    # Obtener el valor de la estadística y partidos jugados
    valor_estadistica = df[stat_column].iloc[0]
    total_partidos = df['GP'].iloc[0]
    
    if total_partidos == 0:
        print("El jugador no ha jugado ningún partido")
        return 0.0, 0, 0
    
    # Calcular la probabilidad basada en el promedio
    probabilidad = valor_estadistica / umbral if umbral > 0 else 0
    probabilidad = min(0.95, max(0.05, probabilidad))  # Mantener entre 5% y 95%
    
    # Calcular el número estimado de partidos donde se superó el umbral
    veces_cumplido = int(round(probabilidad * total_partidos))
    
    # Mostrar datos históricos
    print(f"\nDatos históricos:")
    print(f"Promedio por partido: {valor_estadistica:.1f}")
    print(f"Partidos jugados: {total_partidos}")
    print(f"Umbral a superar: {umbral}")
    print(f"Estimación de partidos donde superó {umbral}: {veces_cumplido} de {total_partidos} ({(veces_cumplido/total_partidos)*100:.1f}%)")
    
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

def evaluar_prop_bet(stats: NBAStats, equipo: str, jugador: str, 
                     prop: str, umbral: float, cuota: float) -> str:
    """
    Evalúa una apuesta de tipo prop usando datos históricos.
    """
    print(f"\nBuscando datos para:")
    print(f"Equipo: {equipo}")
    print(f"Jugador: {jugador}")
    print(f"Estadística: {prop}")
    
    datos = stats.obtener_estadisticas_jugadores_equipo(equipo, None)
    
    if datos.empty:
        return "No hay datos disponibles para este equipo."
    
    # Encontrar la columna correcta para nombres de jugadores
    player_column = None
    for col in datos.columns:
        if 'PLAYER_NAME' in col:
            player_column = col
            break
    
    if not player_column:
        for col in datos.columns:
            if 'PLAYER' in col or 'NAME' in col:
                player_column = col
                break
    
    if not player_column:
        return "Error: No se pudo encontrar la columna con nombres de jugadores."
    
    print(f"\nJugadores disponibles en {equipo}:")
    jugadores = sorted(datos[player_column].unique().tolist())
    for idx, nombre in enumerate(jugadores, 1):
        print(f"{idx}. {nombre}")
    
    # Buscar coincidencia exacta primero
    datos_jugador = datos[datos[player_column] == jugador]
    
    # Si no hay coincidencia exacta, buscar coincidencia parcial
    if datos_jugador.empty:
        print(f"\nNo se encontró coincidencia exacta para '{jugador}'. Buscando coincidencias parciales...")
        for nombre_completo in jugadores:
            if jugador.lower() in nombre_completo.lower():
                print(f"¿Querías decir '{nombre_completo}'?")
                datos_jugador = datos[datos[player_column] == nombre_completo]
                jugador = nombre_completo
                break
    
    if datos_jugador.empty:
        return f"No se encontró al jugador '{jugador}' en el equipo {equipo}.\nJugadores disponibles:\n" + "\n".join([f"- {j}" for j in jugadores])
    
    probabilidad, veces_cumplido, total_partidos = calcular_probabilidad_historica(datos_jugador, prop, umbral)
    
    # Valor esperado simple: probabilidad * ganancia - (1-probabilidad) * pérdida
    # Donde ganancia = cuota - 1, y pérdida = 1
    valor_esperado = probabilidad * (cuota - 1) - (1 - probabilidad) * 1
    
    analisis = f"""
Análisis de la Apuesta:
----------------------
Jugador: {jugador}
Estadística: {prop}
Umbral: {umbral}
Cuota: {cuota}

Datos Históricos:
---------------
Promedio: {datos_jugador[prop].iloc[0]:.1f}
Partidos jugados: {total_partidos}
Veces que superó {umbral}: {veces_cumplido} de {total_partidos} ({(veces_cumplido/total_partidos)*100:.1f}%)
Probabilidad histórica: {probabilidad:.1%}

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