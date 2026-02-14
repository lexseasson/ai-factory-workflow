# Challenge Tecnico
## Lider Tecnico / Arquitecto de Solucion (AI & Sistemas Legados)

- Modalidad: Desarrollo offline + presentacion tecnica
- Fecha de referencia: Febrero 2026

## 1) Contexto del Challenge

Una unidad de Back-Office recibe solicitudes de alta de productos (por ejemplo cuentas, tarjetas o servicios) desde distintos canales.
Cada solicitud puede llegar en `CSV`, `JSON` o `TXT`, con campos basicos:
- `id_solicitud`
- `fecha_solicitud`
- `tipo_producto`
- `id_cliente`
- `monto_o_limite`
- `pais`
- `moneda`
- 1-2 flags

Se solicita un mini-workflow que:
- Ingeste el archivo de solicitudes.
- Procese y normalice campos minimos (fechas, mayusculas/minusculas, trimming).
- Valide reglas simples de elegibilidad.
- Aplique control de calidad (pasan/fallan y motivos).
- Genere logs y reporte breve de validacion/calidad.

Objetivo: diseno claro, estandares, validaciones y trazabilidad (que se hizo, cuando y por que).

## 2) Consigna General

Construir un mini-workflow supervisado con:
1. Diseno.
2. Implementacion funcional.
3. Validacion (1-3 reglas simples).
4. Control de calidad.
5. Logs y registro de decisiones.

## 3) Etapa 1 - Diseno (maximo 1-2 paginas)

### a) Arquitectura minima
Diagrama de flujo que cubra:
- Entrada -> procesamiento -> validacion -> salida.
- Componentes del workflow.
- Donde y como se generan logs.
- Puntos de validacion y control de calidad.

### b) Estandares y convenciones
- Convenciones de nombres.
- Estructura de carpetas/modulos.
- Criterios de logging (que, cuando y nivel).
- Manejo de errores (categorias, mensajes, propagacion).
- Supuestos tecnicos (encoding, formato de fechas, etc.).

### c) Supervision tecnica
- Como asegurar mantenibilidad.
- Que revisar en code review.
- Riesgos tecnicos y mitigaciones.

## 4) Etapa 2 - Implementacion del Mini-Workflow

### Entrada
Archivo `CSV`, `JSON` o `TXT` con al menos:
- `id_solicitud`
- `fecha_solicitud`
- `tipo_producto`
- `id_cliente`
- `monto_o_limite`
- `moneda`
- `pais`
- 1-2 flags

### Proceso
Normalizacion minima + transformacion simple (campo derivado o clasificacion por tipo).

### Validacion (1-3 reglas)
Ejemplos:
- Campos obligatorios presentes.
- Formato valido de fecha y moneda.
- Rangos de `monto_o_limite`.
- Moneda incluida en lista corta (`ARS`, `USD`, `EUR`).

### Control de calidad
Reporte JSON con:
- Totales procesados, validos e invalidos.
- Detalle por regla (caidas y ejemplos).
- Indicadores simples (porcentaje de cumplimiento).

### Logs
- Inicio de workflow.
- Pasos ejecutados.
- Errores y advertencias.
- Resumen final (tiempo y totales).

### Salida
- Datos transformados.
- Reporte de validacion/calidad.
- Logs.

## 5) Etapa 3 - Presentacion Tecnica (20-30 minutos)

- Diseno (arquitectura + estandares) y racional.
- Implementacion (decisiones, supuestos, errores).
- Demo breve o explicacion de ejecucion.
- Extension/escalado (mas reglas, mas fuentes).
- Controles adicionales para entornos con mayor trazabilidad/calidad.

## 6) Entrega

- Documento de diseno (PDF o Markdown).
- Codigo fuente y archivos necesarios (zip o repo).
- Instrucciones minimas de ejecucion (`README`).

## 7) Criterios de evaluacion

- Claridad de diseno y calidad de diagrama.
- Estandares aplicados (nombres, estructura, logs, errores).
- Calidad de validaciones y reporte de control.
- Simplicidad efectiva (sin complejidad innecesaria).
- Comunicacion tecnica en la presentacion.
