# Notas de migración

## Estado inicial

- La wiki remota en PBworks no devuelve fácilmente el contenido público desde herramientas automáticas.
- Se rescataron localmente dos páginas HTML: portada y programa.
- El resto del sitio todavía depende de enlaces a PBworks.

## Prioridades

1. Migrar `Trabajos prácticos`.
2. Migrar `Material complementario`.
3. Traer las páginas temáticas más citadas desde el programa.
4. Recién después mover o descargar adjuntos pesados.

## Criterios

- Mantener `orginal/` como respaldo de fuente.
- Evitar editar los HTML históricos.
- Usar páginas nuevas y limpias para el sitio final.
- Reescribir enlaces internos sólo cuando la página de destino ya exista localmente.

## Publicación

Pensado para un repo estático simple, compatible con GitHub Pages.
