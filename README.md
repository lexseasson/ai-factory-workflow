
# AI Factory – Motor de Control de Admisión (Backoffice)

## Resumen Ejecutivo

Este repositorio implementa un **Motor de Control de Admisión orientado a entornos regulados**.

No es un simple flujo de transformación de datos.
Es una arquitectura de decisión auditada, reproducible y gobernada.

El objetivo no es procesar registros.
El objetivo es **controlar decisiones con evidencia estructurada**.

Fue diseñado bajo principios explícitos de:

- Auditabilidad total
- Gobernanza como primera clase
- Identidad determinística de ejecución
- Evidencia estructurada por evento
- Política versionable
- Reproducibilidad operacional

Este diseño prioriza claridad arquitectónica por sobre complejidad innecesaria.

---

## Contexto del Problema

Las unidades de Back‑Office reciben solicitudes de alta de productos (cuentas, tarjetas, servicios) desde múltiples canales y formatos.

Antes de impactar sistemas core, estas solicitudes deben:

1. Normalizarse
2. Validarse
3. Clasificarse
4. Registrarse como evidencia
5. Evaluarse contra una política de calidad agregada

En un entorno regulado la pregunta crítica no es:

> ¿Funciona?

Sino:

> ¿Podemos reconstruir exactamente qué ocurrió, cuándo ocurrió y por qué ocurrió?

Este motor responde esa pregunta de forma explícita y determinística.

---

## Arquitectura General

Flujo implementado:

Entrada → Normalización → Motor de Reglas → Quality Gate → Artefactos + Evidencia

Componentes clave:

- Motor de Reglas determinístico (elegibilidad)
- Zona de Cuarentena explícita (rejected_requests.csv)
- Decision Log estructurado (JSONL)
- Data Quality Report agregando métricas ejecutivas
- Run Manifest como contrato auditable del lote
- Quality Gate como política formal desacoplada

La separación entre transformación, validación y gobernanza es intencional.

---

## Principios Arquitectónicos

### 1. Separación de Responsabilidades

- Normalización ≠ Validación
- Validación ≠ Gobernanza
- Gobernanza ≠ Reporte
- Evidencia ≠ Métrica

Esto mejora:

- Testeabilidad
- Mantenibilidad
- Trazabilidad
- Claridad en auditoría

---

### 2. Gobernanza como Primera Clase

Se incorpora un **Quality Gate explícito y versionable**.

Ejemplo de política:

invalid_rate <= 0.05

Esto introduce:

- Política formal y visible
- Decisión automatizada
- Snapshot de métricas
- Evidencia explícita en el manifest
- Estado degradado controlado

La política no está implícita en el código.
Está declarada.

---

### 3. Identidad Determinística del Lote

Cada ejecución genera:

timestamp__label__short_id

Y registra:

- UUID del run
- Hash SHA256 del input
- Entorno de ejecución
- Argumentos de ejecución

Esto garantiza reproducibilidad verificable.

---

### 4. Evidencia Estructurada

Cada corrida genera:

- decision_log.jsonl
- normalized_requests.csv
- rejected_requests.csv
- data_quality_report.json
- run_manifest.json

El run_manifest actúa como índice auditable completo del lote.

Cada ejecución es una unidad auditable independiente.

---

## Cómo Ejecutar

```
set PYTHONPATH=src
python -m workflow.run --input data/sample_requests.csv --out artifacts --run-label backoffice_sample
```

Artefactos generados en:

```
artifacts/runs/<run_key>/
```

---

## Cómo Extender

### Agregar una nueva regla

1. Crear nueva clase en `workflow/rules.py`
2. Incorporarla en la lista de reglas en `run.py`

Automáticamente:

- Se registrará en el manifest
- Impactará métricas agregadas
- Aparecerá en el decision log
- Quedará incluida en el reporte de calidad

No requiere modificar la orquestación.

---

### Modificar la Política de Gobernanza

Ajustar la política del Quality Gate en `quality.py`.

La política queda:

- Versionada
- Registrada en el manifest
- Asociada a métricas snapshot
- Auditada por decisión

---

## Controles para Entornos Regulados

Este workflow fue diseñado pensando en escenarios donde la trazabilidad no es opcional.

Incorpora explícitamente:

1. Deterministic Run Identity  
   - UUID  
   - Run key legible  
   - SHA256 del input  

2. Evidence Log desacoplado  
   - stage  
   - event  
   - severity  
   - record_id  
   - rule_id  
   - reason  
   - timestamp UTC  

3. Policy Engine visible  
   - Reglas tipadas  
   - Severidad declarada  
   - Registro en manifest  

4. Quality Gate explícito  
   - Política formal  
   - Métricas snapshot  
   - Decisión trazable  

5. Manifest como contrato del run  
   - Versión del pipeline  
   - Schema del manifiesto  
   - Catálogo de reglas  
   - Conteos agregados  
   - Resultado del gate  
   - Referencia a artefactos  

Permite auditoría posterior sin ejecutar código.

---

## Qué Demuestra Este Repositorio

- Pensamiento arquitectónico orientado a control
- Diseño gobernado por política explícita
- Separación clara entre reglas y orquestación
- Disciplina de tipado estricto (mypy strict)
- Calidad automatizada (ruff + pre-commit)
- Evidencia estructurada y reproducible
- Capacidad de escalar a entornos regulados

No busca sobre‑ingeniería.
Busca responsabilidad técnica.

---

## Conclusión

Esta solución no solo cumple el challenge técnico.

Demuestra:

- Accountability estructural
- Trazabilidad verificable
- Gobernanza explícita
- Control de calidad formal
- Arquitectura preparada para regulación

No está diseñada solo para procesar datos.

Está diseñada para justificar decisiones.
