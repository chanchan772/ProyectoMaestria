# Script para copiar y adaptar JS de junio-julio a 2024
import re

# Leer archivo fuente
with open(r'C:\Proyecto Maestria 23 Sep\fase 3\static\js\visualizacion_junio_julio.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar fechas y referencias
content = re.sub(r'2025-06-01', '2024-01-01', content)
content = re.sub(r'2025-07-31', '2024-12-31', content)
content = re.sub(r'Junio-Julio 2024', 'Año Completo 2024', content)
content = re.sub(r'Junio - Julio 2025', 'Enero - Diciembre 2024', content)
content = re.sub(r'junio-julio', 'año 2024', content)
content = re.sub(r'Junio-Julio', 'Año Completo', content)

# Guardar en archivo destino
with open(r'C:\Proyecto Maestria 23 Sep\fase 3\static\js\visualizacion_2024.js', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Archivo visualizacion_2024.js actualizado exitosamente')
print(f'Total de caracteres: {len(content)}')
