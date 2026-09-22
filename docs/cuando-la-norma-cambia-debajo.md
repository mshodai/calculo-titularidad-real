---
title: "¿Qué le pasa a una implementación de referencia cuando cambia la norma que cita?"
description: "Un texto consolidado no es estable: cuando la norma se modifica, aparece una versión nueva y la citada deja de ser la vigente. El caso de la Directiva 2013/34/UE en este repositorio, por qué vigilar la huella de una URL de EUR-Lex no detecta nada y qué hace falta para que un repositorio así no envejezca en silencio."
---

# La norma cambia debajo: qué le pasa a una implementación de referencia cuando se modifica el texto que cita

Una implementación de referencia se apoya en textos legales concretos. [calculo-titularidad-real](https://github.com/mshodai/calculo-titularidad-real) cita la Ley 10/2010, el Código de Comercio, la Directiva 2013/34/UE y el Reglamento (UE) 2024/1624, cada uno con su versión, su fecha y la huella SHA-256 del PDF usado. Están en [FUENTES.md](https://github.com/mshodai/calculo-titularidad-real/blob/main/docs/fuentes/FUENTES.md).

Pero un texto consolidado no es estable. Cuando se modifica una norma, aparece una versión consolidada nueva, y la anterior deja de ser la vigente. El repositorio sigue funcionando: los tests pasan y las citas siguen siendo literales. Pero apuntan a un texto que ya no se aplica. La pregunta práctica es:

**Cuando cambia la norma que cita una implementación de referencia, ¿cómo se entera el repositorio, y qué puede afirmar después?**

## El caso: la Directiva 2013/34/UE

El proyecto usa el artículo 22 de la Directiva 2013/34/UE, apartados 1 a 5, porque la Ley 10/2010 remite a ellos (art. 4.2.b): «Serán indicadores de control por otros medios, entre otros, los previstos en el artículo 22 (1) a (5) de la Directiva 2013/34/UE». De esos apartados salen, por ejemplo, la base de votos del cálculo en España (22.5) y la atribución de las participaciones que se tienen por cuenta de otro (22.3 y 22.4.a), según la [especificación del cálculo](https://github.com/mshodai/calculo-titularidad-real/blob/main/docs/especificacion-calculo.md).

Las fechas:

- **28 de mayo de 2024.** Fecha de la versión consolidada que citaba el proyecto: «02013L0034 — ES — 28.05.2024 — 006.003». Su última modificación era la Directiva (UE) 2024/1306.
- **26 de febrero de 2026.** Se publica la [Directiva (UE) 2026/470](https://data.europa.eu/eli/dir/2026/470/oj) (DO L 470 de 26.2.2026), que modifica la Directiva 2013/34/UE.
- **18 de marzo de 2026.** Entra en vigor la Directiva 2026/470. EUR-Lex publica una versión consolidada nueva, [02013L0034-20260318](https://eur-lex.europa.eu/legal-content/ES/TXT/PDF/?uri=CELEX:02013L0034-20260318) («18.03.2026 — 007.001»). La de 28 de mayo de 2024 deja de ser la vigente.
- **15 de septiembre de 2026.** El repositorio se publica. Cita la versión de 28 de mayo de 2024 desde su [primer inventario de fuentes](https://github.com/mshodai/calculo-titularidad-real/commit/0b1f867abce63a55c1550b99f49c5e44fdc33dfe). Esa versión llevaba 181 días sin ser la vigente.
- **22 de septiembre de 2026.** Un script de vigilancia lo detecta. El [commit ddf266f](https://github.com/mshodai/calculo-titularidad-real/commit/ddf266faf14a5fc247fa39ecf2aaac872ac90039) actualiza la referencia a la versión de 18 de marzo de 2026.

La Directiva 2026/470 cambia la información sobre sostenibilidad, no los estados financieros consolidados. La versión consolidada de 18 de marzo de 2026 lo muestra así:

- **Ámbito.** La obligación de informar sobre sostenibilidad pasa a aplicarse solo a empresas, o a grupos de forma consolidada, con un volumen de negocios neto superior a 450 000 000 EUR y más de 1 000 empleados de media (arts. 1, 19 bis y 29 bis).
- **Cadena de valor.** Limita la información que puede pedirse a las empresas de la cadena de valor que no superan esos tamaños, la «empresa protegida» (arts. 19 bis, 29 bis y 34.2 bis).
- **Terceros países.** Sube los umbrales de las filiales y sucursales de empresas de terceros países (art. 40 bis).
- **Otros ajustes.** Extiende la revisión por inflación a los nuevos umbrales (art. 3.13) y ajusta la responsabilidad de los órganos de administración (art. 33), la verificación (art. 34) y los actos delegados (arts. 48 bis y 49).

**Los apartados 22.1 a 22.5 no cambiaron.** El artículo 22 es idéntico en las dos versiones, párrafo a párrafo, incluida la marca de la rectificación C5. Tampoco cambió el artículo 24, cuyo apartado 3.a cita el [modelo de datos](https://github.com/mshodai/calculo-titularidad-real/blob/main/docs/modelo-datos.md). La comparación está anotada en [FUENTES.md](https://github.com/mshodai/calculo-titularidad-real/blob/main/docs/fuentes/FUENTES.md#nota-sobre-la-versión-de-la-directiva-201334ue).

Esta vez la modificación no afectaba al fondo. Pero eso se supo después de comprobarlo, no antes. Mientras nadie lo había comprobado, lo único que se podía afirmar era que el proyecto citaba una versión que ya no era la vigente.

## Cómo se detectó, y cómo no

El script de vigilancia es una herramienta local que no está publicada. Lee el bloque «Datos para la vigilancia automática» de cada FUENTES.md, que el repositorio añadió en el [commit 2bae415](https://github.com/mshodai/calculo-titularidad-real/commit/2bae4153a3dcdf51ee1050c78685f64cb2293924) y que repite, para cada documento, el fichero, la URL y la huella.

En su primera versión, el script descargaba cada URL y comparaba su SHA-256 con el declarado. **Su primera ejecución, el 22 de septiembre de 2026, no detectó el cambio.** EUR-Lex respondió `202` con el cuerpo vacío, como hace a veces con las descargas automáticas (lo anota el [commit 2d8b886](https://github.com/mshodai/calculo-titularidad-real/commit/2d8b886d56b2eabae74314022fb7fb645f83258e)). El documento quedó como «no comprobable».

Con una descarga correcta tampoco lo habría detectado. Ese mismo día, la URL de la versión de 28 de mayo de 2024 devolvió un fichero con la misma huella que la copia local ([commit 36e01f5](https://github.com/mshodai/calculo-titularidad-real/commit/36e01f5ce874a7f857a9ba0f991c85a5618746ba)). Seis meses después de que el acto se modificara, la huella decía «sin cambios».

El cambio se detectó la primera vez que el script se ejecutó con otro criterio: comparar la fecha de la versión consolidada vigente con la de la versión citada.

## Por qué no basta con guardar la URL y la huella

La huella detecta si ha cambiado el contenido que sirve una URL. No sirve para saber si ha cambiado la norma. Cuál de las dos cosas mide depende de cómo publique la fuente.

**En EUR-Lex, cada versión es un documento con identificador propio y fecha.** Una modificación no reescribe la versión anterior: añade otra. La [ficha de la Directiva 2013/34/UE](https://eur-lex.europa.eu/legal-content/ES/ALL/?uri=CELEX:32013L0034) tiene nueve versiones consolidadas, de 02013L0034-20130719 a 02013L0034-20270130. Cada una conserva su identificador. La de 28 de mayo de 2024 seguía sirviendo el mismo fichero seis meses después de dejar de ser la vigente, así que su huella daba «sin cambios». Lo que cambia es cuál es la vigente. Para saberlo, hay que mirar la ficha del acto, no el documento citado.

**En el BOE es al revés.** La URL del texto consolidado no lleva fecha: [BOE-A-2010-6737-consolidado.pdf](https://www.boe.es/buscar/pdf/2010/BOE-A-2010-6737-consolidado.pdf). El PDF que sirve declara «Última modificación: 21 de marzo de 2026», que es la más reciente de las redacciones que lista la [ficha de la Ley 10/2010](https://www.boe.es/buscar/act.php?id=BOE-A-2010-6737). Una URL sin fecha que sirve la redacción más reciente no puede servir a la vez las anteriores. Cuando la ley vuelva a modificarse, esa URL servirá otro texto, y la huella cambiará.

Son dos criterios para dos formas de publicar:

| Fuente | Qué no cambia | Qué hay que vigilar |
|---|---|---|
| EUR-Lex: texto publicado o versión consolidada con fecha | El documento de cada URL | Cuál es la versión consolidada vigente del acto |
| BOE: texto consolidado | La URL | La huella del documento que sirve |

Lo que decide el criterio es la forma de publicar, no el sitio. El BOE también aloja copias del Diario Oficial de la Unión Europea, como la del Reglamento general de protección de datos que cita [plazos-conservacion-pbc](https://github.com/mshodai/plazos-conservacion-pbc/blob/main/docs/fuentes/FUENTES.md). Esas copias no cambian nunca, igual que las URL de EUR-Lex, y se vigilan por la versión consolidada del acto que publican.

El script ya no lee la ficha HTML. Las páginas de EUR-Lex, también la ficha, responden `202` a los clientes automáticos. Lee los mismos metadatos, incluida la lista de versiones consolidadas de cada acto, en el [punto de consulta del Cellar](https://publications.europa.eu/webapi/rdf/sparql) de la Oficina de Publicaciones.

## Qué hace falta para que un repositorio así no envejezca en silencio

**Fuentes declaradas con versión, fecha y huella.** Sin una versión declarada no hay con qué comparar. [FUENTES.md](https://github.com/mshodai/calculo-titularidad-real/blob/main/docs/fuentes/FUENTES.md) copia literalmente la versión que declara cada documento, su URL y su SHA-256, y repite esos datos en un bloque que puede leer un programa.

**Una comprobación automática.** La vigilancia se ejecuta cada semana. Nadie revisa a mano, cada lunes, si ha aparecido una versión consolidada nueva de cada norma citada.

**Un criterio por tipo de fuente.** El BOE se compara por huella y EUR-Lex por versión vigente, como se ha visto en el apartado anterior. Con un solo criterio para todo, una de las dos fuentes nunca da aviso.

**Un aviso que distinga lo que exige actuar de lo que no se ha podido comprobar.** Un aviso que salta siempre deja de leerse. La vigilancia termina con tres códigos:

- **0:** nada ha cambiado y se ha podido comprobar todo.
- **1:** algo exige actuar. Ha aparecido una versión vigente más reciente que la citada, o una huella distinta, o el bloque no coincide con el texto.
- **3:** no hay cambios, pero algo no se ha podido comprobar, como la respuesta `202` de EUR-Lex.

Con un solo código para las dos cosas, un servidor que falla a menudo haría saltar la alarma cada semana. Al cabo de un tiempo, nadie la leería, tampoco la semana en que la norma cambia.

Por la misma razón, un repositorio que cita a propósito dos versiones de un acto no debe dar un aviso permanente. [registro-examen-especial-pbc](https://github.com/mshodai/registro-examen-especial-pbc/blob/main/docs/fuentes/FUENTES.md) cita el texto original del Reglamento de Inteligencia Artificial, que es el auténtico, y también su versión consolidada vigente. El original es anterior a la vigente, pero el repositorio ya tiene la vigente. Por eso cada acto se compara con la versión más reciente que cita cada repositorio. Las versiones consolidadas con fecha futura se muestran como información, y pasan a ser un aviso el día en que entran en vigor.

## El límite: el script señala dónde mirar

El script no dice que el artículo citado no haya cambiado. Dice que existe una versión vigente más reciente que la citada, cuál es y dónde descargarla. Para saber si el artículo 22 había cambiado, alguien tuvo que leer las dos versiones y compararlas. El resultado de esa lectura está en FUENTES.md, no en el informe del script.

Lo mismo vale en la otra dirección. Una vigilancia sin avisos no garantiza que las citas del repositorio sigan siendo correctas. Solo dice que, con los criterios que aplica, ninguna fuente declarada tiene una versión vigente distinta de la citada. No mira si la norma se interpreta de otro modo, ni si una norma no citada ha pasado a aplicarse, ni lo que dice un texto cuya descarga ha fallado.

El siguiente aviso ya tiene fecha. La ficha de la Directiva 2013/34/UE lista una versión consolidada de [30 de enero de 2027](https://eur-lex.europa.eu/legal-content/ES/TXT/PDF/?uri=CELEX:02013L0034-20270130). Ese día la vigilancia volverá a terminar con código 1, y alguien tendrá que volver a leer el artículo 22.

---

El código, las fuentes y su historial están en [github.com/mshodai/calculo-titularidad-real](https://github.com/mshodai/calculo-titularidad-real).

Este artículo es un análisis de arquitectura, no asesoramiento jurídico.
