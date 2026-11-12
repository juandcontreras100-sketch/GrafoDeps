Guía de exposición — GrafoDeps
Proyecto de Aula · Matemáticas Discretas · Ingeniería de Software · UDES
Duración sugerida: 12–15 minutos, más preguntas

# 1. Propósito de la exposición

Presentar qué problema aborda GrafoDeps, cómo se representa con un grafo dirigido, qué resultados produce y cuáles son sus límites. La explicación debe conectar la teoría de grafos con una demostración breve del programa, sin afirmar que el prototipo detecta todas las dependencias de Python ni que todo ciclo cause un error durante la ejecución.

## Idea central en una frase

GrafoDeps es un prototipo de análisis estático que representa las importaciones internas reconocidas de un proyecto Python como un grafo dirigido y permite consultar ciclos y otras propiedades desde la CLI o un explorador web local.

## ¿Qué problema abordamos?

En un proyecto modular, los archivos Python importan elementos de otros módulos. Cuando estas relaciones se distribuyen en muchos archivos, puede ser difícil ver qué depende de qué. Si las dependencias forman ciclos, tampoco existe un orden topológico que respete todos los arcos. Los ciclos pueden complicar el mantenimiento y, según el momento y la forma en que se usan los módulos, llegar a causar errores de importación; no todo ciclo produce necesariamente un error inmediato.

GrafoDeps ayuda a hacer visibles esas relaciones. No repara el código automáticamente, no ejecuta el proyecto analizado ni sustituye una revisión de arquitectura.

## Mensaje que debe recordar la audiencia

> Convertimos importaciones estáticas entre módulos en aristas de un digrafo; luego usamos algoritmos de grafos para identificar ciclos, medir valencias, buscar caminos y enfocar el análisis en las dependencias alcanzables de un módulo.

# 2. Recorrido de la exposición

La distribución suma aproximadamente 14 minutos. Si el tiempo asignado es menor, acortar la explicación matemática y conservar la demostración y las limitaciones.

| Diapositiva | Tiempo | Contenido y apoyo visual |
|---|---:|---|
| 1. Título y motivación | 0:45 | Nombre del proyecto y una pregunta inicial: «¿Cómo vemos qué módulos dependen entre sí?» |
| 2. Problema | 1:30 | Dibujo de tres módulos con dependencias cruzadas; explicar que los ciclos dificultan entender y cambiar el sistema. |
| 3. Objetivo y alcance | 1:15 | Qué inspecciona el prototipo y qué no pretende resolver. |
| 4. Modelo matemático | 2:00 | Digrafo G = (V, E), dirección de los arcos, valencias y ciclo de tienda. |
| 5. Arquitectura y funciones | 1:15 | Tres capas: `scanner`, `model` y vistas CLI/web (`cli`, `render`, `webapp`). |
| 6. Demostración | 3:30 | Abrir la interfaz, explorar el grafo `tienda`, resaltar un ciclo, consultar un módulo y exportar PNG; complementar con CLI si hay tiempo. |
| 7. Resultados y verificación | 1:15 | Suite de 25 pruebas y benchmark sintético de 51 vértices y 144 aristas. |
| 8. Límites y trabajo futuro | 1:15 | Importaciones dinámicas, alcance estático, compatibilidad aún no validada en Linux/Python 3.10. |
| 9. Conclusión | 0:45 | Retomar el problema, la solución y el principal aprendizaje matemático. |

# 3. Guion sugerido por diapositiva

## Diapositiva 1 — Título y motivación (0:45)

**En pantalla:** GrafoDeps: analizador de dependencias entre módulos Python con grafos dirigidos.

**Decir:**

«Buenos días. Presento GrafoDeps, un prototipo académico que conecta teoría de grafos con una situación común en proyectos Python: las importaciones entre módulos. La pregunta que guía el proyecto es: ¿cómo podemos reconocer visualmente esas dependencias y detectar si forman ciclos?»

## Diapositiva 2 — Problema (1:30)

**En pantalla:** Una figura sencilla con módulos como `carrito`, `precios` e `impuestos`; flechas en la dirección de la importación.

**Decir:**

«En un programa modular, un archivo puede importar a otro y este depender de un tercero. Cuando hay muchas relaciones, seguirlas manualmente se vuelve difícil. Un ciclo aparece cuando, siguiendo las flechas, se puede regresar al módulo de partida. Eso impide obtener un orden topológico que respete todos los arcos y puede complicar el mantenimiento. Dependiendo de cómo se inicialicen y usen los módulos, también puede producir errores de importación; no afirmamos que todo ciclo falle al ejecutarse.»

**Transición:** «Para estudiar estas relaciones las representamos con un grafo dirigido.»

## Diapositiva 3 — Objetivo y alcance (1:15)

**En pantalla:** Objetivo general y dos columnas: «Incluye» / «No incluye».

**Decir:**

«El objetivo es desarrollar y evaluar una herramienta en Python que modele las importaciones internas de un proyecto como un digrafo y produzca diagnósticos verificables. El prototipo reconoce importaciones estáticas que puede resolver a partir del código fuente, busca ciclos y caminos, calcula valencias, permite filtrar dependencias transitivas y genera una imagen. No ejecuta el proyecto analizado, no repara ciclos y no detecta de forma completa importaciones construidas dinámicamente, por ejemplo mediante reflexión.»

## Diapositiva 4 — Modelo matemático (2:00)

**En pantalla:** La definición G = (V, E), un ejemplo de flechas y la identidad de valencias.

**Decir:**

«El conjunto V contiene los módulos y el conjunto E sus importaciones internas reconocidas. Definimos cada arco como importador hacia importado: si `carrito` importa `precios`, agregamos la arista `carrito → precios`. La valencia de salida cuenta cuántos módulos importa un módulo; la valencia de entrada cuenta cuántos módulos lo importan. La suma de todas las valencias de entrada y la suma de todas las valencias de salida son iguales al número de aristas.»

«En este ejemplo, `precios` importa `impuestos` y `impuestos` importa `precios`; forman un circuito dirigido. Un orden topológico formal coloca el origen antes que el destino de cada arco. Como aquí las flechas van del importador al importado, el orden de construcción con dependencias primero es el inverso del orden topológico.»

**Apoyo opcional:** Mostrar la ruta `main → carrito → precios → impuestos`. Su longitud es 3 aristas.

## Diapositiva 5 — Arquitectura (1:15)

**En pantalla:** Diagrama de arquitectura de tres capas.

**Decir:**

«El `scanner` descubre archivos Python y extrae importaciones del árbol de sintaxis sin ejecutar esos archivos. El `model` construye el digrafo y calcula ciclos, grados, órdenes, caminos y subgrafos. La CLI y la interfaz web local presentan los resultados; `render` exporta imágenes desde la CLI y el navegador genera su propio PNG. Las capas comparten el mismo análisis y no dependen de servicios remotos.»

## Diapositiva 6 — Demostración (3:30)

**Preparación:** Abrir una terminal en la raíz del repositorio y comprobar que el entorno virtual y las dependencias estén listos. No instalar paquetes durante la exposición.

**Demostración visual — explorador web local:**

```powershell
python -m grafodeps.webapp
```

Abrir `http://127.0.0.1:8765` en el navegador. El ejemplo `examples` se carga al iniciar. Señalar los 8 módulos, 8 dependencias y el ciclo; seleccionar `tienda.carrito` para consultar sus valencias y dependencias alcanzables; seleccionar el ciclo para resaltarlo y pulsar **Exportar PNG**. Para analizar otro proyecto, escribir una ruta local en el campo y pulsar **Analizar proyecto**. Al terminar, detener el servidor con Ctrl+C en la terminal.

El servidor escucha en loopback y el análisis se ejecuta en el equipo local; no subir ni copiar proyectos privados para la demostración.

**Si se desea complementar con la CLI**, ejecutar:

**Comando 1 — análisis general:**

```powershell
python -m grafodeps.cli examples --path tienda.main tienda.impuestos
```

**Señalar en la salida:**

- `Módulos |V| = 8` y `Dependencias |E| = 8`.
- Un ciclo: `tienda.impuestos → tienda.precios → tienda.impuestos`.
- «Orden de construcción: no existe» porque el digrafo tiene un ciclo.
- El camino más corto desde `tienda.main` hasta `tienda.impuestos`: `main → carrito → precios → impuestos`, de longitud 3.
- Las valencias de entrada y salida se pueden sumar para comprobar que cada suma es 8, igual a `|E|`.

**Comando 2 — análisis enfocado:**

```powershell
python -m grafodeps.cli examples --from tienda.carrito --path tienda.carrito tienda.impuestos
```

**Señalar en la salida:**

- El subgrafo contiene 5 módulos y 5 dependencias.
- Incluye `tienda.carrito` y los módulos alcanzables mediante sus dependencias.
- Conserva el ciclo entre `impuestos` y `precios`.
- El camino consultado es `carrito → precios → impuestos`.

**Si se quiere mostrar el PNG**, agregar `--out grafo_tienda.png` al primer comando y abrir el archivo creado. La imagen se guarda en la carpeta actual.

**Cierre de la demo:** «La herramienta no deduce si el diseño es bueno o malo: hace explícitas las relaciones que pudo reconocer para que una persona las analice.»

## Diapositiva 7 — Resultados y pruebas (1:15)

**En pantalla:** Tres datos, indicando el alcance de cada medición.

- Suite: 25 pruebas aprobadas en la ejecución registrada; además, las interacciones principales y la exportación PNG se verificaron manualmente en navegador.
- Benchmark sintético: 50 módulos de código más un `__init__.py`; 51 vértices y 144 aristas.
- Cinco mediciones: promedio 0.0174 s y máximo 0.0387 s para escaneo y algoritmos del grafo; el renderizado de imágenes no se incluyó en ese tiempo.

**Decir:**

«Las pruebas comprueban comportamientos concretos del prototipo y no equivalen a cobertura completa del código. El benchmark corresponde a un proyecto sintético, no a una medición de proyectos industriales. En las cinco corridas registradas, todas quedaron por debajo del requisito de cinco segundos.»

## Diapositiva 8 — Límites y trabajo futuro (1:15)

**En pantalla:** «Qué sí podemos concluir» / «Qué queda pendiente».

**Decir:**

«El resultado depende de las importaciones estáticas que el escáner reconoce; una importación construida durante la ejecución puede quedar fuera. Tampoco medimos impacto en productividad ni evaluamos sistemas industriales. Las pruebas se ejecutaron en Windows con Python 3.12.14; la compatibilidad con Linux y con Python 3.10 sigue pendiente de verificación. Como trabajo futuro se podrían ampliar los casos de importación, evaluar otros proyectos y mejorar la visualización de grafos grandes.»

## Diapositiva 9 — Conclusión (0:45)

**Decir:**

«GrafoDeps toma una relación del código fuente —quién importa a quién— y la convierte en un modelo matemático que podemos recorrer y analizar. La principal contribución del proyecto es aplicar digrafos, ciclos, valencias, caminos y orden topológico a un problema concreto de modularidad. La herramienta apoya el análisis; la decisión de cómo corregir una dependencia sigue en manos del desarrollador. Muchas gracias. ¿Qué preguntas tienen?»

# 4. Preguntas probables

| Pregunta | Respuesta breve |
|---|---|
| ¿Un ciclo siempre hace que el programa falle? | No. Puede causar errores según el orden de inicialización y el uso de nombres, pero un ciclo no implica por sí mismo un fallo inmediato. |
| ¿Qué significa una arista `A → B`? | Que el escáner reconoció una importación interna desde el módulo A hacia el módulo B. |
| ¿Por qué no hay orden topológico en `tienda`? | Porque un digrafo admite orden topológico si y solo si es acíclico; el ejemplo contiene el ciclo `impuestos ↔ precios`. |
| ¿Qué diferencia hay entre orden topológico y orden de construcción? | El primero respeta que el origen de cada arco aparezca antes que el destino. Con arcos importador → importado, construir dependencias primero requiere invertir ese orden. |
| ¿Qué significa `--from`? | Analiza el subgrafo inducido por el módulo raíz y los módulos alcanzables siguiendo sus dependencias. |
| ¿El escáner ejecuta los archivos? | No. Lee y analiza la sintaxis mediante el AST; no ejecuta el código del proyecto analizado. |
| ¿Detecta `importlib` o imports calculados? | No de forma completa. El alcance es el de las importaciones estáticas reconocidas por el escáner. |
| ¿El benchmark prueba rendimiento industrial? | No. Es una medición reproducible sobre un grafo sintético pequeño, útil para verificar el requisito definido para el prototipo. |
| ¿El programa corrige automáticamente los ciclos? | No. Los informa y visualiza; el desarrollador decide si debe refactorizar y cómo hacerlo. |
| ¿Qué pasa con módulos de bibliotecas externas? | El modelo se enfoca en módulos internos del proyecto detectados por el escáner; no construye un grafo completo de dependencias instaladas externas. |

# 5. Lista de comprobación antes de exponer

- [ ] Abrir la presentación y confirmar que las figuras y textos se leen desde el fondo del salón.
- [ ] Abrir una terminal en la raíz del repositorio y activar el entorno virtual.
- [ ] Ejecutar con anticipación el comando general y el comando con `--from`.
- [ ] Tener el proyecto `examples` disponible y preparar una captura de la salida como respaldo.
- [ ] Confirmar que el tiempo de ensayo está entre 12 y 15 minutos; no leer literalmente todas las respuestas.
- [ ] Explicar las flechas siempre con la convención importador → importado.
- [ ] No llamar «cobertura» al número de pruebas ni presentar el benchmark sintético como un estudio industrial.
- [ ] Cerrar con una conclusión y reservar tiempo para preguntas.

# 6. Datos de respaldo

Los valores de ejemplo y rendimiento de esta guía corresponden a la evidencia registrada en `docs/informe/evidencias.txt`: el proyecto `tienda` produce 8 módulos y 8 aristas; al filtrar desde `tienda.carrito`, el subgrafo contiene 5 módulos y 5 aristas; el benchmark registrado reporta 51 vértices y 144 aristas, promedio 0.0174 s y máximo 0.0387 s. Si se vuelven a ejecutar pruebas o benchmark antes de exponer, sustituir estos valores por los resultados nuevos tanto en las diapositivas como en el guion.
