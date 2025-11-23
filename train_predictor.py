"""
Script standalone para entrenar y evaluar modelo predictivo LSTM
Predice PM2.5 y PM10 para ventanas de 1, 3 y 5 horas

Uso:
    python train_predictor.py
"""

import os
import sys
from modules.data_processor import DataProcessor
from modules.predictive_model import PredictiveModelPipeline
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def main():
    print("\n" + "="*80)
    print("🔬 MODELO PREDICTIVO LSTM - SOLO DATOS DE RMCAB")
    print("="*80)

    # Paso 1: Cargar datos RMCAB (TODO EL AÑO 2025)
    print("\n[PASO 1] Cargando datos REALES de RMCAB (TODO EL AÑO 2025)...")
    print("-"*80)

    data_processor = DataProcessor()

    try:
        # Cargar SOLO datos de RMCAB desde CSV
        print("\n→ Cargando datos REALES de RMCAB (estación de referencia)...")
        print("  (Espera: esto incluye todos los datos disponibles en 2025)")
        rmcab_df = data_processor.load_rmcab_from_csv()

        if rmcab_df is None or rmcab_df.empty:
            print("[ERROR] No se pudieron cargar datos de RMCAB")
            print("Asegúrate de que data_rmcab/rmcab_data.csv existe")
            return

        # Agregar simulación de temperatura y humedad
        print("\n→ Agregando Temperatura y Humedad (simuladas con patrón Bogotá)...")
        rmcab_df = data_processor._simulate_environmental_data(rmcab_df)

        print("\n✅ Datos preparados:")
        print(f"   - Total registros: {len(rmcab_df)}")
        print(f"   - Período: {rmcab_df['datetime'].min()} a {rmcab_df['datetime'].max()}")
        print(f"   - PM2.5: {rmcab_df['pm25_ref'].notna().sum()} valores válidos")
        print(f"   - PM10: {rmcab_df['pm10_ref'].notna().sum()} valores válidos")
        print(f"   - Temperatura: {rmcab_df['temperature'].min():.1f}°C a {rmcab_df['temperature'].max():.1f}°C")
        print(f"   - Humedad: {rmcab_df['rh'].min():.1f}% a {rmcab_df['rh'].max():.1f}%")

    except Exception as e:
        print(f"[ERROR] Error al cargar datos: {e}")
        print("\nAsegúrate de:")
        print("  1. Tener el archivo: data_rmcab/rmcab_data.csv")
        print("     (Descargado previamente con Postman)")
        import traceback
        traceback.print_exc()
        return

    # Paso 2: Entrenar modelo
    print("\n" + "="*80)
    print("[PASO 2] Entrenando modelo predictivo con datos de RMCAB...")
    print("="*80)

    try:
        predictor = PredictiveModelPipeline(lookback_window=24, forecast_steps=[1, 3, 5])
        results = predictor.train_and_evaluate(
            rmcab_df,
            output_dir='./results'
        )

        # Paso 3: Mostrar resultados
        print("\n" + "="*80)
        print("[PASO 3] RESUMEN DE RESULTADOS")
        print("="*80)

        summary = predictor.get_summary()

        print("\n📊 MÉTRICAS DE EFECTIVIDAD")
        print("-"*80)

        for pollutant in ['pm25', 'pm10']:
            pollutant_name = 'PM2.5' if pollutant == 'pm25' else 'PM10'
            print(f"\n{pollutant_name} (μg/m³):")
            print("-"*50)

            if pollutant in summary and summary[pollutant]:
                for step in [1, 3, 5]:
                    if step in summary[pollutant]:
                        metrics = summary[pollutant][step]
                        print(f"\n  Predicción {step}h adelante:")
                        print(f"    ├─ RMSE: {metrics['rmse']:.2f} μg/m³  (error cuadrático medio)")
                        print(f"    ├─ MAE:  {metrics['mae']:.2f} μg/m³   (error absoluto medio)")
                        print(f"    ├─ R²:   {metrics['r2']:.4f}        (proporción varianza explicada)")
                        print(f"    └─ MAPE: {metrics['mape']:.2f}%      (error porcentual medio)")

        print("\n" + "="*80)
        print("✓ Modelo entrenado exitosamente")
        print("="*80)

        print("\n📁 Archivos generados:")
        print("  ├─ results/predictive_metrics.csv")
        print("  ├─ results/predictions_PM25.png")
        print("  ├─ results/predictions_PM10.png")
        print("  └─ results/steps_comparison.png")

    except Exception as e:
        print(f"[ERROR] Error en entrenamiento: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == '__main__':
    main()
