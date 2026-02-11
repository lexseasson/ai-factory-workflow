# AI Factory – Motor de Control de Admisión (Backoffice)

## Resumen Ejecutivo

Este repositorio implementa un **Motor de Control de Admisión** diseñado para entornos regulados.

No es un ETL simple.
Es un flujo gobernado que transforma solicitudes de alta en decisiones auditables.

Fue construido bajo principios de:

- Auditabilidad total
- Gobernanza explícita
- Identidad determinística de ejecución
- Evidencia estructurada
- Reproducibilidad

El objetivo no es complejidad.
El objetivo es control.

---

## Contexto del Problema

Las unidades de Back‑Office reciben solicitudes de alta de productos (cuentas, tarjetas, servicios) desde múltiples canales.

Antes de impactar sistemas core, estas solicitudes deben:

1. Normalizarse
2. Validarse
3. Clasificarse
4. Auditarse
5. Reportarse

En un entorno regulado la pregunta crítica es:

> ¿Podemos reconstruir por qué un registro fue aceptado o rechazado?

Este motor responde esa pregunta de forma explícita.

---

## Arquitectura General

Flujo implementado:

Entrada → Normalización → Motor de Reglas → Quality Gate → Salidas + Evidencia

Componentes clave:

- **Motor de Reglas** – Validación determinística de elegibilidad
- **Zona de Cuarentena** – Registros inválidos aislados, no descartados
- **Decision Log (JSONL)** – Evidencia estructurada de cada decisión
- **Run Manifest** – Índice auditable del lote completo
- **Quality Gate** – Política formal sobre métricas agregadas

Separar transformación, validación y gobernanza fue una decisión intencional.

---

## Principios de Diseño

### 1. Separación de Responsabilidades

- Normalización ≠ Validación
- Validación ≠ Gobernanza
- Gobernanza ≠ Reporte

Esto mejora:

- Testeabilidad
- Mantenibilidad
- Claridad en auditoría

---

### 2. Gobernanza como Primera Clase

Se introdujo un **Quality Gate explícito**:

Política actual:

invalid_rate <= 0.05

Esto incorpora:

- Política versionable
- Decisión automatizada
- Trazabilidad entre métricas y resultado
- Estado degradado controlado (COMPLETED_WITH_WARNINGS)

---

### 3. Identidad Determinística del Lote

Cada ejecución genera:

timestamp__label__short_id

Permite:

- Reproducibilidad
- Identificación humana del lote
- Agrupación determinística de artefactos

---

### 4. Evidencia Estructurada

Cada corrida genera:

- decision_log.jsonl
- normalized_requests.csv
- rejected_requests.csv
- data_quality_report.json
- run_manifest.json

El run_manifest contiene:

- Versión del pipeline
- Schema del manifiesto
- Hash SHA256 del input
- Catálogo de reglas
- Conteos agregados
- Resultado del Quality Gate
- Tiempos de ejecución
- Referencia a artefactos

Cada ejecución es una unidad auditable.

---

## Cómo Ejecutar

```
set PYTHONPATH=src
python -m workflow.run --input data/sample_requests.csv --out artifacts --run-label backoffice_sample
```

Los artefactos se generan en:

```
artifacts/runs/<run_key>/
```

---

## Cómo Extender

### Agregar una nueva regla

1. Implementar nueva clase en `workflow/rules.py`
2. Agregarla a la lista de reglas en `run.py`

Automáticamente:

- Se incluirá en el manifiesto
- Impactará el reporte de calidad
- Quedará registrada en el decision log

No requiere modificar la orquestación.

---

### Modificar la Política de Gobernanza

Cambiar el threshold en el bloque Quality Gate de `run.py`.

La política quedará registrada en el manifiesto junto con su resultado.

---

## Controles para Entornos Regulados

La arquitectura permite incorporar:

- Firma digital del manifiesto
- Almacenamiento inmutable (WORM) del decision log
- Versionado formal de reglas
- Métricas SLA por etapa
- Lineage formal input-output
- Integración con sistemas de auditoría externos

Sin rediseñar el sistema.

---

## Qué Demuestra Este Repositorio

- Pensamiento arquitectónico orientado a control
- Gobernanza explícita
- Separación clara entre reglas y orquestación
- Disciplina de tipado estricto (mypy strict)
- Calidad automatizada (ruff + pre-commit)
- Reproducibilidad operacional

No busca sobre‑ingeniería.
Busca claridad y control.

---

## Conclusión

Esta solución cumple con el challenge técnico y agrega una capa explícita de:

- Accountability
- Trazabilidad
- Gobernanza
- Control de calidad formal

No está diseñada solo para procesar datos.

Está diseñada para justificar decisiones.
