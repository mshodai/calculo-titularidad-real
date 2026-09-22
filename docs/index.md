---
title: "¿Cuándo importa el capital sin identificar de una sociedad intermedia para saber quién es el titular real?"
description: "Un hueco pequeño en participación efectiva puede ser un hueco de control, solo o sumado a lo que ya tiene un socio conocido. Qué comprobar y qué significa que el resultado esté completo, con el Reglamento (UE) 2024/1624 y la Ley 10/2010."
---

# Lo que llega y lo que manda: cuándo importa un hueco en la cadena de participaciones

Identificar al titular real de una sociedad con varias capas de participaciones casi nunca se hace con la estructura completa. Es habitual que en alguna sociedad intermedia parte del accionariado no esté identificada: capital flotante, socios que no han contestado o una sociedad extranjera de la que solo se conoce una parte. La pregunta práctica es:

**Cuando parte del accionariado de una sociedad intermedia no está identificada, ¿cuándo importa ese hueco?**

Este artículo cuenta cómo respondía a esa pregunta la herramienta de [calculo-titularidad-real](https://github.com/mshodai/calculo-titularidad-real), por qué la respuesta era insuficiente y por qué la primera corrección también lo era. La herramienta calcula la titularidad real en dos regímenes: la Ley 10/2010, hoy vigente en España, y el Reglamento (UE) 2024/1624 (AMLR), que «será aplicable a partir del 10 de julio de 2027» (art. 90).

## La respuesta intuitiva: medir lo que llega

La participación indirecta se calcula multiplicando los porcentajes a lo largo de la cadena y sumando las cadenas. El AMLR lo dice así (art. 52.1): «multiplicando las acciones o los derechos de voto u otra participación en la propiedad de la que sean titulares las entidades intermedias de la cadena […] y sumando los resultados de esas distintas cadenas». La Ley 10/2010 no da método para el porcentaje indirecto (art. 4.2.b), y la herramienta aplica la misma multiplicación.

Con esa regla, un hueco se trata como un socio más: la parte sin identificar de cada sociedad se propaga hacia abajo por la cadena. La intuición es que el hueco importa si lo que llega a la sociedad objetivo alcanza el umbral:
- **AMLR:** «25 % o más» (art. 52.1);
- **España:** «superior al 25 por ciento» (Ley 10/2010, art. 4.2.b).

La herramienta tenía dos comprobaciones de ese tipo:
- **H1:** lo que llega sin identificar alcanza por sí solo el umbral, así que puede haber detrás un titular real desconocido.
- **POS-HUECO:** una persona conocida que ya participa en la sociedad objetivo alcanzaría el umbral si el hueco fuera suyo.

Las dos miden lo mismo: participación efectiva, es decir, el porcentaje que llega a la sociedad objetivo.

## El caso que no cubría

La estructura es el [caso 08 del corpus](https://github.com/mshodai/calculo-titularidad-real/blob/main/corpus/08-hueco-que-controla.json) ([resultado esperado](https://github.com/mshodai/calculo-titularidad-real/blob/main/corpus/08-hueco-que-controla.esperado.json)). Capital y votos coinciden en todas las participaciones.

```
S (sociedad objetivo)
├── 70 %  R
└── 30 %  X
          ├── 10 %  Q1
          ├── 10 %  Q2
          ├── 10 %  Q3
          ├── 10 %  Q4
          └── 60 %  sin identificar
```

Las comprobaciones de participación dan esto:
- **H1.** Lo que llega a S sin identificar es 60 % × 30 % = 18 %. No alcanza el 25 % del AMLR ni supera el 25 % de la Ley. No salta.
- **POS-HUECO.** Cada Q tiene 10 % × 30 % = 3 % de S. Con el hueco llegaría al 3 + 18 = 21 %. No salta.

La herramienta daba «determinado» en los dos regímenes, con R como único titular real. No emitía ningún aviso del cálculo y el código de salida era 0: el mismo que da cuando los dos regímenes coinciden y nada de lo que comprueba cambiaría el resultado. Lo único que había era el aviso AVI-02 de la validación de la entrada: «la suma de "capital" es 40; quedan 60 sin identificar». El aviso decía que faltaba el 60 % de X. No decía si eso importaba, y el cálculo respondía que no.

Sí importa. Si ese 60 % es de una sola persona, directamente o a través de sociedades que controla, esa persona controla X, y X tiene el 30 % de S:

- **AMLR.** Controla X, porque el control a través de participación es «la propiedad directa o indirecta del 50 % más una de las acciones o los derechos de voto» (art. 53.2.c). Y el art. 54.a hace titulares reales a las personas que «controlen, directa o indirectamente, […] entidades jurídicas titulares de una participación en la propiedad directa de la sociedad». Es la prueba A3 de la herramienta: la participación directa de X en S cuenta entera, el 30 %, sin multiplicar. El considerando 108 pide comprobar «si alguna persona física controla al accionista directo con el 25 % o más».
- **España.** Para la Ley es titular real quien «controle», además de quien «posea», un porcentaje superior al 25 % (art. 4.2.b). Para el control remite al art. 42 del Código de Comercio. Con el 60 % de los votos de X, esa persona domina X, porque «posea la mayoría de los derechos de voto» (CCom, art. 42.1.a). A sus votos «se añadirán los que posea a través de otras sociedades dependientes» (art. 42.1, último párrafo), así que controla el 30 % de los votos de S. Es la prueba E2 de la herramienta.

Un matiz en España: la Ley no dice si el art. 42 sirve para medir el porcentaje que alguien «controla» o solo para decidir si hay control. Es el caso N2 de [los que la norma no resuelve](ambiguedades.md). La herramienta aplica esa lectura (E2), y con la multiplicación sola esa persona se quedaría en el 18 %. En el AMLR no hay ese margen: el art. 54.a lo dice expresamente.

## Medir lo que llega no es medir lo que manda

H1 y POS-HUECO preguntan cuánto de la sociedad objetivo puede estar detrás del hueco. Pero las normas no definen al titular real solo por lo que posee. El AMLR incluye a quien controla «la sociedad u otra entidad jurídica» (art. 51.b), y la Ley 10/2010, a quien controla un porcentaje (art. 4.2.b). El control no se multiplica: el 60 % de X no se convierte en un 18 % de control sobre S. Da el control de X, y con él el 30 % entero.

Por eso **un hueco pequeño en participación efectiva puede ser un hueco de control.** En el caso 08, un 18 % que parece inofensivo es el 60 % de la sociedad que tiene el 30 %.

## La primera corrección: el hueco solo

La primera corrección fue la comprobación **H3**, en el [commit 92207d1](https://github.com/mshodai/calculo-titularidad-real/commit/92207d1ca8defb1e73ed0ce31e2e37f6d95a808a). Trata el hueco como una persona y le aplica las pruebas de control, no solo la de participación:
- **AMLR:** A2 (controla S, art. 53.2), A3 (controla accionistas directos de S, art. 54.a) y A4 (tiene el 25 % de una sociedad que controla S, art. 54.b);
- **España:** E2 (votos agregados por la vía del art. 42 del Código de Comercio).

Con H3, el caso 08 dejaba de salir completo. Pero la corrección arreglaba ese caso, no el principio. Había dos comprobaciones de hueco que medían participación, y H3 solo sustituyó una: la del hueco solo. POS-HUECO, la del hueco sumado a lo que ya tiene una persona conocida, siguió midiendo solo lo que llega.

El propio test de H3 lo dejaba escrito. Comprobaba que en el caso 08 no saltaba POS-HUECO, con el comentario «nadie llega con el hueco (3 + 18, sin POS-HUECO)». Es el razonamiento del fallo original: 3 + 18 es una suma de participaciones efectivas. Con el control, Q1 más el hueco tiene el 70 % de X, y cualquiera de los cuatro socios sería titular real si el 60 % fuera suyo. Ese fallo no se veía en el caso 08 porque H3 ya marcaba el resultado como incompleto. Hacía falta un caso en el que el hueco solo no controlara nada.

## El caso que tampoco cubría la primera corrección

Es el [caso 12 del corpus](https://github.com/mshodai/calculo-titularidad-real/blob/main/corpus/12-socio-que-controlaria-con-el-hueco.json) ([resultado esperado](https://github.com/mshodai/calculo-titularidad-real/blob/main/corpus/12-socio-que-controlaria-con-el-hueco.esperado.json)):

```
S (sociedad objetivo)
├── 70 %  R
└── 30 %  X
          ├── 30 %  Q1
          ├── 15 %  Q2
          ├── 15 %  Q3
          ├── 10 %  Q4
          └── 30 %  sin identificar
```

- **H1.** Llega a S un 30 % × 30 % = 9 % sin identificar. No salta.
- **H3.** El 30 % sin identificar no controla X. No salta.
- **POS-HUECO, midiendo participación.** Q1 tiene el 9 % de S; con el hueco, el 18 %. No salta.

Con H3 ya añadido, la herramienta daba en los dos regímenes un resultado determinado, estable y completo, con código de salida 0. Pero si el 30 % que falta es de Q1, Q1 tiene el 60 % de X. Controla X y es titular real por las mismas normas que en el caso 08: art. 54.a en el AMLR, y en España art. 4.2.b de la Ley con el art. 42.1.a del Código de Comercio. Los demás socios no llegan: con el hueco, Q2 y Q3 se quedarían en el 45 % y Q4 en el 40 %.

## La segunda corrección: todas las pruebas, todas las combinaciones

Las dos comprobaciones de hueco hacen dos preguntas distintas: si alguien desconocido puede estar detrás del hueco, y si una persona conocida sería titular con el hueco. Cada pregunta tiene que hacerse con cada tipo de prueba de titularidad. Antes de las correcciones solo estaba cubierta la columna de participación; H3 añadió una casilla de la de control.

| | Prueba de participación (A1, E1) | Pruebas de control (A2 a A4, E2) |
|---|---|---|
| **Hueco solo** | H1 | H3 (primera corrección) |
| **Hueco más una persona conocida** | POS-HUECO | POS-HUECO (segunda corrección) |

La segunda corrección son dos cambios:
- **POS-HUECO aplica todas las pruebas** ([commit ad0d9ce](https://github.com/mshodai/calculo-titularidad-real/commit/ad0d9ce644b04b5ae5472490027d21a8fcd892e6), decisión C34 de la [especificación](especificacion-calculo.md)). Atribuye a la persona todo lo que no está identificado y recalcula A1 a A4, o E1 y E2. Es el mismo aviso y no uno nuevo, porque la pregunta es la misma: si esa persona sería titular real con lo que falta. Sigue contando para la completitud, porque lo que falta son datos, no otra lectura de la norma.
- **H3 evalúa todos los huecos juntos** ([commit e74efe4](https://github.com/mshodai/calculo-titularidad-real/commit/e74efe4126b915665674aa4463634e75067a3f36), decisión C35). Varios huecos pueden ser de la misma persona y controlar juntos una sociedad que ninguno controla solo. Por ejemplo, un 30 % sin identificar de Y más el 60 % sin identificar de Z, que tiene el 40 % de Y, son el 54 % de Y. H1 ya sumaba todos los huecos; H3 los miraba de uno en uno.

Con los dos cambios, el caso 12 sale así:

```
ESTADO
  España  determinado
  AMLR    determinado
  ? España: el resultado puede no estar completo. Lo que no está identificado podría cambiar quién
  es titular real: H2, POS-HUECO (C33).
  ? AMLR: el resultado puede no estar completo. Lo que no está identificado podría cambiar quién es
  titular real: H2, POS-HUECO (C33).

COMPARACIÓN (según las lecturas aplicadas)
  Persona  España               AMLR
  Q1       posible (POS-HUECO)  posible (POS-HUECO)
  R        titular (E1, E2)     titular (A1, A2)
```

En el caso 08, Q1 a Q4 pasan a salir también como posibles titulares, además del aviso H3.

Tanto H3 como POS-HUECO impiden aplicar el supuesto supletorio: los administradores en España (Ley 10/2010, art. 4.2.b bis) y los cargos de dirección de alto nivel en el AMLR (art. 22.2). Si nadie es titular real y lo no identificado podría dar el control de una intermedia, el estado es «no determinable». No se puede afirmar que «no exista» una persona por encima del umbral, ni que se hayan «agotado todos los medios posibles de identificación».

## Qué significa que un resultado esté «completo»

Ninguno de los dos fallos era un error de aritmética: todas las cifras eran correctas. El error estaba en qué se daba por comprobado. Un «determinado» sin avisos parecía decir que la estructura bastaba para responder, y solo se había comprobado para algunas de las pruebas de titularidad.

Por eso la herramienta separa dos propiedades del resultado, que la especificación define en su §9:

- **Estable (C32):** ninguna otra lectura de la norma que la herramienta pueda calcular cambiaría quién es titular real. Por ejemplo, un valor justo en el umbral o una cadena que depende de cómo se lea el art. 54 del AMLR. Los casos en los que la norma admite más de una lectura están en [ambiguedades.md](ambiguedades.md).
- **Completo (C33):** ningún dato que falta podría cambiarlo. No lo es si lleva H1, H2, H3 o POS-HUECO.

Son preguntas distintas, y un resultado puede fallar en una, en la otra o en las dos. En el corpus, el caso 10 es inestable y completo: dos socios al 50 % justo, sin ningún dato que falte. El caso 11 es incompleto y estable: falta el 40 % de la sociedad objetivo, y ninguna otra lectura cambia nada. Mezclarlas en un solo indicador de «incertidumbre» ocultaría lo que hay que hacer en cada caso. Un resultado inestable pide decidir una lectura de la norma, o documentarla. Uno incompleto pide ir a buscar los datos.

La diferencia tiene consecuencias legales. La Ley 10/2010 prohíbe mantener relaciones de negocio con personas jurídicas «cuya estructura de propiedad y de control no haya podido determinarse» (art. 4.4, párr. 2). El AMLR exige tomar medidas para que la entidad obligada tenga «la seguridad de que sabe quién es el titular real y de que comprende la estructura de propiedad y control del cliente» (art. 20.1.b). Las dos normas hablan de propiedad y de control. Una comprobación de completitud que solo mira la propiedad responde a la mitad de la pregunta.

La lección general es esta. **Por cada prueba de titularidad tiene que haber una comprobación de hueco que mida lo mismo que esa prueba, y con cada forma en que el hueco puede combinarse con lo conocido.** Si una regla atribuye porcentajes multiplicados, el hueco se mide multiplicado. Si una regla atribuye porcentajes enteros por control, hay que preguntar si el hueco podría dar ese control: solo, junto con otros huecos o sumado a lo que ya tiene alguien. Corregir el caso que ha fallado no basta: hay que revisar las demás casillas de la tabla.

## Lo que «completo» sigue sin garantizar

«Completo» significa que ninguna de las comprobaciones de hueco salta. Estas son las cosas que esas comprobaciones no miran.

**Un hueco combinado con otra lectura de la norma.** La estabilidad mira otras lecturas con los datos que hay. La completitud mira los datos que faltan con la lectura aplicada. Ninguna de las dos mira las dos cosas a la vez. Un ejemplo: C tiene el 60 % de S y la controla, Q tiene el 70 % de C y falta el 30 % restante.
- **Con la lectura aplicada en España,** quien tenga ese 30 % no llega: multiplicando, un 18 % de S (E1), y sin el dominio de C no agrega votos (E2).
- **Con la lectura extensiva L3** (casos N1 y N2), que trata como transparente a la sociedad que controla S, tendría 30 % × 100 % = 30 %. La herramienta ya comprueba L3 para las personas conocidas (aviso POS-T), pero no para lo que falta.
- **El resultado español sale determinado, estable y completo.** En el AMLR, la misma estructura sí da H3, por el art. 54.b.

**Quien no participa en la sociedad objetivo.** POS-HUECO solo considera a las personas que participan en S en alguna magnitud, capital o votos. Quien no participa no se señala por su nombre: que cualquiera pueda estar detrás del hueco ya lo dicen H1 y H3. Pero hay personas con participación en la estructura que no llegan a S en ninguna magnitud, porque capital y votos se propagan por separado. Un ejemplo:
- X tiene el 30 % del capital de S y ningún voto. En X, Q tiene todo el capital y el 40 % de los votos, P tiene el 30 % de los votos y ningún capital, y falta el 30 % de los votos.
- **P no participa en S:** sus votos en X no llegan a S, porque X no tiene votos en S, y no tiene capital en X. POS-HUECO no lo mira.
- **El hueco solo no controla X** (30 % de los votos), así que no hay H3. Tampoco llega nada sin identificar a S, así que no hay H1.
- **Pero si ese 30 % fuera de P,** tendría el 60 % de los votos de X. Controlaría X (AMLR, art. 53.2.c), y X tiene el 30 % del capital de S: sería titular real por el art. 54.a, que no pide que el control y la participación estén en la misma magnitud.
- **El resultado sale determinado, estable y completo en los dos regímenes, con código de salida 0.** En España no hay fallo: el art. 42.1.a del Código de Comercio solo mira los votos, y X no tiene votos en S.

Es el mismo error que cuenta este artículo, a una escala menor. La restricción de POS-HUECO («participa en S») se pensó para la prueba de participación. Allí es razonable: quien no llega a S no añade nada a lo que llega sin identificar, y que cualquiera pueda estar detrás de eso ya lo dice H1. Pero se aplicó igual a las pruebas de control, y para ellas no vale. Lo que alguien tiene en una sociedad intermedia se suma al hueco de esa sociedad aunque no llegue a S. Para el control, lo que cuenta es participar en alguna sociedad de la cadena.

**Lo que la entrada no puede representar.** El control por otros medios: pactos, estatutos o el derecho a nombrar administradores (AMLR, arts. 53.3 y 53.4.a; Ley 10/2010, art. 4.2.b; CCom, art. 42.1.b a d). Tampoco la actuación concertada entre personas conocidas (AMLR, art. 53.3.a; CCom, art. 42.1, último párrafo) ni las relaciones familiares (AMLR, art. 53.4.b). Dos socios conocidos que actúan juntos pueden controlar una intermedia sin que la entrada lo diga, y sin que haya ningún hueco.

**Lo que la entrada afirma y no es cierto.** Las comprobaciones de hueco solo ven lo que falta en la entrada. Si un socio figura con su participación y en realidad es un nominatario de otra persona sin que la entrada lo indique, la estructura suma el 100 % y no hay hueco que comprobar. El AMLR trata esos acuerdos como control por otros medios (art. 53.4.c) y obliga a los nominatarios a revelar a su nominador (art. 66).

Los dos últimos son límites de lo que la herramienta puede saber, y la especificación los declara. Los dos primeros son límites de lo que comprueba, del mismo tipo que los fallos que cuenta este artículo.

---

El código, la especificación y el corpus están en [github.com/mshodai/calculo-titularidad-real](https://github.com/mshodai/calculo-titularidad-real).

Otro artículo del proyecto: [La norma cambia debajo](cuando-la-norma-cambia-debajo.md), sobre qué le pasa a una implementación de referencia cuando cambia la norma que cita.

Este artículo es un análisis de la arquitectura de una herramienta de cálculo, no asesoramiento jurídico.
