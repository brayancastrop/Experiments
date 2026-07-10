# Sistema de Covered Calls — ingresos repetibles con riesgo controlado

Un sistema operativo, paso a paso, para generar ingresos mensuales vendiendo
*covered calls* (llamadas cubiertas). El objetivo no es hacerse rico rápido:
es cobrar primas de forma **repetible** sobre acciones que ya quieres tener,
con reglas fijas que eliminan la improvisación.

> ⚠️ **Honestidad primero.** "Riesgo bajo" no significa "sin riesgo". El riesgo
> principal de un covered call es el mismo que el de tener acciones: que la
> acción caiga. La prima solo amortigua la caída; no la elimina. A cambio,
> renuncias a las subidas por encima del strike. Este documento no es asesoría
> financiera.

---

## 1. Cómo funciona (en 30 segundos)

1. Tienes (o compras) **100 acciones** de una empresa. Eso es la "cobertura".
2. Vendes **1 contrato call** contra esas acciones: cobras una **prima** hoy,
   a cambio de la obligación de vender tus 100 acciones al precio **strike**
   si la acción termina por encima de él al vencimiento.
3. Resultados posibles al vencimiento:
   - **La acción queda por debajo del strike** → el call expira sin valor,
     te quedas la prima íntegra y las acciones. Repites el ciclo.
   - **La acción queda por encima del strike** → entregas las acciones al
     strike ("asignación"). Te quedas la prima **más** la ganancia hasta el
     strike. Ganaste, solo que con techo.

La prima es tuya en ambos casos. Por eso es un generador de ingresos: cada
ciclo de 30–45 días cobras, pase lo que pase con la asignación.

---

## 2. Requisitos previos

- **Capital**: mínimo 100 acciones por contrato. Con una acción de $50 son
  ~$5,000 por posición; idealmente 2–4 posiciones distintas.
- **Broker** con permisos de opciones nivel 1 (covered calls es el nivel más
  básico y el que menos margen exige).
- **Horizonte**: disposición a mantener las acciones durante meses. Si no
  quieres ser dueño de la acción, no vendas calls sobre ella.

---

## 3. Paso 1 — Selección del subyacente

Regla de oro: **vende calls solo sobre acciones que comprarías igual sin la
prima.** La prima nunca justifica tener una mala empresa.

Criterios (todos deben cumplirse):

| Criterio | Regla |
|---|---|
| Calidad | Empresa rentable y estable, o un ETF amplio (SPY, QQQ, VOO...) |
| Liquidez de opciones | Spread bid-ask del call < 5–10% de la prima; *open interest* > 500 en el strike |
| Volatilidad | Volatilidad implícita (IV) moderada. IV altísima = prima jugosa = el mercado espera un golpe. No persigas primas gordas |
| Eventos | Sin *earnings* ni eventos binarios (FDA, juicios) antes del vencimiento del ciclo |
| Precio | Preferible $20–$200 por acción para diversificar con capital razonable |

Los ETF amplios son el punto de partida más seguro: menos prima, pero sin
riesgo de quiebra de una sola empresa.

## 4. Paso 2 — Selección del contrato (reglas fijas)

- **Vencimiento (DTE)**: **30–45 días**. Es la zona donde el paso del tiempo
  (*theta*) erosiona más rápido el valor del call que vendiste, que es
  exactamente lo que te beneficia.
- **Strike / delta**: delta entre **0.20 y 0.30** (≈ 20–30% de probabilidad de
  terminar dentro del dinero). Equivale típicamente a un strike 3–8% por
  encima del precio actual.
- **Nunca por debajo de tu costo base**: si te asignan, que sea con ganancia
  en la acción, no con pérdida bloqueada.
- **Prima mínima**: que el rendimiento del ciclo sea ≥ **0.5–1%** del valor de
  las acciones (≈ 6–12% anualizado solo en primas). Si no da, busca otro
  subyacente o no operes ese mes: **no operar también es una decisión del
  sistema.**

Usa la [calculadora incluida](index.html) para verificar rendimiento del
ciclo, anualizado, breakeven y retorno si te asignan antes de vender.

## 5. Paso 3 — Gestión de la posición (aquí se gana o se pierde)

Reglas mecánicas, sin emociones:

1. **Toma de ganancias**: recompra el call cuando hayas capturado el
   **50–70% de la prima**. Ejemplo: vendiste a $1.00, recompra a $0.30–$0.50.
   El riesgo restante no compensa los centavos que quedan; libera la posición
   y vende el siguiente ciclo.
2. **Si el strike se ve amenazado** (la acción sube y el call está cerca o
   dentro del dinero):
   - **¿Quieres conservar las acciones?** → *Roll*: recompra el call y vende
     otro con strike más alto y vencimiento más lejano, **siempre por crédito
     neto** (que el roll te pague, nunca pagues por él).
   - **¿Te da igual venderlas?** → No hagas nada. Deja que te asignen: cobras
     prima + ganancia hasta el strike. Eso es una operación ganadora, no un
     fracaso.
3. **Si la acción cae fuerte** (> 8–10%): no vendas la acción en pánico ni
   "persigas" la caída vendiendo calls con strike bajo tu costo. Recompra el
   call barato (ya casi no vale nada), espera estabilización y reanuda el
   ciclo con strikes sensatos.
4. **Nunca vendas el call desnudo**: si vendes las acciones, recompra el call
   el mismo día. Sin cobertura, el riesgo es ilimitado.

## 6. Paso 4 — Después de la asignación: la rueda (*the wheel*)

Si te asignaron y quieres reentrar en la misma acción, puedes cerrar el
círculo vendiendo **puts aseguradas con efectivo** (*cash-secured puts*):

1. Vende un put con delta ~0.20–0.30 y 30–45 DTE al precio al que te gustaría
   recomprar. Cobras prima.
2. Si no te asignan, repites. Si te asignan, recompras las 100 acciones con
   descuento (strike − prima) y vuelves al paso de vender covered calls.

La rueda convierte el sistema en un ciclo continuo: cobras prima tanto al
entrar como al salir. Aplican los mismos criterios de selección del paso 3:
solo sobre acciones que quieres tener y a precios que pagarías de todas formas.

## 7. Gestión de riesgo (los límites del sistema)

- **Tamaño**: ninguna posición > **20–25%** de la cartera. Mínimo 3–4
  subyacentes distintos, idealmente de sectores diferentes.
- **Reserva de efectivo**: mantén 10–20% en efectivo para no estar forzado a
  vender en caídas (y para puts aseguradas si haces la rueda).
- **La prima no es "gratis"**: rendimientos de ciclo > 3% mensual casi siempre
  significan que estás vendiendo volatilidad de algo peligroso (meme stocks,
  biotech pre-FDA). El sistema muere por ahí.
- **Escenario malo asumido**: en un mercado bajista fuerte, un covered call
  pierde menos que solo tener las acciones (por las primas cobradas), pero
  **pierde**. Dimensiona el capital sabiendo eso.

## 8. Expectativas realistas

- Primas: **0.5–2% mensual** sobre el capital empleado con deltas 0.20–0.30.
- Anualizado en primas: **6–20%** según volatilidad del subyacente, **antes**
  de movimientos de la acción, comisiones e impuestos.
- Años laterales o levemente alcistas: el sistema tiende a batir a *buy &
  hold*. Años fuertemente alcistas: quedas por debajo (te asignan y pierdes
  parte de la subida). Años bajistas: pierdes menos, pero pierdes.

## 9. El ciclo mensual (checklist repetible)

Este es "el sistema": la misma rutina cada ciclo, sin excepciones.

- [ ] **Día 1** — Revisar calendario de earnings/eventos de cada subyacente.
- [ ] **Día 1** — Para cada 100 acciones libres: vender call 30–45 DTE, delta
      0.20–0.30, strike ≥ costo base, rendimiento ≥ 0.5% del ciclo.
- [ ] **Semanal** — Revisar posiciones 1–2 veces por semana (no a diario):
      ¿alguna prima ya capturó 50–70%? → recomprar y esperar/reabrir.
- [ ] **Si el strike es amenazado** — decidir con la regla del paso 5.2:
      roll por crédito o aceptar asignación.
- [ ] **Al vencimiento** — anotar resultado en el registro; si hubo
      asignación, decidir: recomprar acciones, vender put asegurada, o rotar
      a otro subyacente.
- [ ] **Fin de mes** — actualizar métricas del registro y verificar límites de
      tamaño de posición.

## 10. Registro (lo que no se mide no se repite)

Lleva una hoja con una fila por operación:

`fecha venta · subyacente · nº contratos · strike · DTE · prima cobrada ·
delta al abrir · fecha cierre · costo de recompra · resultado neto ·
% del ciclo · asignado (sí/no) · notas`

Métricas mensuales: prima neta cobrada, % sobre capital, tasa de asignación,
% de operaciones cerradas al 50–70%. Si la tasa de asignación supera ~30%
sostenidamente, estás vendiendo deltas demasiado altos.

## 11. Errores comunes que rompen el sistema

1. Elegir la acción por la prima y no por la empresa.
2. Vender strikes por debajo del costo base "porque la prima es mejor".
3. No tomar ganancias al 50–70% y devolverlas en la última semana.
4. Hacer rolls pagando débito para "no perder las acciones".
5. Vender calls atravesando earnings sin saberlo.
6. Concentrar todo en un solo subyacente porque "lo conoces bien".
7. Confundir techo de ganancias con pérdida: ser asignado con prima + ganancia
   hasta el strike **es el sistema funcionando**.

---

## Herramientas incluidas

📊 **[Calculadora de covered calls](index.html)** — introduce precio, strike,
prima y días al vencimiento y obtén: ingreso por prima, rendimiento del ciclo,
anualizado, breakeven, retorno si asignado, diagrama de payoff comparado con
solo tener las acciones, y tabla de escenarios.

⚙️ **[Orquestación en Activepieces](activepieces/README.md)** — carpeta con 5
flujos importables que automatizan el ciclo: candidatos al abrir ciclo,
vigilancia de las reglas 50–70% y de strikes amenazados, registro de
operaciones por webhook, informe mensual de métricas y alertas de earnings.

*Nada de lo anterior constituye asesoría financiera. Opera con capital que
puedas mantener invertido y entiende cada regla antes de usarla.*
