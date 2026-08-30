# 09 — Decisiones no negociables

1. `insumos/` es inmutable.
2. BR-CONAF se conserva como baseline separado.
3. No llamar “alta resolución meteorológica” a un simple resampling.
4. H3-8 es la unidad operacional inicial.
5. H3-9 es experimental hasta validación.
6. El test 2022–2024 permanece ciego durante selección/tuning.
7. No se permite leakage temporal.
8. Las probabilidades publicadas deben estar calibradas.
9. Python no es una dependencia obligatoria del request path.
10. PostgreSQL/PostGIS no entra al MVP sin un caso de uso que lo justifique.
11. Credenciales GEE/R2/Railway nunca llegan al navegador ni al Git.
12. No interpolar flags binarios/categorías con bilinear.
13. Cada corrida y cada modelo se versionan.
14. Cada tecnología nueva debe demostrar aporte fuera de muestra.
15. La interfaz debe diferenciar probabilidad, severidad/potencial y confianza.
16. El producto comunal se deriva del sistema subcomunal, no al revés.
17. No cortar la identidad H3; usar tabla H3↔comuna con fracciones.
18. El resultado de gran incendio es un modelo condicional separado de ignición.
19. La complejidad se añade por fases y ablation studies.
20. Los originales siempre deben permitir reconstruir todo el pipeline.
