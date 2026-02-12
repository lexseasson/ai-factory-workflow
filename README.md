# AI Factory Workflow - Challenge Backoffice

Mini-workflow supervisado para alta de productos en Backoffice, orientado a claridad, trazabilidad y control de calidad.

## 1. Alcance

Entrada -> normalizacion -> validacion -> reporte de calidad -> artefactos auditables.

Formato de entrada soportado:
- `csv`
- `json`
- `txt` delimitado (`|`, `;`, `,` o tab)
- `cobol` fixed-width (layout incluido)

## 2. Arquitectura minima

Componentes principales:
- `workflow.io`: ingesta multi-formato
- `workflow.normalize`: normalizacion de campos
- `workflow.rules`: reglas de elegibilidad
- `workflow.engine`: evaluacion de reglas
- `workflow.quality`: reporte y quality gate
- `workflow.audit`: logging estructurado JSONL
- `workflow.run`: orquestacion del workflow

## 3. Reglas implementadas

- `REQUIRED_FIELDS`: campos obligatorios
- `CURRENCY_ALLOWED`: monedas permitidas (`ARS`, `USD`, `EUR`)
- `AMOUNT_RANGE`: rango de `monto_o_limite` (`1` a `1_000_000`)

## 4. Layout COBOL fixed-width

Cuando se usa `--format cobol`, cada linea se parsea con este layout:

- `id_solicitud`: 0-12
- `fecha_solicitud`: 12-22
- `tipo_producto`: 22-34
- `id_cliente`: 34-46
- `monto_o_limite`: 46-58
- `moneda`: 58-61
- `pais`: 61-63
- `is_vip`: 63-68
- `risk_score`: 68-71

## 5. Ejecucion

```powershell
set PYTHONPATH=src
python -m workflow.run --input data/sample_requests.csv --format csv --out artifacts --run-label backoffice_csv
```

Ejemplos por formato:

```powershell
python -m workflow.run --input data/sample_requests.json --format json --out artifacts --run-label backoffice_json
python -m workflow.run --input data/sample_requests.txt --format txt --out artifacts --run-label backoffice_txt
python -m workflow.run --input data/sample_requests.cob --format cobol --out artifacts --run-label backoffice_cobol
```

Tambien se puede usar `--format auto` para inferir por extension.

## 6. Artefactos de salida

Por corrida se genera `artifacts/runs/<run_key>/` con:
- `normalized_requests.csv`
- `rejected_requests.csv`
- `data_quality_report.json`
- `decision_log.jsonl`
- `run_manifest.json`

## 7. Cobertura del challenge

- Diseno: `docs/design.md`
- Implementacion: `src/workflow/`
- Validaciones: `src/workflow/rules.py`
- Control de calidad: `src/workflow/quality.py`
- Logs y trazabilidad: `src/workflow/audit.py` + `run_manifest.json`
- Instrucciones de ejecucion: este `README.md`

## 8. Calidad de codigo

Tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Incluye:
- tests unitarios de normalizacion y reglas
- tests de ingesta multi-formato
- test E2E del workflow con verificacion de artefactos

## 9. Versionado

- Paquete: `0.2.0`
- Pipeline: `0.2.0`
- Manifest schema: `ai_factory.workflow.run_manifest.v2`
