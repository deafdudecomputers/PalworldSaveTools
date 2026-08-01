<div align="center">

![PalworldSaveTools Logo](../assets/branding/PalworldSaveTools_Blue.png)

# PalworldSaveTools

**Un kit de herramientas completo para editar archivos de guardado de Palworld**

[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldTools/releases/latest)
[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)
[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)

[English](../../README.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md) | [Português (Brasil)](README.pt_BR.md) | [Português (Portugal)](README.pt_PT.md)

---

### **Descarga la versión independiente de [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)** 

---

</div>
<div align="center">

## Descripción general

<img src="https://readme-typing-svg.demolab.com?lines=%C2%BFQu%C3%A9+es+exactamente+esto%3F;Tu+salvaci%C3%B3n%2C+a+tu+manera;Una+herramienta+para+gobernarlos+a+todos&center=true&width=490&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Palworld Save Tools (PST) es una rápida aplicación de escritorio todo en uno para inspeccionar y editar archivos guardados de Palworld. Construido con Python y PySide6, lee y escribe el formato de guardado comprimido del juego directamente, sin necesidad de modificaciones del juego.

Ya sea que necesite administrar un servidor dedicado, migrar entre servidores cooperativos y dedicados, limpiar datos abandonados o ajustar Pals individual, PST proporciona una única interfaz unificada para todo ello.

### Destacados

- **Multiplataforma**: archivos binarios prediseñados para **Windows**, **Linux** y **macOS**.
- **Análisis nativo rápido**: uno de los lectores de archivos guardados más rápidos disponibles, impulsado por el motor [`palsav`](src/palsav).
- **Mapa visual**: mapa mundial interactivo con marcadores de base/jugador, zonas de exclusión y calibración de coordenadas.
- **Edición profunda de Pal**: control total sobre estadísticas, IVs, almas, habilidades, passives, idoneidades laborales, rango y banderas de apariencia.
- **Herramientas de nivel de servidor**: eliminación, limpieza, conversión y transferencia de caracteres en masa diseñadas para administradores.
- **Copias de seguridad automáticas**: cada operación de guardado crea una copia de seguridad antes de escribir.
- **9 idiomas**: interfaz de usuario localizada, guías en la aplicación y documentación.





---





## Índice

- [Descripción general](#descripción-general)
- [Características](#características)
- [Instalación](#instalación)
- [Inicio rápido](#inicio-rápido)
- [Guías](#guías)
- [Solución de problemas](#solución-de-problemas)
- [Construyendo desde la fuente](#construyendo-desde-la-fuente)
- [Contribuyendo](#contribuyendo)
- [Licencia](#licencia)
- [El equipo de Palworld](#el-equipo-de-palworld)
- [Construyendo desde la fuente] (#construcción-desde-la-fuente)
- [Contribuyendo](#contribuyendo)
- [Descargo de responsabilidad](#descargo de responsabilidad)
- [Soporte](#soporte)
- [Licencia](#licencia)
- [El equipo Palworld](#el-equipo-palworld)
- [Agradecimientos](#agradecimientos)





---




<div align="center">

## Características

<img src="https://readme-typing-svg.demolab.com?lines=las+cosas+buenas;Compru%C3%A9balo;Lleno+de+herramientas&center=true&width=290&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

| Categoría | Qué puedes hacer |
|---|---|
| **Gestión de jugadores** | Edite nombres, niveles, estadísticas, puntos tecnológicos. Gestión masiva de elementos, pals, tecnología entre jugadores. Limpiar jugadores inactivos o duplicados. |
| **Pal Editor** | Cambiar estadísticas, IVs, almas, rango, habilidades, passives, idoneidad laboral, jefe/banderas de la suerte. Exportar/importar pals. Detectar y reparar pals ilegal. Modo trampa para edición sin límites. |
| **Gestión del gremio** | Cambie el nombre de los gremios, cambie los líderes, establezca niveles. Desbloquea la investigación de laboratorio. Mueve jugadores entre gremios. Elimina gremios vacíos o inactivos. |
| **Herramientas del campamento base** | Ver todas las bases con información del gremio. Exportar/importar planos. Clonar bases a otros gremios. Reposicionar bases en el mapa. Ajustar el radio. Eliminar bases inactivas. |
| **Visor de mapas** | Mapa mundial interactivo con marcadores de base y jugadores. Dibujar zonas de exclusión. Modo de calibración. Vistas de mapa mundial y mapa de árbol. Zoom, panorámica, vuelo hacia. |
| **Gestión de inventario** | Edite elementos de jugador, elementos clave y espacios para equipos. Desbloquea todos los puntos de viaje rápido. Explore y edite inventarios básicos y contenedores en todos los gremios. Administrar el trabajador base pals. |
| **Exclusiones** | Proteja a los jugadores, gremios y bases de la limpieza con listas de exclusión persistentes. Agregue entradas desde los menús contextuales. |
| **Guardar herramientas** | Convierte archivos guardados entre SAV y JSON. Convierta GamePass a Steam. Transfiere personajes entre mundos. Arreglar los guardados del host. Restaurar el progreso del mapa. Amplíe las ranuras de palbox. |
| **Limpieza y servicios públicos** | Eliminar gremios vacíos, bases/jugadores inactivos, datos sin referencia. Eliminar elementos/pals/estructuras no válidos. Restablecer mazmorras, plataforma petrolera, entregas de suministros. Corregir marcas de tiempo. |

### Gestión de jugadores

- Ver y buscar todos los jugadores por nombre, nivel, recuento de pal, UID, gremio y hora de la última vez que fueron vistos.
- Editar nombres de jugadores, niveles, estadísticas y puntos de tecnología.
- **Pestaña Estadísticas**: estadísticas del héroe (salud, resistencia, ataque, defensa, velocidad de trabajo, peso) con valores correctos calculados en el juego; Habilidades de reliquia con palancas y giradores.
- **Máximo de todas las estadísticas**: limita instantáneamente todas las estadísticas al máximo (50 puntos).
- **Operaciones masivas** entre varios jugadores: gestión de elementos, gestión de pal y desbloqueo de tecnología.
- Eliminar jugadores inactivos por umbral de tiempo; eliminar duplicados.

### Pal Editor

Una interfaz de edición profunda para cualquier Pal propiedad de cualquier jugador. Pals están organizados por **Grupo** (equipo activo) y **Palbox** (almacenamiento).

- **Estadísticas y IVs**: HP, ataque, defensa (IV 0–100), nivel (1–80), rango de confianza (0–10).
- **Almas**: HP, ataque, defensa, velocidad de artesanía (0–20).
- **Habilidades** — Selector de habilidades activo; aprender todos los movimientos; Habilidades de sincronización masiva en Pals.
- **Rasgos pasivos**: selector pasivo con datos completos del juego.
- **Idoneidad para el trabajo**: establezca niveles individuales de idoneidad para el trabajo (0 a 10).
- **Banderas de apariencia**: alterna entre Jefe/Alfa, Afortunado/Brillante, Depredador, Despertado e Importado/ADN.
- **Clasificación y bloqueo**: establece el rango y el nivel de bloqueo de favoritos (0–3).
- **Modo de trampa**: alternar para expandir todo en mayúsculas: nivel, IVs, almas, rango del condensador a 255; Desbloquea habilidades activas/pasivas ilimitadas y se permiten duplicados.
- **Exportar/Importar**: haga clic con el botón derecho en cualquier pal para exportarlo como `.pstpal` (comprimido) o `.json`. Importe a espacios vacíos entre los trabajadores del grupo, palbox, DPS o base. Funciona entre partidas guardadas y jugadores.
- **Max All Pals**: maximiza todas las estadísticas (IVs, almas, rango, nivel) para todos los pals del grupo, todas las páginas de palbox o todos los trabajadores de la base; respeta los límites del modo trampa.
- **Reparar Pals** ilegal: detecta y limita a pals con estadísticas, habilidades o rasgos ilegales por jugador.
- **Clonar/Eliminar masivamente**: cuadro de diálogo de selección de especies con controles de cantidad y alternancia de fuentes (Party/Palbox/DPS) para operaciones por lotes.
- Agregue un nuevo Pals o elimine rápidamente con doble clic.

### Gestión del gremio

Vista de dos paneles: lista de gremio en la parte superior, lista de miembros debajo.

- Cambiar el nombre de los gremios, cambiar líderes, establecer el nivel del gremio, el nivel máximo del gremio.
- Desbloquear todas las investigaciones de laboratorio; reconstruir todos los gremios.
- Mover jugadores entre gremios; eliminar gremios vacíos o inactivos.

### Herramientas del campamento base

- Ver todos los campamentos base con asociación de gremio.
- **Exportar** planos base a `.json`; **importar** (archivo único o múltiple) a cualquier gremio.
- **Clonar** bases para otros gremios con posicionamiento desplazado.
- **Cambiar coordenadas**: haz clic derecho en un marcador de base en el mapa, selecciona "Cambiar coordenadas" y luego haz clic en cualquier lugar para teletransportar la base.
- **Empujar base**: empuja una base mediante desplazamientos X/Y/Z exactos para corregir el recorte o la flotación del suelo.
- **Ajustar el radio base** (50%–1000%).
- Eliminar bases inactivas y objetos de mapa que no sean bases.

### Visor de mapas

Visualización interactiva de todo tu mundo.

- Marcadores de base (icono de casa) y marcadores de jugador (icono de persona) con paneles de detalles.
- Alternar superposiciones: bases, jugadores, anillos de radio, zonas de exclusión.
- **Dibujo de zonas**: dibuja zonas de exclusión rectangulares o poligonales directamente en el mapa.
- **Modo de calibración**: alinea con precisión el mapa con las coordenadas del juego.
- Vistas del mapa mundial y del mapa de árboles; filtrar por gremio o nombre de jugador.
- Zoom (1,0x–30,0x), panorámica, doble clic para volar hasta un marcador.
- Marcadores de clic derecho y espacio vacío para acciones de gestión.

### Gestión de inventario

**Inventario de jugadores** — Tres subpestañas:
- *Inventario* — Todos los artículos y equipos en la bolsa principal; editar cantidad, agregar, eliminar.
- *Objetos clave*: elementos de misión, efigies y tecnología; agregue en masa todas las efigies/elementos clave.
- *Estadísticas*: nivel, HP, resistencia, ataque, defensa, velocidad de trabajo, peso.
- Panel de equipo para ranuras para armas, accesorios, alimentos, armaduras, escudos, planeadores y módulos.
- Desbloquea todos los mapas + puntos de viaje rápido con un solo clic.

**Inventario base**: busque y administre artículos y trabaje Pals en todas las bases:
- Ver/editar elementos en contenedores; contenedores transparentes; modificar las ranuras del contenedor.
- Operaciones de elementos entre gremios (buscar/eliminar elementos en todos los gremios).
- Eliminación de estructura entre gremios.
- Subpestaña **Base Pals**: administra el Pals de trabajo asignado a cada base con menús contextuales completos del editor pal.

### Exclusiones

Listas de protección que protegen a los jugadores, gremios y bases de las operaciones de limpieza.

- Tres paneles uno al lado del otro: UID de jugador, ID de gremio e ID de base excluidos.
- Agregue entradas mediante menús contextuales al hacer clic derecho en las pestañas Jugadores, Gremios o Bases.
- Guardar y cargar listas de exclusión de forma persistente.
- Cree su lista **antes** de ejecutar la limpieza masiva.

### Guardar herramientas

Accesible desde la pestaña **Herramientas** como tarjetas en las que se puede hacer clic:

| Herramienta | Descripción |
|------|-------------|
| **Convertir guardados** | Convertir entre formatos SAV y JSON |
| **Convertir GamePass → Steam** | Convertir archivos guardados de Xbox/GamePass al formato Steam |
| **Convertir SteamID** | Convierta ID de Steam a UID de Palworld |
| **Restaurar mapa** | Aplicar el progreso del mapa completamente desbloqueado a todos los mundos/servidores |
| **Inyector de ranura** | Aumentar espacios de palbox por jugador |
| **Modificar Guardar** | Abrir y modificar datos guardados sin procesar |
| **Transferencia de personaje** | Transferir personajes entre diferentes mundos/servidores (guardado cruzado) |
| **Reparar el guardado del host** | Intercambiar UID entre dos jugadores (intercambio de host, migración de plataforma) |

### Funciones de limpieza y utilidades

Accesibles a través de **Menú → Funciones**, estas operaciones de nivel de servidor incluyen:

- **Eliminación**: elimina gremios vacíos, bases/jugadores inactivos, jugadores duplicados y datos sin referencia.
- **Limpieza**: elimina elementos no válidos/modificados, pals y passives no válidos, estructuras no válidas; arreglar pals ilegal (límite al máximo legal); restablecer las torretas antiaéreas; desbloquear private chests; reparar todas las estructuras.
- **Restablecimientos**: reinicio de misiones, mazmorras, plataforma petrolera, invasor y entrega de suministros.
- **Marcas de tiempo**: corrige marcas de tiempo negativas; restablecer los tiempos del jugador.
- **PalDefender** — Genera comandos `killnearestbase`.





---




<div align="center">

## Instalación

<img src="https://readme-typing-svg.demolab.com?lines=Hazlo+funcionar+en+minutos;Descargar+y+listo;No+se+requiere+configuraci%C3%B3n&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Compilaciones independientes (recomendadas)

Los binarios prediseñados están disponibles para las tres plataformas principales desde [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest):

| Plataforma | Descargar | Requisitos |
|----------|----------|--------------|
| **Windows** | `PalworldSaveTools-*.exe` | Windows 10/11, [VC++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015-2022) |
| **Linux** | `PalworldSaveTools-*-linux.AppImage` | Cualquier distribución moderna |
| **macOS** | `PalworldSaveTools-*-macos.dmg` | macOS 12+ (Monterey o posterior) |

También disponible en [Nexus Mods](https://www.nexusmods.com/palworld/mods/3190).

1. Descargue la versión adecuada para su plataforma.
2. Extraiga (si está archivado) y ejecute el ejecutable.
3. Eso es todo: no se necesitan Python ni dependencias.

> **Windows:** Si ve "No se encontró VCRUNTIME140.dll", instale [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170).

> **Linux:** Es posible que necesites marcar el archivo como ejecutable: `chmod +x PalworldSaveTools-*-linux.AppImage`

> **macOS:** Si Gatekeeper bloquea la aplicación, haga clic derecho → **Abrir** la primera vez o ejecute `xattr -d com.apple.quarantine /path/to/app`.

### Desde la fuente (todas las plataformas)

PST usa [`uv`](https://docs.astral.sh/uv/) para la gestión de dependencias. El script de inicio crea automáticamente un entorno virtual e instala todo.

**Requisitos previos:** [Python 3.11+](https://www.python.org/) y [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv run start.py
```

**Windows** (lanzador de doble clic):
```
start.cmd
```

El iniciador crea un `.venv`, instala dependencias a través de `uv sync` e inicia la aplicación. Limpia el archivo de bloqueo al salir para que cada ejecución sea reproducible.





---




<div align="center">

## Inicio rápido

<img src="https://readme-typing-svg.demolab.com?lines=Cargar.+Editar.+Ahorrar.+As%C3%AD+de+sencillo.;Tres+pasos+hacia+la+gloria;es+asi+de+facil&center=true&width=450&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

1. **Carga tu guardado**
   - Haga clic en **Menú → Cargar Guardar**, o arrastre y suelte un archivo `.sav` en la ventana.
   - Navegue hasta su carpeta de guardado de Palworld y seleccione `Level.sav`.

2. **Explora tus datos**
   - Usa las pestañas: **Mapa**, **Herramientas**, **Jugadores**, **Gremios**, **Bases**, **Inventario de jugadores**, **Inventario de base**, **Pal Editor**, **Exclusiones**, para explorar tu partida guardada.
   - La barra de estadísticas muestra recuentos en vivo; Los iconos de navegación rápida saltan a cada sección.

3. **Hacer cambios**
   - Haga clic izquierdo para seleccionar; Haga clic derecho en casi cualquier cosa para realizar acciones contextuales.
   - Haga doble clic para editar o eliminar rápidamente (consulte las guías en la aplicación para obtener más detalles).

4. **Guarde sus cambios**
   - Haga clic en **Menú → Guardar cambios**. Las copias de seguridad se crean automáticamente.

> **Consejo:** Cada pestaña tiene una guía incorporada: haga clic en el ícono de ayuda en cualquier pestaña para ver exactamente qué puede hacer. Para obtener un conocimiento más profundo, **pase el cursor sobre cualquier botón, campo o control** para revelar información sobre herramientas detallada en el encabezado. El sistema de ayuda de información sobre herramientas en la aplicación es su mejor referencia para comprender exactamente qué hace cada función y cómo usarla.





---




<div align="center">

## Guías

<img src="https://readme-typing-svg.demolab.com?lines=Tutoriales+paso+a+paso;Sigue+la+gu%C3%ADa;Te+mostraremos+c%C3%B3mo&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Guardar ubicaciones de archivos

**Anfitrión/Cooperativo (Windows):**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**Servidor Dedicado:**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### Desbloqueo del mapa

PST puede desbloquear el mapa completo (todos los puntos de viaje rápido) para guardar:

1. Cargue su archivo guardado en PST.
2. Abre la pestaña **Inventario de jugadores** y haz clic en **Desbloquear todos los mapas + Viaje rápido** para un solo jugador, **o**
3. Utilice la herramienta **Restaurar mapa** en la pestaña Herramientas para aplicar el progreso del mapa desbloqueado en **todos** sus mundos/servidores a la vez.
4. Guarde los cambios. Se crean copias de seguridad automáticas.

### Cooperativo → Servidor dedicado

<details>
<summary>Haga clic para ampliar</summary>

Mueve tu mundo cooperativo (donde alojas desde tu PC) a un servidor dedicado para que otros puedan jugar incluso cuando no estés conectado.

**Cómo funciona:** Los guardados cooperativos usan `0001.sav` para el jugador anfitrión. Los servidores dedicados no: cada jugador tiene un UID normal. Fix Host Save **intercambia** dos archivos de reproductor (como asientos intercambiables), no una copia. Tu personaje cooperativo en `0001.sav` se intercambia en la ranura del servidor.

1. **Copia tu guardado cooperativo en el servidor.**
   - Ubicación de guardado cooperativo: `%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\`
   - Copie `Level.sav` y la carpeta `Players` desde allí.
   - Pegar en la carpeta de guardado del servidor: `steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\`

2. **Únete al servidor y crea un personaje temporal.**
   - Inicie el servidor, únase a él y cree un nuevo personaje (cualquier nombre/apariencia; esto es solo un marcador de posición).
   - Espere a que se guarde automáticamente y luego apague el servidor.

3. **Cambia tu personaje cooperativo en la ranura del servidor.**
   - Abra PST → **Herramientas** → **Reparar guardado de host**.
   - Busque el `Level.sav` del servidor.
   - **Reproductor fuente**: selecciona tu personaje cooperativo (el de `0001.sav`, que figura como anfitrión).
   - **Jugador objetivo**: selecciona el personaje temporal que acabas de crear.
- Haga clic en el botón para ejecutar el intercambio.

4. **Inicie el servidor.**
   - Tu personaje cooperativo original (con todo el progreso, Pals, bases) ahora está vinculado al servidor. El marcador de posición temporal desapareció.

</details>

### Servidor dedicado → Cooperativo

<details>
<summary>Haga clic para ampliar</summary>

Lleva tu personaje del servidor dedicado a un guardado cooperativo local, algo útil si dejas de alquilar un servidor o quieres jugar sin conexión.

**Cómo funciona:** El mismo intercambio de GUID a la inversa: Fix Host Save **intercambia** dos archivos, no una copia. El personaje de tu servidor (UID normal) se intercambia en `0001.sav` (la ranura del host) para que puedas hospedar en modo cooperativo con el progreso de tu servidor.

1. **Copie el servidor guardado en su PC local.**
   - Ubicación para guardar el servidor: `steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\`
   - Copie `Level.sav` y la carpeta `Players` desde allí.
   - Pega en tu carpeta cooperativa local: `%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\`

2. **Organiza un juego cooperativo y crea un personaje temporal.**
   - Inicia Palworld, organiza una sesión cooperativa y crea un nuevo personaje.
   - Deja que se guarde automáticamente y luego cierra Palworld.

3. **Cambia tu personaje de servidor por la ranura de anfitrión.**
   - Abra PST → **Herramientas** → **Reparar guardado de host**.
   - Navega hasta la cooperativa local `Level.sav`.
   - **Reproductor de origen**: selecciona el personaje de tu servidor dedicado (enumerado por su UID).
   - **Jugador objetivo**: selecciona el personaje cooperativo temporal (el de `0001.sav`, que figura como anfitrión).
   - Haga clic en el botón para ejecutar el intercambio.

4. **Organiza la cooperativa normalmente.**
   - Tu personaje servidor ahora es el anfitrión (`0001.sav`). Todo el progreso, Pals y bases intactas.

</details>

### Cambio de anfitrión (intercambio cooperativo)

<details>
<summary>Haga clic para ampliar</summary>

Dos jugadores quieren cambiar quién es el anfitrión. El jugador A ha sido anfitrión; su personaje vive en `0001.sav`. El jugador B se une como cliente: su personaje vive en `1234.sav`. Ahora quieren que el jugador B se convierta en el anfitrión, pero el puesto de anfitrión siempre es `0001.sav`.

**Concepto clave: Fix Host Save siempre INTERCAMBIA dos jugadores.** Intercambia sus archivos guardados, como dos personas intercambiando asientos. NO copia uno sobre el otro. Después de cualquier intercambio, ambos reproductores siguen existiendo, sólo que están en archivos diferentes.

Dado que un intercambio mueve al jugador B a la ranura del anfitrión pero deja los datos del jugador A en el archivo antiguo de B, se necesita un segundo intercambio para devolver el personaje original del jugador A. He aquí cómo:

---

**Estado inicial:**
```
0001.sav  = Player A (current host)
1234.sav  = Player B (current client)
```

---

**Paso 1: Intercambia A y B.**
- Abra PST → **Herramientas** → **Reparar guardado de host**.
- Busque su cooperativa `Level.sav`.
- **Fuente**: Jugador A (`0001.sav`). **Objetivo**: Jugador B (`1234.sav`).
- Haga clic en el botón. Fix Host Save intercambia los dos archivos.

**Después del paso 1:**
```
0001.sav  = Player B  ← now the host with B's character
1234.sav  = Player A  ← A's data is here, but this UID no longer exists in the game
```

---

**Paso 2: el jugador B es el anfitrión, el jugador A se une.**
- El jugador B es el anfitrión del mundo. El jugador A se une.
- Dado que A ya no es el host, Palworld asigna un UID nuevo para el carácter temporal de A (por ejemplo, `9999.sav`).
- El jugador A alcanza el **Nivel 2** con el personaje temporal y luego todos salen del juego.

**Después del paso 2:**
```
0001.sav  = Player B (host, correct)
1234.sav  = Player A's original data (not linked to any active UID)
9999.sav  = Player A's temporary character (fresh, Level 2+)
```

---

**Paso 3: intercambia los datos originales de A por el nuevo UID de A.**
- Abra **Fix Host Save** nuevamente con el mismo `Level.sav`.
- **Fuente**: `1234.sav` (datos originales del jugador A). **Objetivo**: `9999.sav` (personaje temporal del jugador A).
- Haga clic en el botón. Se intercambian de nuevo.

**Después del paso 3:**
```
0001.sav  = Player B (host, correct)
1234.sav  = Player A's temp character (unused, can delete)
9999.sav  = Player A's original character  ← restored!
```

---

**Listo.** El jugador B presenta con el personaje original del jugador B. El jugador A se une al personaje original del jugador A. El `1234.sav` sobrante se puede ignorar o eliminar.

> **¿Por qué dos intercambios?** Reparar host Guardar **intercambia** dos archivos: no es una copia. El primer intercambio coloca a B en la ranura del host, pero los datos de A terminan en el antiguo UID de B (que ya no existe en el juego). El segundo intercambio mueve los datos de A al nuevo UID del cliente de A. Dos cambios, todo el progreso preservado.

</details>

### Transferencia de personajes (guardado cruzado)

<details>
<summary>Haga clic para ampliar</summary>

Copia a un jugador (con todo Pals, inventario, tecnología y progreso) de un mundo a otro, lo que resulta útil para mover tu personaje entre un mundo cooperativo y un servidor dedicado, o entre dos servidores.

**Cómo funciona:** A diferencia de Fix Host Save (que **intercambia** dos archivos), Character Transfer **copia** un reproductor de un `Level.sav` a otro. La fuente guardada está intacta.

1. Abra PST → **Herramientas** → **Transferencia de personajes**.
2. **Cargue el código fuente guardado**: haga clic en el botón Fuente y seleccione el `Level.sav` que tiene el carácter que desea copiar (por ejemplo, su servidor anterior).
3. **Cargue el destino guardado**: haga clic en el botón Destino y seleccione el `Level.sav` al que desea copiar (por ejemplo, su nuevo servidor).
4. **Seleccione el reproductor** para transferir desde la lista de reproductores de origen a la izquierda.
5. **Elige dónde colocarlos** en la lista de jugadores objetivo a la derecha. Puedes sobrescribir un jugador existente o dejarlo vacío para un nuevo espacio.
6. Haga clic en **Transferir**. El personaje, Pals, el inventario y la membresía del gremio se copian en el guardado de destino.
7. Guarde los cambios. Se crean copias de seguridad automáticas.

También puedes transferir **todos los jugadores** a la vez usando el botón "Transferir todos".

</details>

### Base Exportar / Importar / Clonar

<details>
<summary>Haga clic para ampliar</summary>

**Exportando una Base:**
1. Vaya a la pestaña **Bases** (o utilice el Visor de mapas).
2. Haga clic derecho en una base → **Exportar base**.
3. Guárdelo como un archivo de plano `.json`.

**Importando una base:**
1. Haga clic derecho en el gremio objetivo (en la pestaña Bases, Visor de mapas o pestaña Gremios).
2. Seleccione **Importar base** (archivo único) o **Importar bases (varios archivos)**.
3. Seleccione sus archivos `.json` exportados.

**Clonación de una base:**
1. Haga clic derecho en una base → **Clonar base**.
2. Selecciona el gremio objetivo.
3. La base se clona con posicionamiento desplazado.

**Ajuste del radio de la base:**
1. Haga clic derecho en una base → **Ajustar radio**.
2. Ingrese un nuevo radio (50%–1000%).
3. Guarde y vuelva a cargar el archivo guardado en el juego para las estructuras que desea reasignar.

</details>





---




<div align="center">

## Solución de problemas

<img src="https://readme-typing-svg.demolab.com?lines=Cuando+las+cosas+van+de+lado;No+entres+en+p%C3%A1nico;Lo+hemos+visto+todo&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### "No se encontró VCRUNTIME140.dll" (Windows)

Instale el [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015–2022).

### `struct.error` al analizar un guardado

El formato del archivo guardado está desactualizado. Cargue el guardado en el juego (Solo, Cooperativo o Servidor Dedicado) una vez para activar una actualización automática de la estructura, luego inténtelo nuevamente. Asegúrate de que el guardado se haya actualizado a partir del último parche del juego.

### El convertidor GamePass no funciona

1. Cierre completamente la versión GamePass de Palworld.
2. Espere unos minutos hasta que se liberen los identificadores de archivos.
3. Ejecute el convertidor GamePass → Steam.
4. Inicie Palworld en GamePass para verificar.

### El binario de Linux/macOS no se inicia

- **Linux:** `chmod +x PalworldSaveTools-*-linux.AppImage` para marcarlo como ejecutable.
- **macOS:** Si Gatekeeper lo bloquea, haga clic derecho → **Abrir** o ejecute `xattr -d com.apple.quarantine /path/to/app`.





---




<div align="center">

## Construyendo desde la fuente

<img src="https://readme-typing-svg.demolab.com?lines=comp%C3%ADlalo+t%C3%BA+mismo;Construye+el+tuyo+propio;Del+c%C3%B3digo+fuente+al+binario&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

PST admite dos rutas de compilación. La canalización de CI/CD utiliza Nuitka para archivos binarios de lanzamiento multiplataforma; cx_Freeze se utiliza para el instalador local de Windows.

### Nuitka (multiplataforma: utilizado por CI/versiones)

Requiere Python 3.11+ y `uv`. Nuitka se instala automáticamente.

```bash
# One-file build (Windows / Linux)
uv run python build/nuitka/build_nuitka.py --onefile

# One-directory build (macOS .app)
uv run python build/nuitka/build_nuitka.py --onedir
```

Las salidas van a `dist/`:
- Ventanas → `dist/PalworldSaveTools-*.exe`
-Linux → `dist/PalworldSaveTools-*-linux`
- macOS → `dist/PalworldSaveTools.app` → empaquetado como `.dmg`

### cx_Freeze (instalador de Windows)

Para un paquete local de Windows `.zip`:

```
scripts\build_cx.cmd
```

Esto crea `PST_standalone_v{version}.zip` en la raíz del proyecto.

### Constructor interactivo

Un menú interactivo para elegir un modo de construcción:

```bash
uv run python build/build_interactively.py
```





---




<div align="center">

## Contribuyendo

<img src="https://readme-typing-svg.demolab.com?lines=%C2%BFQuieres+ayudar%3F+As%C3%AD+es+como;%C3%9Anete+al+equipo;Cada+contribuci%C3%B3n+cuenta&center=true&width=440&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

¡Las contribuciones son bienvenidas! No dude en enviar una solicitud de extracción.

1. Bifurque el repositorio.
2. Cree su rama de funciones (`git checkout -b feature/AmazingFeature`).
3. Confirme sus cambios (`git commit -m 'Add some AmazingFeature'`).
4. Empuje hacia la rama (`git push origin feature/AmazingFeature`).
5. Abra una solicitud de extracción.





---




<div align="center">

## Descargo de responsabilidad

<img src="https://readme-typing-svg.demolab.com?lines=Lee+esto+antes+de+romper+algo.;has+sido+advertido;%C2%A1Copia+de+seguridad+primero%21;Con+gran+poder...&center=true&width=520&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

**Utilice esta herramienta bajo su propia responsabilidad. Siempre haga una copia de seguridad de sus archivos guardados antes de realizar modificaciones.**

Los desarrolladores no son responsables de ninguna pérdida de datos guardados o problemas que puedan surgir al utilizar esta herramienta.





---




<div align="center">

## Soporte

<img src="https://readme-typing-svg.demolab.com?lines=Te+respaldamos;%C2%BFNecesitas+ayuda%3F;Estamos+aqu%C3%AD+para+ti&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

- **Discord:** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub Problemas:** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Modificaciones Nexus:** [Download & discuss](https://www.nexusmods.com/palworld/mods/3190)





---




<div align="center">

## Licencia

<img src="https://readme-typing-svg.demolab.com?lines=MIT%3A+haz+lo+que+quieras;Gratis+como+en+la+cerveza;C%C3%B3digo+abierto%2C+mente+abierta&center=true&width=430&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Este proyecto tiene la licencia MIT; consulte el archivo [license](license) para obtener más detalles.





---




<div align="center">

## El equipo de Palworld

<img src="https://readme-typing-svg.demolab.com?lines=La+gente+detr%C3%A1s+de+la+magia;Conoce+al+equipo;Construido+con+pasi%C3%B3n&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Este proyecto no existiría sin las personas que lo respaldan.

### Mantenedores activos

**[Pylar](https://github.com/deafdudecomputers)** — El hombre que empezó todo. Cada línea de esta herramienta se remonta a su visión y trabajo incansable en el motor de guardado, la GUI y las funciones que utiliza todos los días.

**[cyrix](https://github.com/CyrixJD115)** — Refactorizador y submantenedor. Centrado en la calidad del código, la simplificación y las mejoras estructurales, manteniendo la base del código limpia, más pequeña y más fácil de mantener a medida que crece el proyecto.

### Colaboradores

**[dkoz](https://github.com/dkoz)** — El hombre detrás de las identificaciones. Proporciona ID de datos del juego, información estructural sobre los códigos de ID y un conocimiento profundo de cómo se conectan los datos de Palworld que mantiene la herramienta precisa con cada actualización del juego.

**[oMaN-Rod](https://github.com/oMaN-Rod)**: proporcionó el analizador de guardado original del que se bifurcó este proyecto. Sin su trabajo fundamental para descifrar el formato de guardado de Palworld, nada de esto existiría. La bifurcación simplificó y simplificó su analizador hasta convertirlo en lo que es PST hoy.
**[Okaetsu](https://github.com/Okaetsu)** — Información sobre modificaciones que hizo posible la importación/exportación básica. Su comprensión de cómo Palworld estructura los datos básicos desde el lado de la modificación cerró la brecha entre la modificación y la edición guardada, haciendo de esta característica una realidad.





---




<div align="center">

## Agradecimientos

<img src="https://readme-typing-svg.demolab.com?lines=D%C3%B3nde+se+debe+el+cr%C3%A9dito;gracias+a+todos;Nos+paramos+sobre+los+hombros&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Un enorme agradecimiento a:

- **Palworld** desarrollado por Pocketpair, Inc. — para el juego que nos unió a todos.
- **Los reporteros de errores**: cada problema presentado, cada caso extremo encontrado, cada registro pegado en Discord. Usted hace que esta herramienta sea más sólida con cada informe.
- **La comunidad de modding de Palworld**: compañeros modders, desarrolladores de herramientas y expertos que comparten conocimientos, realizan ingeniería inversa en formatos e impulsan el ecosistema hacia adelante. Este proyecto se sustenta sobre los hombros de ese esfuerzo colectivo.
- **Todos los contribuyentes y miembros de la comunidad**: ya sea que enviaron un PR, respondieron una pregunta en Discord o simplemente le contaron a un amigo sobre PST, gracias.

---

<div align="center">

![Divider](../assets/branding/PalworldSaveTools_readme_divider.png)

**Hecho con ❤️ para la comunidad Palworld**

[⬆ Back to Top](#palworld-save-tools)

</div>