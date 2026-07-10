#!/usr/bin/env bash
# Crea la carpeta "Covered Calls" en una instancia de Activepieces e importa
# los 5 flujos de flows/ vía API REST.
#
# Uso:
#   export AP_URL="https://tu-instancia.example.com"
#   export AP_API_KEY="tu_api_key"        # Bearer token
#   export AP_PROJECT_ID="tu_project_id"
#   ./import-flows.sh
set -euo pipefail

: "${AP_URL:?Define AP_URL (p. ej. https://cloud.activepieces.com)}"
: "${AP_API_KEY:?Define AP_API_KEY}"
: "${AP_PROJECT_ID:?Define AP_PROJECT_ID}"

command -v jq >/dev/null || { echo "Este script necesita jq"; exit 1; }

API="${AP_URL%/}/api/v1"
AUTH=(-H "Authorization: Bearer ${AP_API_KEY}" -H "Content-Type: application/json")
DIR="$(cd "$(dirname "$0")" && pwd)/flows"
FOLDER_NAME="Covered Calls"

echo "==> Buscando/creando la carpeta '${FOLDER_NAME}'..."
FOLDER_ID="$(curl -fsS "${API}/folders?projectId=${AP_PROJECT_ID}&limit=100" "${AUTH[@]}" \
  | jq -r --arg n "$FOLDER_NAME" '.data[]? | select(.displayName == $n) | .id' | head -n1)"

if [ -z "${FOLDER_ID}" ]; then
  FOLDER_ID="$(curl -fsS -X POST "${API}/folders" "${AUTH[@]}" \
    -d "$(jq -n --arg n "$FOLDER_NAME" --arg p "$AP_PROJECT_ID" '{displayName: $n, projectId: $p}')" \
    | jq -r '.id')"
  echo "    Carpeta creada: ${FOLDER_ID}"
else
  echo "    Carpeta existente: ${FOLDER_ID}"
fi

for archivo in "${DIR}"/*.json; do
  NOMBRE="$(jq -r '.displayName' "${archivo}")"
  echo "==> Importando: ${NOMBRE}"

  FLOW_ID="$(curl -fsS -X POST "${API}/flows" "${AUTH[@]}" \
    -d "$(jq -n --arg n "$NOMBRE" --arg p "$AP_PROJECT_ID" --arg f "$FOLDER_ID" \
          '{displayName: $n, projectId: $p, folderId: $f}')" \
    | jq -r '.id')"

  # IMPORT_FLOW reemplaza trigger + pasos con la plantilla exportada
  curl -fsS -X POST "${API}/flows/${FLOW_ID}" "${AUTH[@]}" \
    -d "$(jq -n --slurpfile t "${archivo}" \
          '{type: "IMPORT_FLOW", request: {displayName: $t[0].displayName, trigger: $t[0].template.trigger, schemaVersion: ($t[0].template.schemaVersion // "1")}}')" \
    > /dev/null

  # Por si la instancia ignora folderId en la creación
  curl -fsS -X POST "${API}/flows/${FLOW_ID}" "${AUTH[@]}" \
    -d "$(jq -n --arg f "$FOLDER_ID" '{type: "CHANGE_FOLDER", request: {folderId: $f}}')" \
    > /dev/null || echo "    (aviso: CHANGE_FOLDER falló; mueve el flujo a la carpeta desde la UI)"

  echo "    OK — flow ${FLOW_ID}"
done

echo
echo "Listo. Recuerda (ver README.md): reemplazar los marcadores PEGA_AQUI_*,"
echo "reconectar gmail/google-sheets, ajustar los cron a tu zona horaria y"
echo "activar los flujos."
