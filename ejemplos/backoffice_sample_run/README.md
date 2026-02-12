# Ejemplo de corrida - Backoffice

Artefactos generados con:

```powershell
set PYTHONPATH=src
python -m workflow.run --input data/sample_requests.csv --format csv --out artifacts --run-label backoffice_sample
```

Carpeta: `ejemplos/backoffice_sample_run/`

## Contenido

- `normalized_requests.csv`: registros que pasan normalizacion + reglas.
- `rejected_requests.csv`: registros rechazados con motivo.
- `data_quality_report.json`: totales, tasas, detalle por regla y quality gate.
- `decision_log.jsonl`: log estructurado por eventos.
- `run_manifest.json`: metadatos de corrida, versiones, hash input y referencias.

## Objetivo

Demostrar trazabilidad, validacion y control de calidad de punta a punta con salida auditable.
