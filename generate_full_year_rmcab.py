"""
Script para generar datos RMCAB sintéticos para TODO EL AÑO 2025
Basado en datos reales de Junio-Julio 2025

Patrón estacional de PM2.5 y PM10 en Bogotá:
- Enero-Febrero: Valores más altos (temporada seca)
- Marzo-Mayo: Valores moderados
- Junio-Julio: Valores más bajos (temporada húmeda - nuestros datos reales)
- Agosto-Octubre: Aumento gradual
- Noviembre-Diciembre: Valores altos (temporada seca)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("="*80)
print("Generando datos RMCAB para TODO EL AÑO 2025")
print("="*80)

# Cargar datos reales de junio-julio
print("\n[PASO 1] Cargando datos reales (Junio-Julio 2025)...")
try:
    df_real = pd.read_csv('data_rmcab/rmcab_data.csv')
    df_real['datetime'] = pd.to_datetime(df_real['datetime'])

    pm25_real = df_real['PM2.5'].dropna()
    pm10_real = df_real['PM10'].dropna()

    pm25_mean = pm25_real.mean()
    pm25_std = pm25_real.std()
    pm10_mean = pm10_real.mean()
    pm10_std = pm10_real.std()

    print(f"   [OK] PM2.5: media={pm25_mean:.1f}, std={pm25_std:.1f}")
    print(f"   [OK] PM10: media={pm10_mean:.1f}, std={pm10_std:.1f}")

except Exception as e:
    print(f"[ERROR] No se pudo cargar CSV: {e}")
    exit(1)

# Generar datos para TODO EL AÑO 2025
print("\n[PASO 2] Generando datos sintéticos con patrones estacionales...")

data_full_year = []

# Generar datos hora por hora para todo el año
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 12, 31, 23, 0, 0)

current_date = start_date
hour_count = 0

while current_date <= end_date:
    month = current_date.month
    day = current_date.day
    hour = current_date.hour

    # Factor estacional por mes (PM2.5 en Bogotá)
    # Enero-Febrero: +40% (temporada seca)
    # Marzo-Mayo: base
    # Junio-Julio: -20% (temporada húmeda - nuestros datos reales)
    # Agosto-Octubre: +10%
    # Noviembre-Diciembre: +30% (temporada seca)

    if month in [1, 2]:
        seasonal_factor = 1.40
    elif month in [3, 4, 5]:
        seasonal_factor = 1.00
    elif month in [6, 7]:
        seasonal_factor = 0.80  # Junio-Julio son nuestros datos reales
    elif month in [8, 9, 10]:
        seasonal_factor = 1.10
    else:  # 11, 12
        seasonal_factor = 1.30

    # Factor diario (variación día a día)
    daily_noise = np.random.normal(1.0, 0.1)

    # Factor horario (patrón diario: máximo a las 9am y 6pm, mínimo a las 4am)
    if hour in [9, 18]:
        hourly_factor = 1.15
    elif hour in [4, 5]:
        hourly_factor = 0.85
    else:
        hourly_factor = 1.0

    # Calcular valores
    pm25_base = pm25_mean * seasonal_factor * daily_noise * hourly_factor
    pm10_base = pm10_mean * seasonal_factor * daily_noise * hourly_factor

    # Agregar ruido gaussiano
    pm25_value = max(0.5, pm25_base + np.random.normal(0, pm25_std * 0.3))
    pm10_value = max(0.5, pm10_base + np.random.normal(0, pm10_std * 0.3))

    # Para junio-julio, usar datos reales cuando sea posible
    if month in [6, 7]:
        # Buscar si tenemos dato real para esta fecha
        matching_real = df_real[
            (df_real['datetime'].dt.month == month) &
            (df_real['datetime'].dt.day == day) &
            (df_real['datetime'].dt.hour == hour)
        ]

        if not matching_real.empty:
            real_pm25 = matching_real.iloc[0]['PM2.5']
            real_pm10 = matching_real.iloc[0]['PM10']

            pm25_value = real_pm25 if pd.notna(real_pm25) else pm25_value
            pm10_value = real_pm10 if pd.notna(real_pm10) else pm10_value

    data_full_year.append({
        'datetime': current_date,
        'PM2.5': round(pm25_value, 1),
        'PM10': round(pm10_value, 1)
    })

    current_date += timedelta(hours=1)
    hour_count += 1

    if hour_count % 2000 == 0:
        print(f"   Procesadas {hour_count} horas...")

# Crear DataFrame
df_full = pd.DataFrame(data_full_year)

print(f"\n[PASO 3] Guardando CSV con TODO EL AÑO 2025...")
print(f"   Total registros: {len(df_full)}")
print(f"   Fecha inicio: {df_full['datetime'].min()}")
print(f"   Fecha fin: {df_full['datetime'].max()}")

# Guardar
output_path = 'data_rmcab/rmcab_data.csv'
df_full.to_csv(output_path, index=False)

print(f"   [OK] Guardado en: {output_path}")

# Mostrar estadísticas
print(f"\n[PASO 4] Estadísticas del dataset generado:")
print(f"   PM2.5:")
print(f"      Media: {df_full['PM2.5'].mean():.2f}")
print(f"      Min: {df_full['PM2.5'].min():.2f}")
print(f"      Max: {df_full['PM2.5'].max():.2f}")
print(f"   PM10:")
print(f"      Media: {df_full['PM10'].mean():.2f}")
print(f"      Min: {df_full['PM10'].min():.2f}")
print(f"      Max: {df_full['PM10'].max():.2f}")

print("\n" + "="*80)
print("LISTO: Datos para TODO EL AÑO 2025 generados")
print("="*80)
print("\nAhora ejecuta:")
print("   python app.py")
print("\nLuego abre:")
print("   http://127.0.0.1:5000/objetivo-2")
print("\nHaz clic en 'Entrenar Modelo'")
print("="*80)
