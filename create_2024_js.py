#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear visualizacion_2024.js a partir de visualizacion_junio_julio.js
"""

import os

# Rutas
source_file = r'C:\Proyecto Maestria 23 Sep\fase 3\static\js\visualizacion_junio_julio.js'
target_file = r'C:\Proyecto Maestria 23 Sep\fase 3\static\js\visualizacion_2024.js'

# Leer archivo fuente
with open(source_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Realizar reemplazos
replacements = [
    ('2025-06-01', '2024-01-01'),
    ('2025-07-31', '2024-12-31'),
    ('Junio-Julio 2025', 'Año Completo 2024'),
    ('junio-julio', 'año 2024'),
    ('RMCAB_LasFer', 'RMCAB_MinAmb'),
    ("'RMCAB_LasFer':", "'RMCAB_MinAmb':"),
    ('Las Ferias', 'Min Ambiente'),
    ('station: 6', 'station: 9'),
    ('Periodo: 1 junio - 31 julio 2025', 'Periodo: 1 enero - 31 diciembre 2024'),
    ('/**\n * JavaScript para Visualización Junio-Julio 2024\n */', '/**\n * JavaScript para Visualización Año Completo 2024\n */')
]

for old, new in replacements:
    content = content.replace(old, new)

# Guardar archivo destino
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'✅ Archivo creado exitosamente: {target_file}')
print(f'📊 Tamaño: {len(content)} caracteres')
