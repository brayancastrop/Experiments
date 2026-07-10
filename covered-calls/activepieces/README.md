# Orquestación del sistema en Activepieces

Carpeta **"Covered Calls"** para tu instancia de Activepieces: 5 flujos que
automatizan el ciclo mensual de [ESTRATEGIA.md](../ESTRATEGIA.md). Los
disparadores y avisos los ponen los flujos; **las órdenes las pones tú** —
ningún flujo opera en el broker.

## Los flujos

| Flujo | Disparador | Qué hace |
|---|---|---|
| **CC · 01 Apertura de ciclo** | Cron mensual (día 1, 14:00 UTC) | Lee la hoja *Posiciones*, consulta la cadena de opciones (Tradier) y te envía por Gmail los strikes candidatos que cumplen las reglas: 30–45 DTE, delta 0.20–0.30, strike ≥ costo base, rendimiento ≥ 0.5% |
| **CC · 02 Vigilancia de posiciones** | Cron lunes y jueves (14:00 UTC) | Para cada call abierto calcula el % de prima capturada y si el strike está amenazado; si hay que actuar (regla 50–70% o roll/asignación) envía alerta |
| **CC · 03 Registro de operaciones** | Webhook | Recibe una operación (venta, recompra o asignación), la normaliza, calcula el resultado neto y añade la fila a la hoja *Diario* |
| **CC · 04 Cierre de mes** | Cron mensual (día 1, 13:00 UTC) | Calcula las métricas del mes anterior desde el *Diario* (prima neta, % sobre capital, tasa de asignación, cierres en banda 50–70%) y envía el informe; avisa si la tasa de asignación supera el 30% |
| **CC · 05 Alerta de earnings** | Cron laborables (12:00 UTC) | Cruza los calls abiertos con el calendario de earnings (Finnhub) y avisa si hay resultados antes del vencimiento |

Los horarios están en UTC — ajusta los cron a tu zona al importar.

## Requisitos

1. **Google Sheet** con dos pestañas (fila 1 = cabeceras exactas):
   - `Posiciones`: `ticker, acciones, costo_base, call_abierto, strike, vencimiento, prima_cobrada, contratos`
     (`call_abierto` = `si`/`no`; `vencimiento` = `AAAA-MM-DD`)
   - `Diario`: `fecha_venta, ticker, contratos, strike, dte, prima_cobrada, delta_apertura, fecha_cierre, costo_recompra, resultado_neto, asignado, notas`
   - Los flujos de **lectura** usan el export CSV público de la hoja
     (`.../gviz/tq?tqx=out:csv&sheet=...`): comparte la hoja como *"cualquiera
     con el enlace — lector"*, o sustituye ese paso HTTP por la acción de
     lectura del piece de Google Sheets si prefieres mantenerla privada.
2. **Conexiones en Activepieces**: `gmail` (envío de correos) y
   `google-sheets` (escritura del Diario, flujo 03).
3. **Tokens de datos de mercado** (gratuitos):
   - [Tradier](https://documentation.tradier.com/) — cadenas de opciones con
     griegas (flujos 01 y 02). El JSON viene apuntando al *sandbox*; cambia el
     input `entorno` a `produccion` cuando tengas token real.
   - [Finnhub](https://finnhub.io/) — calendario de earnings (flujo 05).

## Importar los flujos

**Opción A — interfaz**: en tu instancia AP crea la carpeta *Covered Calls*
(Flows → ícono de carpeta → New folder) y luego, dentro de ella,
*Import Flow* con cada JSON de [`flows/`](flows/).

**Opción B — API** (crea la carpeta e importa los 5 de una vez):

```bash
export AP_URL="https://tu-instancia.example.com"
export AP_API_KEY="tu_api_key"        # Bearer token (API key de plataforma)
export AP_PROJECT_ID="tu_project_id"  # visible en la URL del dashboard
./import-flows.sh
```

## Después de importar (buscar y reemplazar)

En cada flujo, sustituye los marcadores:

| Marcador | Dónde | Valor |
|---|---|---|
| `PEGA_AQUI_EL_ID_DE_TU_HOJA` | pasos HTTP y Sheets | ID de tu Google Sheet |
| `PEGA_AQUI_EL_GID_DE_LA_PESTANA_DIARIO` | flujo 03 | `gid` de la pestaña Diario |
| `TU_CORREO@gmail.com` | pasos Gmail | tu correo |
| `PEGA_AQUI_TU_TOKEN_TRADIER` | flujos 01 y 02 | token de Tradier |
| `PEGA_AQUI_TU_TOKEN_FINNHUB` | flujo 05 | token de Finnhub |
| `PEGA_AQUI_TU_CAPITAL_TOTAL` | flujo 04 | capital del sistema (para el % mensual) |

Además: reconecta `gmail` y `google-sheets` a tus cuentas, copia la URL del
webhook del flujo 03 (para registrar operaciones desde un atajo de
iPhone/Android, un formulario o `curl`), activa los flujos y prueba cada uno
con *Test flow*.

Ejemplo de registro vía webhook (flujo 03):

```bash
curl -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" -d '{
  "ticker": "AAPL", "contratos": 1, "strike": 210, "dte": 35,
  "prima_cobrada": 2.10, "delta_apertura": 0.25, "notas": "apertura de ciclo"
}'
```

## Notas de compatibilidad

- Los JSON usan el esquema de exportación de flujos de Activepieces con
  versiones de pieces conocidas (`~x.y.z`). Si tu instancia trae versiones más
  nuevas, el import normalmente migra solo; si algún paso queda inválido,
  ábrelo en el editor y re-selecciona la acción (los inputs están documentados
  arriba y el código de los *code steps* se puede copiar tal cual).
- El paso condicional usa `BRANCH`; las versiones recientes lo migran a
  *Router* automáticamente al importar.
