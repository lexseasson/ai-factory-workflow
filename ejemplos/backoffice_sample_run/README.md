# Ejecución de Ejemplo – Backoffice Admission Workflow

Este directorio contiene los artefactos generados por una ejecución real del motor de admisión utilizando:

    data/sample_requests.csv

La corrida fue ejecutada con:

    python -m workflow.run       --input data/sample_requests.csv       --out artifacts       --run-label backoffice_sample       --format auto

---

## Identidad del Run

Datos principales extraídos del manifiesto:

- Formato detectado: csv
- Total registros procesados: 20
- Válidos: 9
- Inválidos: 11
- Estado final: COMPLETED_WITH_WARNINGS

El estado es COMPLETED_WITH_WARNINGS porque el Quality Gate detectó:

    rejection_rate = 0.55
    threshold máximo permitido = 0.40

La política aplicada es versionable y está registrada como:

    quality_gate.v1

---

## Artefactos Generados

### 1. run_manifest.json

Contrato formal del lote procesado.

Incluye:

- Versión del pipeline
- Identidad determinística del run
- Hash SHA256 del input
- Catálogo de reglas aplicadas
- Métricas agregadas
- Decisión del Quality Gate
- Integridad SHA256 de todos los artefactos

Permite reconstruir el contexto completo del procesamiento sin reejecutar código.

---

### 2. decision_log.jsonl

Log estructurado por eventos.

Cada línea representa un evento con:

- timestamp UTC
- stage (ingest / normalize / validate / governance / output)
- severidad (INFO / WARN / ERROR)
- record_id
- rule_id
- motivo

Es evidencia granular lista para auditoría técnica o regulatoria.

---

### 3. normalized_requests.csv

Contiene únicamente los registros aceptados por el motor de reglas.

Son los registros elegibles para sistemas downstream.

---

### 4. rejected_requests.csv

Zona de cuarentena explícita.

Incluye:

- Registro original
- reject_rule_ids
- reject_reasons

Ningún dato inválido se descarta silenciosamente.

---

### 5. data_quality_report.json

Resumen agregado del control de calidad.

Incluye:

- Totales
- Tasas de aceptación y rechazo
- Failure rate por regla
- Ejemplos de registros fallidos
- Decisión automatizada del Quality Gate
- Snapshot de métricas utilizadas

Conecta métricas con decisión de gobernanza.

---

## Qué Demuestra Esta Ejecución

1. Identidad determinística del lote.
2. Evidencia estructurada por evento.
3. Validación determinística y reproducible.
4. Política de calidad explícita y versionable.
5. Separación entre procesamiento y control.
6. Cadena de custodia mediante hashes SHA256.

No es un ejemplo sintético manual.
Es una ejecución real del pipeline end-to-end.

---

## Cómo Revisar Esta Evidencia

Para evaluadores técnicos:

1. Abrir run_manifest.json para entender el contrato del lote.
2. Revisar data_quality_report.json para métricas y decisión.
3. Consultar decision_log.jsonl para trazabilidad granular.
4. Comparar normalized_requests.csv vs rejected_requests.csv.

La estructura completa permite responder:

- Qué se procesó
- Cuándo
- Con qué reglas
- Bajo qué política
- Con qué resultado
- Con qué evidencia

Este ejemplo demuestra que el sistema no solo procesa datos.
Justifica decisiones.
