# Vanessa Bot - README Final

## Resumen del Proyecto
Vanessa Bot es un asistente virtual modular para Recursos Humanos en Vanity/Soul, construido con una arquitectura desacoplada. Temporalmente, el bot solo envía solicitudes vía webhooks a n8n sin esperar respuesta inmediata, enfocándonos en flujos conversacionales dinámicos. La DB está removida inicialmente, con roadmap para implementar persistencia externa o nativa.

## Nueva Estructura del Proyecto
- **main.py**: Orquestador puro que registra handlers y coordina módulos. No contiene lógica de negocio.
- **/modules/**: Módulos especializados (rh_requests.py, flow_builder.py, ui.py, logger.py, ai.py, finalizer.py).
- **/conv-flows/**: Archivos JSON que definen flujos conversacionales (e.g., horario.json).
- **.env.example**: Variables de entorno (Telegram token, webhooks; sin DB).
- **requirements.txt**: Dependencias Python.
- **Docker**: Para despliegue (Dockerfile, docker-compose.yml).
- **Archivos eliminados**: db_logic.md, bot_brain.md, Vanessa.md, Readme.md (original), models/, init/ (temporalmente, ya que DB está fuera).

## Arquitectura y Funcionamiento
### Flujo Actual (Temporal: Solo Envío de Webhooks)
1. Usuario inicia comando (e.g., /vacaciones).
2. main.py enruta a handler en módulo.
3. Módulo procesa conversación, valida, envía webhook a n8n.
4. n8n procesa y guarda en DB remota.
5. Bot responde inmediatamente al usuario (sin esperar confirmación).

### Nuevo Enfoque Propuesto (Bidireccional)
Cambiar a webhooks bidireccionales donde el bot espera respuesta de n8n antes de notificar al usuario, garantizando persistencia.

## Componentes Clave
### 1. main.py
- Registra comandos y handlers desde módulos.
- Setup de Telegram bot.

### 2. /modules
- **rh_requests.py**: Solicitudes de vacaciones/permisos; envía webhooks.
- **flow_builder.py**: Carga y ejecuta flujos desde JSON en /conv-flows.
- **ui.py**: Teclados y menús.
- **logger.py**: Logging.
- **ai.py**: Clasificación IA.
- **finalizer.py**: Finaliza flujos.

### 3. /conv-flows
- JSON con steps: state, type (keyboard/text/info), question, options, next_step.
- Ejemplo: horario.json para definir horarios.

## Roadmap
### Fase 1 (Actual): Sin DB, Webhooks Unidireccionales
- Flujos conversacionales funcionales.
- Envío de payloads a n8n.

### Fase 2: Webhooks Bidireccionales
- Agregar receptor de webhooks (Flask en main.py).
- Esperar respuesta de n8n para confirmar usuario.
- Storage temporal para solicitudes pendientes.

### Fase 3: Implementar DB
- DB nativa (SQLite/PostgreSQL) o acceso remoto en VPS.
- Persistencia local para reporting.

### Fase 4: Escalabilidad y Mejoras
- Manejo concurrente, logging avanzado, integraciones.

## Instalación y Ejecución
1. Clonar repo.
2. `cp .env.example .env` y configurar (TOKEN, WEBHOOK_*).
3. `pip install -r requirements.txt`
4. `python main.py` o `docker-compose up`

## Problema Actual y Solución
- **Problema**: Pérdida de datos en DB al mover desde n8n.
- **Temporal**: Bot responde inmediatamente.
- **Futuro**: Esperar confirmación para asegurar persistencia.

## Beneficios del Approach
- Modularidad: Fácil extender.
- Desacoplamiento: Sin DB local inicial.
- Escalabilidad: Webhooks para cualquier backend.
- Mantenibilidad: Código limpio.

## Pasos de Implementación (Detalle en new_plan.md)
- Análisis de flujo actual.
- Diseño bidireccional.
- Agregar receptor webhooks.
- Modificar módulos.
- Storage pendiente.
- Actualizar n8n.
- Pruebas.

## Timeline
- Análisis: 1-2 días
- Diseño: 1 día
- Implementación: 3-5 días
- Pruebas: 2-3 días

## Consideraciones Técnicas
- Timeout para callbacks.
- Seguridad en webhooks.
- Escalabilidad con Redis si necesario.