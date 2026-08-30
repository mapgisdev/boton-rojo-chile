# Reglas del workspace BR-HR

## Siempre
- Lee `GEMINI.md` y `docs/` antes de cambios estructurales.
- Trata `insumos/` como inmutable.
- Usa datos derivados en `data/derived/` o `work/`.
- Mantén baseline y modelo mejorado separados.
- Añade pruebas de regresión antes de modificar lógica existente.
- Registra supuestos en `docs/generated/DECISION_LOG.md`.
- Mantén UTC y hora local explícitos.
- Usa semilla reproducible para cualquier muestreo.
- Separa train/validation/test por tiempo.
- Mantén el test 2022–2024 cerrado hasta selección final.
- Verifica documentación oficial antes de integrar servicios externos.

## Nunca
- No escribas secretos en el repositorio.
- No uses variables posteriores al incendio para predecir ignición.
- No llames “250 m meteorológicos” a una grilla derivada.
- No uses interpolación bilinear para flags binarios/categorías.
- No añadas PostGIS solo por convención.
- No sustituyas el baseline original por el modelo nuevo.
- No publiques probabilidades no calibradas como probabilidades absolutas.
- No borres datos fuente para “limpiarlos”.
- No uses el test ciego para tuning.

## Forma de trabajo
Para cambios de arquitectura:
1. inspeccionar;
2. documentar;
3. proponer plan;
4. implementar pequeño;
5. probar;
6. medir;
7. documentar resultado.
