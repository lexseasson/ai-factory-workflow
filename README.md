# AI Factory Workflow

Mini-workflow supervisado para alta de productos de Back-Office, orientado a trazabilidad, simplicidad efectiva y calidad operativa.

## Resumen Ejecutivo

Este repositorio implementa un flujo end-to-end:

`entrada -> normalizacion -> validacion -> control de calidad -> artefactos auditables`

Con foco en:
- Diseno claro y mantenible.
- Evidencia tecnica auditable (logs + reportes).
- Reglas de elegibilidad simples y extensibles.
- Operacion reproducible para evaluacion tecnica.

## Contexto del Challenge

Este trabajo responde al challenge:

`Challenge Tecnico - Lider Tecnico / Arquitecto de Solucion (AI & Sistemas Legados), Febrero 2026`

Documento completo del enunciado:
- `docs/challenge_tecnico.md`

Documento de diseno (Etapa 1):
- `docs/design.md`

## Arquitectura

Componentes principales:
- `workflow.io`: ingesta multi-formato (`csv`, `json`, `txt` delimitado y `cobol` fixed-width).
- `workflow.normalize`: normalizacion de fechas, trimming, casing y campos derivados.
- `workflow.rules`: reglas de elegibilidad.
- `workflow.engine`: evaluacion de reglas por registro.
- `workflow.quality`: calculo de metricas, resumen y quality gate.
- `workflow.audit`: logging estructurado JSONL.
- `workflow.run`: orquestacion de pipeline y publicacion de artefactos.

## Reglas Implementadas

- `REQUIRED_FIELDS`: campos obligatorios.
- `CURRENCY_ALLOWED`: monedas permitidas (`ARS`, `USD`, `EUR`).
- `AMOUNT_RANGE`: rango de `monto_o_limite` (`1` a `1_000_000`).

## Estructura del Repositorio

- `src/workflow/`: codigo del workflow.
- `tests/`: unit tests + E2E.
- `data/`: datasets de ejemplo.
- `artifacts/`: salidas por corrida.
- `docs/`: diseno y documentacion del challenge.

## Quickstart

### 1) Clonar el repositorio

```bash
git clone <URL_DEL_REPO>.git
cd ai-factory-workflow
```

### 2) Prerrequisitos

- Python 3.11 o superior
- Git

### 3) Crear y activar entorno virtual

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Ubuntu/Linux (bash):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4) Configurar `PYTHONPATH`

Windows (PowerShell):

```powershell
$env:PYTHONPATH = "src"
```

Ubuntu/Linux (bash):

```bash
export PYTHONPATH=src
```

### 5) Ejecutar el workflow

Windows (PowerShell):

```powershell
python -m workflow.run --input data/sample_requests.csv --format csv --out artifacts --run-label backoffice_csv
```

Ubuntu/Linux (bash):

```bash
python -m workflow.run --input data/sample_requests.csv --format csv --out artifacts --run-label backoffice_csv
```

Ejemplos por formato (ambos SO):

```powershell
python -m workflow.run --input data/sample_requests.json --format json --out artifacts --run-label backoffice_json
python -m workflow.run --input data/sample_requests.txt --format txt --out artifacts --run-label backoffice_txt
python -m workflow.run --input data/sample_requests.cob --format cobol --out artifacts --run-label backoffice_cobol
```

Tambien se puede usar `--format auto` para inferir por extension.

## Artefactos de Salida

Cada corrida genera `artifacts/runs/<run_key>/`:
- `normalized_requests.csv`
- `rejected_requests.csv`
- `data_quality_report.json`
- `decision_log.jsonl`
- `run_manifest.json`

## Layout COBOL (fixed-width)

Cuando se usa `--format cobol`, el parser aplica:
- `id_solicitud`: 0-12
- `fecha_solicitud`: 12-22
- `tipo_producto`: 22-34
- `id_cliente`: 34-46
- `monto_o_limite`: 46-58
- `moneda`: 58-61
- `pais`: 61-63
- `is_vip`: 63-68
- `risk_score`: 68-71

## Calidad Tecnica

Instalar dependencias de testing:

Windows (PowerShell):

```powershell
python -m pip install --upgrade pip
python -m pip install pytest
```

Ubuntu/Linux (bash):

```bash
python -m pip install --upgrade pip
python -m pip install pytest
```

Ejecutar tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

En Ubuntu/Linux:

```bash
python -m pytest -q
```

Cobertura funcional incluida:
- Normalizacion y reglas.
- Ingesta multi-formato.
- Flujo E2E con verificacion de artefactos.

## Etapas del Challenge (Mapa de Cobertura)

- Etapa 1 - Diseno:
  - `docs/design.md`
- Etapa 2 - Implementacion:
  - `src/workflow/`
  - `tests/`
- Etapa 3 - Presentacion tecnica:
  - Soporte con arquitectura, decisiones, artefactos y demo reproducible.

## Subir a Repositorio Remoto (GitHub/GitLab/Azure DevOps)

Si el remoto todavia no esta configurado:

```bash
git remote add origin <URL_DEL_REPO_REMOTO>.git
git branch -M main
git push -u origin main
```

Si ya existe remoto:

```bash
git push
```

## Versionado

- Paquete: `0.2.0`
- Pipeline: `0.2.0`
- Manifest schema: `ai_factory.workflow.run_manifest.v2`
