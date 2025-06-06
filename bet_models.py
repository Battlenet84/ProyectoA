"""
Módulo para modelos bayesianos y simulaciones de Monte Carlo para predicción de props en la NBA.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from scipy import stats
from nba_stats import NBAStats
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BayesianPropPredictor:
    """
    Clase para predecir props de jugadores usando simulaciones de Monte Carlo.
    """
    
    def __init__(self):
        """Inicializa el predictor con configuraciones por defecto."""
        self.stats = NBAStats()
        self.n_simulaciones = 10000
        self.seed = 42
        np.random.seed(self.seed)
        
        # Mapeo de props a columnas de datos
        self.prop_mapping = {
            'Puntos': 'PTS',
            'Asistencias': 'AST',
            'Rebotes': 'REB',
            'Triples': 'FG3M',
            'Robos': 'STL',
            'Tapones': 'BLK',
            'Pérdidas': 'TOV'
        }
        
    def _validar_entrada(self, equipo: str, jugador: str, tipo_prop: str, linea: float) -> None:
        """
        Valida los datos de entrada.
        """
        if not isinstance(equipo, str) or not equipo:
            raise ValueError("El equipo debe ser una cadena no vacía")
        if not isinstance(jugador, str) or not jugador:
            raise ValueError("El jugador debe ser una cadena no vacía")
        if tipo_prop not in self.prop_mapping:
            raise ValueError(f"Tipo de prop no válido. Opciones válidas: {list(self.prop_mapping.keys())}")
        if not isinstance(linea, (int, float)) or linea < 0:
            raise ValueError("La línea debe ser un número no negativo")
            
    def _obtener_datos_historicos(self, equipo: str, jugador: str, tipo_prop: str) -> pd.Series:
        """
        Obtiene los datos históricos del jugador para la prop especificada.
        """
        try:
            logger.info(f"Obteniendo datos históricos para {jugador} ({equipo}) - {tipo_prop}")
            
            # Primero obtenemos los datos generales del jugador para obtener su ID
            datos_generales = self.stats.obtener_estadisticas_jugadores_equipo(equipo)
            
            if datos_generales.empty:
                raise ValueError(f"No se encontraron datos para el equipo {equipo}")
            
            # Asegurarnos que los nombres estén limpios
            datos_generales['PLAYER_NAME'] = datos_generales['PLAYER_NAME'].astype(str).str.strip()
            
            # Filtrar por jugador
            datos_jugador = datos_generales[datos_generales['PLAYER_NAME'] == jugador]
            
            if datos_jugador.empty:
                # Intentar búsqueda parcial
                jugadores_similares = datos_generales[datos_generales['PLAYER_NAME'].str.contains(jugador, case=False, na=False)]
                if not jugadores_similares.empty:
                    sugerencias = jugadores_similares['PLAYER_NAME'].unique().tolist()
                    raise ValueError(f"No se encontró exactamente '{jugador}'. ¿Quisiste decir alguno de estos? {sugerencias}")
                raise ValueError(f"No se encontraron datos para el jugador {jugador}")
            
            # Obtener el ID del jugador
            if 'PLAYER_ID' not in datos_jugador.columns:
                raise ValueError("No se encontró el ID del jugador en los datos")
            
            player_id = str(datos_jugador['PLAYER_ID'].iloc[0])
            
            # Obtener datos partido a partido
            datos_partidos = self.stats.get_player_game_logs(player_id=player_id)
            
            if datos_partidos.empty:
                raise ValueError(f"No se encontraron datos partido a partido para {jugador}")
            
            # Obtener la columna correcta para la prop
            columna = self.prop_mapping.get(tipo_prop)
            if not columna:
                raise ValueError(f"Tipo de prop no válido: {tipo_prop}")
            
            if columna not in datos_partidos.columns:
                raise ValueError(f"No se encontró la columna {columna} para la prop {tipo_prop}")
            
            # Convertir a float y manejar valores no válidos
            datos_prop = pd.to_numeric(datos_partidos[columna], errors='coerce')
            datos_prop = datos_prop.dropna()
            
            if datos_prop.empty:
                raise ValueError(f"No hay datos válidos para {tipo_prop}")
            
            if len(datos_prop) < 2:
                raise ValueError(f"Se necesitan al menos 2 partidos para analizar. Solo se encontraron {len(datos_prop)} partidos.")
            
            logger.info(f"Datos obtenidos exitosamente: {len(datos_prop)} partidos")
            return datos_prop
            
        except Exception as e:
            logger.error(f"Error al obtener datos históricos: {str(e)}")
            raise
        
    def _simular_valores(self, datos: pd.Series, n_sims: Optional[int] = None) -> np.ndarray:
        """
        Realiza simulaciones de Monte Carlo usando una distribución normal truncada.
        """
        try:
            if n_sims is None:
                n_sims = self.n_simulaciones
            
            if len(datos) < 2:
                raise ValueError("Se necesitan al menos 2 datos para realizar simulaciones")
            
            # Calcular estadísticas
            media = datos.mean()
            std = datos.std()
            
            if std == 0:
                logger.warning("Desviación estándar es 0, usando valor mínimo")
                std = 0.1
            
            # Usar una distribución normal truncada para evitar valores negativos
            lower_bound = 0
            upper_bound = media + 4*std  # Límite superior razonable
            
            # Generar simulaciones
            simulaciones = stats.truncnorm(
                (lower_bound - media) / std,
                (upper_bound - media) / std,
                loc=media,
                scale=std
            ).rvs(size=n_sims)
            
            logger.info(f"Simulaciones generadas: media={simulaciones.mean():.2f}, std={simulaciones.std():.2f}")
            return simulaciones
            
        except Exception as e:
            logger.error(f"Error en simulación: {str(e)}")
            raise
        
    def analizar_prop(self, equipo: str, jugador: str, tipo_prop: str, 
                     linea: float, cuota: float, es_over: bool = True) -> Dict:
        """
        Analiza una prop usando simulaciones de Monte Carlo.
        
        Args:
            equipo: Nombre del equipo
            jugador: Nombre del jugador
            tipo_prop: Tipo de prop (Puntos, Asistencias, etc)
            linea: Línea de la prop
            cuota: Cuota ofrecida por la casa de apuestas
            es_over: Si es True, analiza probabilidad de over. Si es False, de under.
            
        Returns:
            Dict con resultados del análisis
        """
        try:
            # Validar entrada
            self._validar_entrada(equipo, jugador, tipo_prop, linea)
            if not isinstance(cuota, (int, float)) or cuota <= 1:
                raise ValueError("La cuota debe ser un número mayor a 1")
            
            # Obtener datos históricos
            datos = self._obtener_datos_historicos(equipo, jugador, tipo_prop)
            
            # Realizar simulaciones
            simulaciones = self._simular_valores(datos)
            
            # Calcular probabilidad
            if es_over:
                prob = (simulaciones > linea).mean()
            else:
                prob = (simulaciones < linea).mean()
            
            # Calcular intervalo de confianza del 95%
            intervalo = np.percentile(simulaciones, [2.5, 97.5])
            
            # Calcular valor esperado de la estadística
            valor_esperado_stat = simulaciones.mean()
            
            # Calcular métricas adicionales
            desviacion = simulaciones.std()
            mediana = np.median(simulaciones)
            
            # Calcular métricas de apuesta
            prob_implicita = 1 / cuota
            ganancia_potencial = cuota - 1  # Por unidad apostada
            valor_esperado_apuesta = (prob * ganancia_potencial) - ((1 - prob) * 1)  # -1 es la pérdida por unidad
            porcentaje_valor = ((prob - prob_implicita) / prob_implicita) * 100
            
            resultado = {
                'probabilidad': prob,
                'valor_esperado_stat': valor_esperado_stat,
                'intervalo_confianza': intervalo,
                'simulaciones': simulaciones,
                'mediana': mediana,
                'desviacion': desviacion,
                'n_simulaciones': len(simulaciones),
                'datos_historicos': {
                    'media': datos.mean(),
                    'mediana': datos.median(),
                    'std': datos.std(),
                    'n_registros': len(datos)
                },
                'metricas_apuesta': {
                    'cuota': cuota,
                    'prob_implicita': prob_implicita,
                    'ganancia_potencial': ganancia_potencial,
                    'valor_esperado': valor_esperado_apuesta,
                    'porcentaje_valor': porcentaje_valor,
                    'kelly': (prob * cuota - 1) / (cuota - 1) if cuota > 1 else 0  # Criterio de Kelly
                }
            }
            
            logger.info(f"Análisis completado para {jugador} - {tipo_prop}")
            return resultado
            
        except Exception as e:
            logger.error(f"Error en análisis de prop: {str(e)}")
            raise 