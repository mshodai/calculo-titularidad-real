# 0001. Comparar dos regímenes bajo lecturas declaradas en lugar de dar una respuesta

- Estado: aceptada
- Fecha: 15/09/2026

## Contexto

El titular real de una sociedad es la persona física que, en último término, la posee o la controla, directamente o a través de otras sociedades. Identificarlo es una obligación legal para los sujetos obligados por la normativa de prevención del blanqueo de capitales. La Ley 10/2010 lo dice así: «Los sujetos obligados identificarán al titular real y adoptarán medidas adecuadas a fin de comprobar su identidad con carácter previo al establecimiento de relaciones de negocio o a la ejecución de cualesquiera operaciones» (art. 4.1). Si no lo consiguen, la consecuencia también es legal: «no establecerán o mantendrán relaciones de negocio con personas jurídicas […] cuya estructura de propiedad y de control no haya podido determinarse» (art. 4.4, párr. 2).

Hay dos regímenes con reglas distintas, y durante la transición las mismas estructuras de propiedad hay que leerlas con los dos:

- **El español, vigente.** Es titular real quien posea o controle «un porcentaje superior al 25 por ciento del capital o de los derechos de voto» (Ley 10/2010, art. 4.2.b). Para el control, la Ley remite al art. 42 del Código de Comercio, que solo mira los votos. Si nadie supera el umbral, «se considerará que ejerce dicho control el administrador o administradores» (art. 4.2.b bis).
- **El AMLR, el Reglamento (UE) 2024/1624.** «Será aplicable a partir del 10 de julio de 2027» (art. 90). Obliga a «identificar a los titulares reales y tomar medidas razonables para comprobar su identidad de forma que la entidad obligada tenga la seguridad de que sabe quién es el titular real y de que comprende la estructura de propiedad y control del cliente» (art. 20.1.b). El umbral es el «25 % o más» (art. 52.1). El control por participación es «el 50 % más una de las acciones o los derechos de voto» (art. 53.2.c), es decir, en capital o en votos. El art. 54 tiene reglas propias para las cadenas que mezclan control y participación, sin equivalente en la Ley española. Si nadie es titular real, se identifica a los cargos de dirección de alto nivel, que «no son los titulares reales» (considerando 125).

Las diferencias no se quedan en el 25 frente al 25 justo. La misma estructura puede dar titulares distintos en cada régimen. Quien tiene el 30 % de una sociedad que controla la entidad es titular en el AMLR (art. 54.b) y en España no llega a serlo por ninguna vía que la Ley prevea.

Calcular el titular real parece aritmética: multiplicar porcentajes a lo largo de las cadenas de propiedad y compararlos con un umbral. No lo es del todo. El propio AMLR lo reconoce: «Las normas están sujetas a interpretaciones divergentes, lo que da lugar a métodos distintos para identificar a los titulares reales […]. Esto se debe, entre otras cosas, a la incoherencia entre los métodos aplicados para calcular la propiedad indirecta» (considerando 104). Al analizar los textos para este proyecto aparecieron catorce casos que la norma no resuelve ([ambiguedades.md](../ambiguedades.md)). Unos ejemplos:
- la Ley española no dice cómo se calcula el porcentaje indirecto (N1);
- ninguna norma dice qué hacer con los ciclos de participación, cuando una sociedad es, a través de otras, accionista de sí misma (N7);
- el AMLR dice que la multiplicación se aplica «salvo que resulte de aplicación el artículo 54», sin aclarar si el 54 la sustituye o se le añade (N3).

La herramienta recibe la estructura de propiedad como un grafo: personas y sociedades como nodos, y participaciones con su porcentaje de capital y de votos como aristas ([modelo-datos.md](../modelo-datos.md)). Muchos hechos que deciden quién es titular real no están en ese grafo.

## Decisión

Esta herramienta calcula bajo lecturas declaradas y compara los dos regímenes. No da una respuesta sobre quién es el titular real.

Para una estructura, calcula en cada régimen qué personas cumplen las pruebas de titularidad, con qué valores y en qué estado queda el resultado, y muestra en qué difieren los dos. Donde la norma deja margen, la [especificación del cálculo](../especificacion-calculo.md) elige una lectura, la nombra y explica por qué. Si la otra lectura se puede calcular con los datos de la entrada, la calcula también y dice si cambiaría el resultado.

Hay tres razones.

**Catorce casos que la norma no resuelve.** Cualquier respuesta única resuelve cada uno de ellos en un sentido. Algunos cambian quién es titular real en estructuras corrientes. En el ejemplo del modelo de datos, que una de las personas sea titular en el AMLR depende de cómo se lea el «salvo que» del art. 52.1. A esos catorce casos se suman cuatro que no vienen de la norma, sino del formato del dato (F1 a F4). El más visible: con porcentajes a 4 decimales, un 50 % registrado no distingue la mitad justa de la mitad más una acción en una sociedad de más de un millón de acciones.

**Más de treinta decisiones propias.** La especificación del cálculo declara 35 (C1 a C35) y el modelo de datos otras 27 (D1 a D27). Cada una tiene su alternativa descartada y su motivo, y ninguna es la ley. Una salida del tipo «X es titular real» las incorpora todas sin nombrar ninguna.

**Una salida que afirma más de lo que sabe sería indefendible ante quien la discuta.** Un supervisor, un auditor o la otra parte de una operación pueden leer la norma de otra forma en cualquiera de esos puntos. Si la salida declara la lectura aplicada, la discusión es sobre la lectura, que es donde tiene que estar. Si no la declara, la discusión es sobre por qué la herramienta afirmó algo que la norma no dice, y esa discusión la herramienta la pierde.

Comparar, además de calcular, es lo que tiene sentido durante la transición. A quien prepara el cambio de régimen le sirve saber qué estructuras cambian de resultado y por qué regla. Por eso la comparación es el resultado principal. Calcular un solo régimen sigue siendo posible (`--regimen`), sin la comparación.

## Consecuencias

**Cada resultado va con la lectura de la que depende.**
- Los titulares aparecen como «titulares reales según las lecturas aplicadas».
- Cada aviso lleva el caso no resuelto al que corresponde (N…), o de dónde viene si no es un caso de la norma.
- El informe termina con las lecturas de las que depende el resultado y con los casos no resueltos que afectan a esa entrada.
- La correspondencia entre avisos y casos está en [ambiguedades.md](../ambiguedades.md), y los tests comprueban que la salida la sigue.

**Dos estados además del resultado: estabilidad y completitud.**
- **Inestable (C32):** otra lectura que la herramienta comprueba lo cambiaría. Por ejemplo, un valor justo en el umbral o una cadena que depende de cómo se lea el art. 54.
- **Incompleto (C33):** lo podrían cambiar datos que faltan, porque parte del capital no está identificado o lo no identificado, solo o sumado a lo que tiene una persona conocida, controlaría una sociedad intermedia.

Un resultado puede ser las dos cosas. La línea de órdenes devuelve 0 solo si los dos regímenes quedan determinados, estables, completos y con los mismos titulares. En el [corpus](https://github.com/mshodai/calculo-titularidad-real/blob/main/corpus/README.md) pasa en uno de doce casos, y es lo esperado: 0 no significa que la herramienta esté segura, sino que nada de lo que comprueba cambiaría el resultado.

**Un resultado «determinado» no es una determinación jurídica.** Significa que, con los datos de la entrada y las lecturas declaradas, las pruebas dan esos titulares. Los supuestos supletorios van más lejos en esa dirección:
- el español es siempre «condicional», porque la Ley exige que nadie ejerza el control «por otros medios» y la presunción admite «prueba en contrario» (RD 304/2014, art. 8.b);
- el del AMLR es siempre «provisional», porque no se han «agotado todos los medios posibles de identificación» (art. 22.2).

**El alcance termina en la frontera entre aritmética y juicio.** Lo que hace la herramienta es aritmética sobre un grafo: productos, sumas, series, umbrales y puntos fijos. Todo es exacto y reproducible, y se puede comprobar a mano. Pero hay juicios sobre hechos que el grafo no contiene, y quedan fuera:

- **Hechos que la entrada afirma y la herramienta no comprueba.** Que una participación se tiene por cuenta de otro (modelo, D11). Que una cotizada está sujeta a requisitos de información adecuados (modelo, D13).
- **Hechos que la entrada no puede representar.** El control por otros medios: pactos de socios, estatutos, derecho a nombrar administradores, actuación concertada o relaciones familiares. También los derechos económicos distintos del capital, las opciones, los fideicomisos y las reglas propias de fundaciones y asociaciones (modelo, §7 y D19). Una entidad objetivo que no es una sociedad queda «fuera de alcance» (C31).
- **Juicios que la norma deja a quien aplica la ley.** Si hay «prueba en contrario» de la presunción del administrador, y si se han agotado los medios de identificación.

Donde uno de estos hechos puede cambiar el resultado, la salida lo dice: con un estado condicional o provisional, con un aviso, o declarando el caso fuera de alcance. No lo resuelve.

**Costes.**
- El informe es más largo y exige más lectura que una respuesta con un nombre. Quien busque solo el nombre tiene que leer también de qué lectura depende.
- Cada nueva decisión hay que declararla en la especificación y, si es un caso de la norma, señalarla en la salida. Los tests obligan a mantener las dos cosas alineadas.
- El AMLR se calcula aunque la fecha de referencia sea anterior al 10 de julio de 2027, con un aviso de que todavía no es aplicable (C7): la comparación lo necesita.

## Referencias

- Ley 10/2010, de 28 de abril, de prevención del blanqueo de capitales y de la financiación del terrorismo, arts. 4.1, 4.2.b, 4.2.b bis y 4.4 (texto consolidado, última modificación de 21 de marzo de 2026): <https://www.boe.es/buscar/act.php?id=BOE-A-2010-6737>
- Real Decreto 304/2014, de 5 de mayo, Reglamento de la Ley 10/2010, arts. 8 y 9: <https://www.boe.es/buscar/act.php?id=BOE-A-2014-4742>
- Código de Comercio, art. 42: <https://www.boe.es/buscar/act.php?id=BOE-A-1885-6627>
- Directiva 2013/34/UE, art. 22: <https://eur-lex.europa.eu/legal-content/ES/TXT/PDF/?uri=CELEX:02013L0034-20240528>
- Reglamento (UE) 2024/1624 (AMLR), considerandos 104 y 125, arts. 20.1.b, 22.2, 51 a 54 y 90: <http://data.europa.eu/eli/reg/2024/1624/oj>
- Versiones y huellas de los documentos usados: [fuentes/FUENTES.md](../fuentes/FUENTES.md)
