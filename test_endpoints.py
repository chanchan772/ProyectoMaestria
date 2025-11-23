"""
Script para probar los endpoints de Objetivo 1
Ejecutar con: python test_endpoints.py
"""

from app import app
import json

if __name__ == '__main__':
    # Crear cliente de test
    client = app.test_client()

    print("=" * 60)
    print("PRUEBA DE ENDPOINTS - OBJETIVO 1")
    print("=" * 60)

    # Test 1: Initialize
    print("\n[1] POST /api/objetivo1/initialize")
    print("-" * 60)
    response = client.post('/api/objetivo1/initialize')
    data = response.get_json()
    print(f"Status Code: {response.status_code}")
    print(f"Status: {data.get('status')}")
    print(f"Message: {data.get('message')}")
    if data.get('metrics'):
        print(f"Total Records: {data['metrics'].get('total_records')}")
        print(f"Date Range: {data['metrics']['date_range']['start']} a {data['metrics']['date_range']['end']}")

    # Test 2: Timeseries
    print("\n[2] GET /api/objetivo1/timeseries")
    print("-" * 60)
    response = client.get('/api/objetivo1/timeseries')
    data = response.get_json()
    print(f"Status Code: {response.status_code}")
    print(f"Status: {data.get('status')}")
    if data.get('graph'):
        graph = data['graph']
        print(f"Graph Data Traces: {len(graph.get('data', []))}")
        print(f"Graph Layout: {graph.get('layout', {}).get('title', 'N/A')}")

    # Test 3: Scatter Plots
    print("\n[3] GET /api/objetivo1/scatter-plots")
    print("-" * 60)
    response = client.get('/api/objetivo1/scatter-plots')
    data = response.get_json()
    print(f"Status Code: {response.status_code}")
    print(f"Status: {data.get('status')}")
    if data.get('graphs'):
        print(f"Scatter Plots: {len(data['graphs'])} gráficos")
        for sensor, metrics in data.get('metrics', {}).items():
            print(f"  {sensor}: R²={metrics['r2']}, RMSE={metrics['rmse']}")

    # Test 4: Calibrate
    print("\n[4] POST /api/objetivo1/calibrate")
    print("-" * 60)
    response = client.post('/api/objetivo1/calibrate',
                          json={'time_range_days': None},
                          content_type='application/json')
    data = response.get_json()
    print(f"Status Code: {response.status_code}")
    print(f"Status: {data.get('status')}")
    if data.get('best_models'):
        print(f"Best Models Found: {len(data['best_models'])}")
        for sensor, model_info in data['best_models'].items():
            print(f"  {sensor}: {model_info['model']} (R²={model_info['metrics']['r2']})")
    if data.get('conclusions'):
        print(f"Conclusion Summary: {data['conclusions'].get('summary', 'N/A')}")
        print(f"Recommendation: {data['conclusions'].get('recommendations', 'N/A')}")

    # Test 5: Time Ranges
    print("\n[5] POST /api/objetivo1/test-ranges")
    print("-" * 60)
    response = client.post('/api/objetivo1/test-ranges',
                          content_type='application/json')
    data = response.get_json()
    print(f"Status Code: {response.status_code}")
    print(f"Status: {data.get('status')}")
    if data.get('best_ranges'):
        print(f"Best Ranges:")
        for sensor, range_info in data['best_ranges'].items():
            print(f"  {sensor}: {range_info['best_range']} (R²={range_info['best_r2']})")

    print("\n" + "=" * 60)
    print("PRUEBAS COMPLETADAS")
    print("=" * 60)
