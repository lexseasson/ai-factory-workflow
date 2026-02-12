# Ejemplo de Ejecución – Backoffice Admission Workflow

Los artefactos aquí incluidos corresponden a una ejecución reproducible del workflow utilizando el archivo:

    data/sample_requests.csv

Este dataset contiene 20 registros sintéticos diseñados para probar el sistema end-to-end, incluyendo casos válidos e inválidos.

---

## Artefactos generados

### normalized_requests.csv

Contiene los registros que superaron:

- Normalización
- Validaciones de elegibilidad
- Quality Gate

Incluye los siguientes campos:

- id_solicitud  
- fecha_solicitud (ISO 8601)  
- tipo_producto  
- id_cliente  
- monto_o_limite  
- moneda  
- pais  
- is_vip  
- risk_score  
- risk_bucket  

Este archivo representa la salida "aprobada" del Admission Control Engine.

---

### rejected_requests.csv

Contiene los registros que fueron rechazados por:

- Error de normalización
- Fallas en reglas de elegibilidad

Incluye:

- id_solicitud  
- reject_rule_ids  
- reject_reasons  

Funciona como zona de cuarentena explícita (quarantine).

---

### data_quality_report.json

Reporte estructurado de control de calidad que incluye:

- total
- valid
- invalid
- acceptance_rate
- rejection_rate
- failure_rate_by_rule
- rule_details (con ejemplos auditables)
- quality_gate (policy versionable + decisión automatizada)

Responde explícitamente a:

- ¿Cuántos registros pasaron?
- ¿Cuántos fallaron?
- ¿Por qué fallaron?
- ¿El run es aceptable bajo la política definida?

---

### decision_log.jsonl

Evidence log en formato append-only (JSON Lines).

Cada línea representa un evento del workflow con:

- stage
- event
- level
- run_id
- timestamps
- metadata relevante

Permite reconstruir qué ocurrió, cuándo y por qué.

Es la base de trazabilidad y auditabilidad.

---

### run_manifest.json

Índice estructurado del run.

Contiene:

- Identidad determinística del run (run_id + run_key)
- Información del entorno de ejecución
- Hash SHA256 del archivo de entrada
- Reglas aplicadas
- Métricas agregadas
- Decisión del Quality Gate
- Referencias a todos los artefactos generados

Es el punto único de entrada para auditoría técnica.

---

## Reproducibilidad

La ejecución puede reproducirse con:

    set PYTHONPATH=src
    python -m workflow.run --input data/sample_requests.csv --out artifacts --run-label backoffice_sample

El hash SHA256 del input garantiza integridad del dataset utilizado.

---

## Objetivo del ejemplo

Este ejemplo demuestra:

- Admission Control Engine funcional
- Validaciones explícitas y versionables
- Control de calidad cuantificado
- Quality Gate automatizado
- Trazabilidad completa
- Separación entre procesamiento y gobernanza
- Reproducibilidad determinística

---

## Enfoque arquitectónico

Este diseño prioriza:

- Determinismo (run identity y hash del input)
- Auditabilidad (decision_log + manifest)
- Gobierno explícito (quality_gate versionado)
- Separación de responsabilidades
- Simplicidad efectiva sin sobreingeniería

El objetivo no es solo validar datos.
El objetivo es demostrar control técnico en entornos regulados.
