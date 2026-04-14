# Astronomía Estelar · FCAGLP · UNLP

Sitio de la cátedra de Astronomía Estelar de la Facultad de Ciencias Astronómicas y Geofísicas de la UNLP.

Publicado en [GitHub Pages](https://astronomia-estelar-unlp.github.io/web/).

## Contenido

Programa de la materia, trabajos prácticos, material complementario y recursos de la cursada.

## Estructura

- `orginal/`: copia histórica del material rescatado de PBworks.
- `index.html`: nueva portada local.
- `programa.html`: versión migrada del programa.
- `trabajos-practicos.html`: landing local para la futura migración de prácticas.
- `material-complementario.html`: landing local para recursos anexos.
- `enlaces-pendientes.html`: inventario inicial para continuar el traspaso.
- `assets/styles.css`: estilos comunes del sitio.
- `docs/migracion.md`: notas operativas para seguir trabajando.

## Flujo recomendado

1. Guardar primero la fuente cruda en `orginal/`.
2. Crear la versión limpia en una página local nueva.
3. Reemplazar enlaces internos de PBworks por URLs locales.
4. Dejar los archivos o páginas aún no migrados apuntando a la fuente original hasta completar el reemplazo.
5. Publicar cuando la navegación principal ya no dependa de PBworks.

## Publicación sugerida

La opción más simple es usar un repositorio dedicado con GitHub Pages sirviendo desde la raíz.

## Nota

El directorio `orginal/` se mantuvo con su nombre actual para no tocar la evidencia fuente durante esta primera etapa. Si querés, después lo renombramos a `original/` y actualizamos referencias.
