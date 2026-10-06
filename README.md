# IoT Operations Center

Panel para seguir sensores de **temperatura** y **humedad** en tiempo real. Cada lectura llega por MQTT, se guarda y aparece en el navegador: qué sensor está en línea, cómo van sus valores y si hay una alerta.

El repositorio trae el sistema completo. Para verlo sin hardware se usa un simulador que publica las mismas mediciones que enviaría un sensor.

## Problema que resuelve

Un sensor solo entrega números. Para operar un espacio hace falta saber, sin leer esos mensajes a mano:

- qué equipos están conectados y cuáles dejaron de reportar;
- la temperatura y la humedad recientes de cada uno;
- cuándo un valor se sale de lo normal;
- quién puede mirar, quién puede cerrar una alerta y quién administra dispositivos y usuarios.

IoT Operations Center recibe esa telemetría, la guarda, abre alertas y las muestra en un panel con inicio de sesión.

## Funcionalidades

- Inicio de sesión con tres perfiles: consulta, operación y administración.
- Dashboard en vivo: dispositivos, online, offline, alertas abiertas y mediciones de la última hora. La gráfica de temperatura y la tabla se actualizan solas.
- Lista y ficha de cada sensor. El administrador puede crearlos, editarlos y eliminarlos.
- Alertas cuando la temperatura supera el umbral o cuando el modelo marca un patrón anómalo. El operador puede resolverlas.
- Detección por dispositivo con Isolation Forest, a partir del historial de lecturas.
- Simulador de sensores para probar el panel antes de conectar equipos reales.
- Arranque del stack con Docker Compose: broker, base de datos, API, ingestión y web.

| Rol | Qué puede hacer |
|-----|-----------------|
| viewer | Ver el dashboard, los dispositivos y las alertas |
| operator | Lo mismo, y resolver alertas |
| admin | Lo mismo, más alta, edición y baja de dispositivos, y alta de usuarios |

## Tecnologías

| Para qué | Qué se usa |
|----------|------------|
| Pantalla | Angular 19, TypeScript |
| API | Python, FastAPI |
| Acceso | JWT y bcrypt |
| Mensajes de los sensores | MQTT (Eclipse Mosquitto) |
| Actualización en vivo | WebSocket |
| Datos | PostgreSQL 16 |
| Anomalías | scikit-learn (Isolation Forest) |
| Publicación | Nginx y Docker Compose |

## Arquitectura

1. El sensor (o el simulador) publica temperatura, humedad y su estado por MQTT.
2. Mosquitto reparte el mensaje.
3. La ingestión lo valida, lo guarda en PostgreSQL y, si corresponde, crea una alerta.
4. La API sirve el historial, el login y los dispositivos, y reenvía lo nuevo al navegador por WebSocket.
5. Nginx entrega la aplicación Angular.

```text
Sensores o simulador
        │
        ▼
   Mosquitto
        │
        ├── Ingestión ──► PostgreSQL
        │
        └── FastAPI ──► PostgreSQL
                │
                ▼
             Nginx + Angular
```

Un sensor real publica en `iot/devices/<id>/telemetry` un JSON con `device_id`, `timestamp`, `temperature` y `humidity`, y su estado en `iot/devices/<id>/status`. El broker escucha en el puerto 1883.

### Carpetas

| Carpeta | Qué hay |
|---------|---------|
| `frontend/angular-app` | Login, dashboard, dispositivos y alertas |
| `backend` | API, base de datos, ingestión MQTT y detección de anomalías |
| `simulator` | Sensores de prueba que publican en Mosquitto |
| `infrastructure` | Configuración de Mosquitto y de Nginx |
| `docker-compose.yml` | Servicios que se levantan juntos |

## Instalación

Hace falta Docker con Docker Compose.

```bash
docker compose up -d --build
```

- Panel: http://localhost/
- Documentación de la API: http://localhost:8000/docs
- MQTT: `localhost:1883`

La primera vez la API crea las tablas y los usuarios de acceso. El panel se llena cuando llega telemetría. Con el simulador, en otra terminal:

```bash
cd simulator
py -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python simulator.py
```

Para forzar una lectura anómala de un sensor:

```bash
.\.venv\Scripts\python simulator.py --force-anomaly SENSOR-001
```

Para trabajar el frontend sin reconstruir la imagen, hace falta Node.js:

```bash
cd frontend/angular-app
npm start
```

Esa copia queda en http://localhost:4200 y usa la API del puerto 8000.

### En un servidor

1. Clonar el repositorio.
2. Cambiar `JWT_SECRET` y la contraseña de Postgres en `docker-compose.yml` antes de exponerlo.
3. Ejecutar `docker compose up -d --build`.
4. Abrir el puerto 80. El 1883 solo si los sensores están fuera del servidor.
5. Opcional: TLS con Certbot delante de Nginx.

## Autora

**naohan** — [hannohemi@gmail.com](mailto:hannohemi@gmail.com)
