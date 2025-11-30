# AGENTS.md

Este archivo replica las reglas definidas en `.cursor/rules` para que los agentes sin acceso directo a Cursor tengan el mismo contexto.

## BloodHound MCP Usage

- Usa la base de conocimiento de BloodHound MCP como primera fuente de verdad para sintaxis de consultas, tipos de relaciones, endpoints y compatibilidad de funcionalidades.
- Ante dudas de sintaxis Cypher o contratos REST, consulta el recurso MCP en vez de asumir.
- Documenta hallazgos relevantes (formas de consulta, limitaciones) en comentarios o en el README cuando afecten las decisiones de implementación.
- Prefiere ejemplos de la documentación MCP para componer o validar cláusulas `MATCH`, `WHERE` y recorridos de relaciones.
- Si la información falta en MCP, indícalo explícitamente y solicita aclaración o reúne evidencia manual mediante pruebas.

## Configuration Management

- Guarda secretos y valores específicos de cada entorno en archivos `.env` excluidos del control de versiones (revisa `.env.example` para mantener los mismos campos).
- Modela la configuración con `pydantic-settings` para que las opciones de CLI, variables de entorno y `.env` se validen automáticamente.
- Centraliza la carga de configuración en un único módulo (por ejemplo `core/settings.py`) y reutiliza esas settings en los comandos.
- Documenta cualquier variable de entorno nueva en `README.md` y actualiza `.env.example`.

## Dependencies Management

- Usa `uv` para toda operación de dependencias: `uv pip install`, `uv pip compile`, `uv sync` (evita `pip` directamente).
- Actualiza los lockfiles ejecutando `uv pip compile pyproject.toml --output-file requirements.lock` cuando cambien las dependencias.
- Documenta nuevas dependencias en `README.md` (sección de dependencias) con el comando utilizado para instalarlas.

## Error Checks

- Después de cambiar código Python, ejecuta `uv run ruff check` y `uv run pylint src/bloodhound_cli` antes de dar la tarea por finalizada.
- Acompaña cualquier supresión de lint con un comentario que explique por qué es segura.

## Error Handling and Logging

- Envuelve E/S externa (red, sistema de archivos, subprocesos) en bloques `try/except`; propaga las excepciones inesperadas tras registrarlas.
- Configura y reutiliza `structlog` para el logging (ver `src/bloodhound_cli/core/logging_utils.py` cuando exista) y registra a nivel `error` con identificadores contextuales (comando, IDs, endpoint).
- Al recuperarte de una excepción incluye el mensaje original con `exc_info=True` (o `structlog.exception()`) para conservar el traceback.
- Añade contexto estructurado (campos estilo diccionario) para facilitar filtrado; evita `print` en rutas de error y usa la consola Rich solo para resúmenes al usuario.

## General Python Development

- Antes de modificar código inspecciona los módulos existentes en `src/bloodhound_cli` para entender patrones actuales y reutilizar helpers compartidos.
- Escribe funciones y clases componibles con responsabilidades claras; evita scripts monolíticos.
- Automatiza tareas repetitivas del CLI extendiendo las herramientas en `scripts/` en vez de comandos ad-hoc en docs o comentarios.

## Project Structure

- Mantén el código de runtime en `src/bloodhound_cli/`, las pruebas en `tests/`, la documentación en `docs/` y la configuración en `.cursor/` o `config/`.
- Al introducir un módulo nuevo, añade pruebas en `tests/` y actualiza los `__init__.py` para exponer APIs públicas intencionalmente.
- No coloques scripts ejecutables en la raíz del proyecto; agrégalos a `scripts/` y documenta su uso en el README.

## Python AI-Friendly Coding Practices

- Cuando compartas código en respuestas, incluye fragmentos cortos con explicación previa de la intención.
- Usa nombres de variables y funciones descriptivos que reflejen conceptos del dominio.
- Añade anotaciones de tipo en firmas y variables complejas.
- Comenta la lógica no trivial enfocándote en el “por qué”.
- Registra o lanza errores con contexto accionable (parámetros de entrada, endpoints, IDs) para simplificar el triage.

## Python Architecture

- Diseña módulos separados para modelos, servicios, controladores y utilidades.
- Aplica el Principio de Responsabilidad Única.
- Respeta el principio DRY.

## Python Code Formatting

- Usa Black para el formateo.
- Usa Pylint para linting.
- Sigue PEP 8 y las reglas específicas del proyecto.

## Python Documentation

- Añade docstrings a nivel de módulo que resuman propósito y puntos de entrada públicos principales.
- Documenta cada clase y función pública con docstrings estilo Google (`Args`, `Returns`, `Raises` cuando aplique).
- Actualiza la documentación inline cada vez que cambien comportamientos o parámetros; evita ejemplos obsoletos.
- Incluye ejemplos de uso en docstrings cuando las APIs sean no triviales (puedes referenciar `docs/`).

## Python General Coding Style

- Prefiere funciones independientes para helpers sin estado; introduce clases solo al encapsular estado/comportamiento.
- Aplica estilo con `uv run ruff check --fix`.
- Habilita `ruff --unsafe-fixes` solo tras revisar el diff.
- Usa indentación de 4 espacios.
- Mantén líneas ≤ 120 caracteres salvo que afecte la legibilidad.
- Usa `#` para comentarios de una línea y `"""` para docstrings; reserva comentarios en bloque para explicaciones multilínea.
- Cuando agregues comentarios, explica la intención o casos borde en vez de parafrasear el código.

## Python General Rules

- Añade anotaciones de tipo (incluidos returns) a todas las funciones o métodos nuevos o modificados.
- Escribe docstrings PEP 257 para módulos, clases y funciones públicas; actualízalos si cambia su comportamiento.
- Conserva los comentarios existentes a menos que sean incorrectos; mejora la claridad en lugar de borrar contexto.
- Usa pytest bajo `tests/` para todas las pruebas automatizadas; evita suites basadas en unittest.
- Añade docstrings breves a las pruebas describiendo el escenario y anota fixtures/helpers cuando su tipo no sea obvio.
- Importa helpers de tipado de pytest bajo un bloque `TYPE_CHECKING` cuando sea necesario.
- Aplica `uv run ruff check` y da formato con `uv run ruff format` (o Black si está configurado) antes de abrir un PR.

## Python Naming Conventions

- snake_case para variables y funciones.
- PascalCase para clases e interfaces.
- snake_case para nombres de archivo.

## Python Testing with pytest

- Ubica las nuevas pruebas en `tests/` reflejando la estructura del paquete fuente (por ejemplo `tests/core/test_ce_client.py`).
- Usa fixtures de pytest para setup/teardown; evita `unittest.TestCase` o estado global.
- Ejecuta `uv run pytest --maxfail=1 --disable-warnings` antes de terminar el trabajo y documenta fallos en las notas de la tarea.
- Prefiere tests parametrizados para cubrir múltiples entradas sin duplicación.
