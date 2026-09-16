# Ambigüedades del cálculo de la titularidad real

Puntos en los que las normas no determinan un comportamiento único para calcular la titularidad real de una sociedad. Las normas son la Ley 10/2010 (art. 4.2.b y b bis), el RD 304/2014 (arts. 8 y 9), el Código de Comercio (art. 42), la Directiva 2013/34/UE (art. 22), a la que remite la Ley, y el Reglamento (UE) 2024/1624, el AMLR (arts. 51 a 54). Las fuentes y sus versiones están en [fuentes/FUENTES.md](fuentes/FUENTES.md).

Los casos N1 a N14 proceden de la norma. Los casos F1 a F4 no: surgen del formato del dato de entrada ([modelo-datos.md](modelo-datos.md)), y la norma no tiene nada que ver con ellos. Están al final, en una sección aparte.

**Criterio.** Ningún caso se resuelve en silencio.
- Donde la norma admite más de una lectura, esta implementación aplica la que declara la [especificación del cálculo](especificacion-calculo.md). Cada decisión se cita por su número (C…).
- La salida señala el caso cuando otra lectura se puede calcular con los datos de la entrada y cambiaría quién es titular real (C25). Lo hace con los avisos del §9 de la especificación y, en N9 y N13, además, con la marca «por cuenta de».
- N10 y N11 no tienen señal propia, porque no hay otra lectura con la que comparar.
- Los avisos de los casos no resueltos hacen que el resultado no sea estable (C32), y la línea de órdenes devuelve 1. La excepción es CICLO-CERRADO (N7): el ciclo ya está tratado como hueco (§6.4).

«Esta implementación» es `src/titularidad/`: `propagacion.py` (el grafo y los métodos de ciclos), `control.py` (control y dominio), `espana.py`, `amlr.py` y `salida.py`.

**A qué régimen afecta.** Cada caso lo dice. Siete son solo del AMLR, cinco solo de España y dos de los dos. Un caso de un solo régimen no se aplica al otro: es el patrón que la especificación pide vigilar en su §0.

## Resumen

| # | Caso | Dónde se nota | Qué hace v0.1 | Señal en la salida (C25) |
|---|---|---|---|---|
| N1 | España: método para la participación indirecta | §5.1 | C17 (multiplicación) | POS-T (§5.3) |
| N2 | España: si el art. 42 sirve para medir el porcentaje que alguien «controla» | §5.1 | C19; L3 solo como aviso | POS-T |
| N3 | AMLR: si el 54 sustituye al 52.1 o se añade a él | §4.2, §6.3, Ej. 5b | C14 (se añade) | ART54-SENS (C27) |
| N4 | AMLR: cadenas con varios tramos de control | §4.4, Ej. 5 | Reglas literales | POS-T |
| N5 | AMLR 54.a: si se suma la participación directa propia | §4.3 | C15 | POS-T |
| N6 | Mezcla de magnitudes dentro de una cadena | §7, Ej. 6 | C21 | POS-MEZCLA |
| N7 | Ciclos | §6 | C20 | CICLO-SENS y CICLO-CERRADO |
| N8 | AMLR: control conjunto a través de varias entidades controladas | §3.3 | No se considera control | POS-AGREGADO (C26) |
| N9 | AMLR: si la participación de un nominatario cuenta como propiedad del nominador (52.1 frente a 53.4.c) | §2.2 | C2 | Marca «por cuenta de» y POS-FORMAL (C29) |
| N10 | España: qué es «mayoría» en el CCom 42.1.a | §3.2 | C10 (> 50) | Ninguna propia |
| N11 | AMLR: dos personas que controlan a la vez, una por capital y otra por votos (53.2.c) | §3.3, Ej. 4 | Se acepta tal como sale del texto | Ninguna |
| N12 | AMLR: si la autocartera se descuenta al decidir el control | §6.2 | La serie completa la descuenta de hecho; ninguna norma del AMLR lo dice | CICLO-SENS: el método A no la descuenta (§6.2) |
| N13 | España: a quién se atribuye el capital de una participación por cuenta de otro | §2.2, §6.3 | C2 (al principal) | Marca «por cuenta de» y POS-FORMAL (C29) |
| N14 | España: cómo se mide la «filial participada mayoritariamente» del RD 9.4 | §2.5, Ej. 8 | C30 (más del 50 % del capital, multiplicando) | EXENCION-SENS (C30) |

Las secciones (§…) y los ejemplos (Ej. …) de la tabla remiten a la [especificación del cálculo](especificacion-calculo.md). El [corpus](https://github.com/mshodai/calculo-titularidad-real/blob/main/corpus/README.md) tiene un caso sintético para varios de ellos.

---

## N1. Cómo se calcula el porcentaje indirecto en España

**Qué dice la norma.** Ley 4.2.b: titulares reales son las personas que «posean o controlen, directa o indirectamente, un porcentaje superior al 25 por ciento del capital o de los derechos de voto». El RD 304/2014, art. 8.b, repite la fórmula.

**Por qué no determina un comportamiento único.** Ninguno de los dos textos dice cómo se mide el porcentaje indirecto. Caben al menos cuatro lecturas (especificación, §5.2):
- L0: solo las participaciones directas. La descarta el propio texto, que dice «directa o indirectamente».
- L1: multiplicar a lo largo de cada cadena y sumar las cadenas.
- L2: sumar enteros los votos de las sociedades que se dominan, como el art. 42 del Código de Comercio.
- L3: tratar como transparentes las sociedades que se controlan (peso 1) y multiplicar el resto.

Dan resultados distintos. En el Ej. 2, quien controla una sociedad con el 30 % de S tiene un 18 % por L1 y un 30 % por L2 o L3.

**Qué hace esta implementación.** Mide «posean» con L1 (C17) y lo une a L2 (C19): es titular quien pasa del 25 % por cualquiera de las dos. Con ciclos, L1 usa la serie completa (C20).

**Cómo se señala en la salida.** POS-T, junto con N2: quien sería titular con L3 y no con L1 ∪ L2. De las respuestas posibles, L0 la descarta el texto, L2 ya se aplica y L3 queda señalada.

**Régimen.** Solo España. El AMLR sí da el método (52.1: multiplicar y sumar las cadenas).

## N2. Si el art. 42 sirve para medir el porcentaje que alguien «controla»

**Qué dice la norma.** Ley 4.2.b: «A efectos de la determinación del control serán de aplicación, entre otros, los criterios establecidos en el artículo 42 del Código de Comercio».

**Por qué no determina un comportamiento único.** La remisión es «a efectos de la determinación del control». No dice si sirve también para medir el porcentaje que alguien «controla», es decir, para L2. Si no sirve, «controlen un porcentaje» no tiene método propio; si sirve, hay que decidir sobre qué base se mide.

**Qué hace esta implementación.** Mide «controlen» con L2: los votos agregados de la persona y de las sociedades que domina, sobre la base ajustada de la Dir. 22.5, con el umbral de más del 25 % (C12 y C18). La lectura aplicada es L1 ∪ L2 (C19).

**Cómo se señala en la salida.** POS-T, junto con N1 (lectura extensiva L3). Es el caso del Ej. 3: quien tiene el 30 % de una sociedad que controla S es titular en el AMLR (54.b) y en España solo posible.

**Régimen.** Solo España.

## N3. Si el art. 54 sustituye al 52.1 o se añade a él

**Qué dice la norma.** AMLR 52.1: la participación indirecta se calcula multiplicando y sumando cadenas, «salvo que resulte de aplicación el artículo 54». El art. 54 regula las cadenas en las que «coexista la participación en la propiedad y el control en relación con diferentes niveles de la cadena».

**Por qué no determina un comportamiento único.** «Salvo que» admite dos lecturas. Si el 54 **sustituye** al 52.1 en las cadenas mixtas, la multiplicación no se aplica a ellas. Si se **añade**, se aplican las dos pruebas y basta con cumplir una. La primera puede dejar fuera a quien llega al 25 % por pura multiplicación a través de una cadena que tiene un tramo de control.

**Qué hace esta implementación.** Aplica todas las pruebas y une los resultados: A1 (52.1), A2 (51.b), A3 (54.a) y A4 (54.b), según C14. Se apoya en los considerandos 106 («deben realizarse en paralelo») y 108 («evaluar simultáneamente») y en la disyunción del art. 51.

**Cómo se señala en la salida.** ART54-SENS (C27). Se recalcula la participación sin las aristas de control, y si un titular lo es solo por A1 y así no llega al 25 %, dejaría de serlo con la otra lectura. Pasa en el ejemplo del modelo (P-CARLOS: 19,15 % de capital y 21,51 % de votos sin la cadena por E-BETA) y en el Ej. 5b.

**Régimen.** Solo AMLR.

## N4. Cadenas con varios tramos de control

**Qué dice la norma.** AMLR 54: a) titulares son quienes controlan «entidades jurídicas titulares de una participación en la propiedad directa de la sociedad»; b) quienes tienen una participación en «la sociedad que controle directa o indirectamente la sociedad».

**Por qué no determina un comportamiento único.** El art. 54 contempla un solo cambio a lo largo de la cadena: control arriba y participación abajo (a), o al revés (b). No dice nada de cadenas con varias alternancias, como control, participación, control, participación. A esas cadenas no les aplica ninguna regla del 54.

**Qué hace esta implementación.** Aplica las reglas literales (A1 a A4). Aparte calcula la lectura extensiva (C13), con peso 1 en cada arista en la que el titular tiene más del 50 % del capital o de los votos. Si con ella alguien alcanza el 25 % sin ser titular, se señala. Nunca lo cuenta como titular.

**Cómo se señala en la salida.** POS-T. Si la lectura extensiva no se puede calcular (un ciclo formado solo por aristas de control), T-NO-CONVERGE. En el Ej. 5, P y B2 llegan cada uno al 25 % con esa lectura.

**Régimen.** Solo AMLR. En España, la misma lectura extensiva responde a N1 y N2.

## N5. Si en el 54.a se suma la participación directa propia

**Qué dice la norma.** AMLR 54.a: titulares son quienes controlan «entidades jurídicas titulares de una participación en la propiedad directa de la sociedad, ya sea de forma individual o acumulativa».

**Por qué no determina un comportamiento único.** Si P tiene un 10 % directo en S y controla una entidad con otro 20 %, el texto no dice si eso suma 30 %. «Acumulativa» se refiere a las entidades controladas, y no está claro que incluya lo que P tiene directamente.

**Qué hace esta implementación.** Suma solo las participaciones de las entidades controladas (C15), porque el texto dice «entidades jurídicas titulares».

**Cómo se señala en la salida.** POS-T: la lectura extensiva sí suma la participación directa.

**Régimen.** Solo AMLR.

## N6. Mezcla de capital y votos dentro de una cadena

**Qué dice la norma.** AMLR 52.1: «multiplicando las acciones o los derechos de voto». Ley 4.2.b: «del capital o de los derechos de voto».

**Por qué no determina un comportamiento único.** Ningún texto dice si una misma cadena puede tomar el capital en un tramo y los votos en otro. Si se puede, una persona con mucho capital en una sociedad que tiene muchos votos en S podría alcanzar el umbral sin alcanzarlo en ninguna magnitud por separado.

**Qué hace esta implementación.** No mezcla: el capital se multiplica por capital y los votos por votos (C9, C21). Aparte calcula el producto mixto, con el mayor de las dos magnitudes en cada arista.

**Cómo se señala en la salida.** POS-MEZCLA, si con el producto mixto alguien alcanza el umbral sin ser titular (Ej. 6: 0,6 × 0,45 = 27 % en España). Si el producto mixto no converge, MEZCLA-NO-CONVERGE: puede sumar más del 100 % en una entidad y formar un ciclo que las magnitudes por separado no tienen.

**Régimen.** Los dos. En el AMLR el aviso casi nunca aparece, porque una arista con más del 50 % en cualquier magnitud ya es control y entra por el 54.a.

## N7. Ciclos de participación

**Qué dice la norma.** Nada expreso. La Ley 10/2010, el RD 304/2014, el RD 609/2023 y el art. 42 del Código de Comercio no hablan de ciclos. El AMLR 52.1 manda sumar «los resultados de esas distintas cadenas» y tener en cuenta «todas las participaciones en todos los niveles de propiedad». La Dir. 22.5 saca de la base los votos que una empresa tiene sobre sí misma o a través de sus filiales, pero para decidir el control, no la titularidad real.

**Por qué no determina un comportamiento único.** Con un ciclo hay infinitas cadenas. Se pueden sumar todas (una serie que converge), solo las que no repiten entidad, o quitar de la base los votos propios, como la Dir. 22.5. Los tres métodos dan cifras distintas (modelo de datos, §4.2) y, a veces, titulares distintos.

**Qué hace esta implementación.** Según C20:
- para multiplicar (A1, E1 y el control del AMLR), la serie completa (método B), resolviendo un sistema lineal;
- para agregar votos en España (L2), la base de la Dir. 22.5 (método C);
- como prueba de sensibilidad, las cadenas simples (método A).

Si un grupo de entidades se tiene entre sí al 100 %, sin titulares de fuera, la serie no tiene solución: esas entidades se tratan como un hueco (§6.4).

**Cómo se señala en la salida.** CICLO-SENS, si con el método A cambia quién es titular real (corpus, caso 04: 26,09 % con el método B y 24 % con el A). CICLO-CERRADO, si hay un ciclo sin titulares externos.

**Régimen.** Los dos.

## N8. Control a través de varias entidades controladas

**Qué dice la norma.** AMLR 53.2.b: el control indirecto es «el control de entidades jurídicas intermedias […] cuando se identifica el control directo en cada nivel de la estructura». 53.2.c: el control a través de participación es «la propiedad directa o indirecta del 50 % más una de las acciones o los derechos de voto».

**Por qué no determina un comportamiento único.** Si P controla D1 y D2, que tienen el 30 % de K cada una, ninguna controla K sola, pero juntas tienen el 60 %. El AMLR no dice si P controla K. El art. 42 español sí suma: agrega los votos de las dependientes.

**Qué hace esta implementación.** No lo considera control (C11). Para avisar calcula el control agregado C⁺ (C26), que suma lo que tienen X y sus controladas, como el art. 42.

**Cómo se señala en la salida.** POS-AGREGADO, si con C⁺ alguien cumpliría A2, A3 o A4 sin ser titular.

**Régimen.** Solo AMLR.

## N9. Si lo que tiene un nominatario es propiedad del nominador

**Qué dice la norma.** AMLR 53.4.c: clasifica «el uso de acuerdos de nominatario formales o informales» como control por otros medios. El art. 66 obliga a los nominatarios a revelar la identidad de su nominador. El 52.1 no dice si lo que tiene el nominatario cuenta como propiedad del nominador.

**Por qué no determina un comportamiento único.** Se puede atribuir la participación al nominador en el cálculo del 52.1 o tratarla solo como control por otros medios, que v0.1 no evalúa (modelo, D19). En el segundo caso, la participación queda en el titular formal.

**Qué hace esta implementación.** Atribuye la participación al principal en todos los cálculos y en las dos magnitudes (C2). El titular formal no recibe nada por esa arista.

**Cómo se señala en la salida.** Con la marca «por cuenta de» en cada titular cuyo resultado depende de esa atribución. Además, POS-FORMAL si con la lectura contraria (todo al titular formal) alguien sería titular (C29). Es el caso 07 del corpus.

**Régimen.** Solo AMLR. En España el caso equivalente es N13.

## N10. Qué es «mayoría» en el art. 42 del Código de Comercio

**Qué dice la norma.** CCom 42.1.a: hay dominio cuando una sociedad «posea la mayoría de los derechos de voto».

**Por qué no determina un comportamiento único.** El Código no define «mayoría». La entrada tiene porcentajes, no número de votos, así que hay que traducir «mayoría» a un umbral en porcentaje.

**Qué hace esta implementación.** Mayoría estricta: más del 50 % (C10).

**Cómo se señala en la salida.** No tiene señal propia (C25), porque no hay otra lectura con la que comparar. La única alternativa, «≥ 50», no es una lectura de «mayoría»: con ella, dos socios al 50 % dominarían a la vez la misma sociedad. Lo que sí queda abierto es un límite del dato, no de la norma: con 4 decimales, un 50 registrado puede ser la mitad justa o la mitad más un voto redondeada. Es el caso F1, y lo señala UMBRAL-EXACTO, que en la práctica también calcula la lectura «≥ 50».

**Régimen.** Solo España. En el AMLR, el «50 % más una» del 53.2.c es claro; el límite del dato (F1) le afecta igual.

## N11. Dos personas que controlan a la vez la misma sociedad

**Qué dice la norma.** AMLR 53.2.c: control a través de participación es «la propiedad directa o indirecta del 50 % más una de las acciones o los derechos de voto». 53.2.a: control es «la posibilidad de ejercer, directa o indirectamente, una influencia significativa e imponer decisiones pertinentes en la entidad».

**Por qué no determina un comportamiento único.** Con la disyunción («acciones o los derechos de voto»), una persona con más del 50 % del capital y otra con más del 50 % de los votos controlan a la vez la misma sociedad. El texto lleva a ese resultado, pero no lo comenta. Se podría argumentar desde el 53.2.a que solo controla quien puede imponer decisiones, es decir, quien tiene los votos.

**Qué hace esta implementación.** Lo acepta tal como sale del texto: los dos controlan, y los dos son titulares si el resto de condiciones se cumple. El 53.2.c no condiciona el control por participación a lo que dice el 53.2.a.

**Cómo se señala en la salida.** No tiene señal propia (C25). Una regla que eligiera a una de las dos personas no está en ningún texto, y comparar con ella sería inventar la alternativa. Es el caso 09 del corpus: en el AMLR, P (capital) y Q (votos) son titulares; en España solo Q, porque el art. 42 solo mira los votos.

**Régimen.** Solo AMLR.

## N12. Si la autocartera se descuenta al decidir el control

**Qué dice la norma.** AMLR 53.2.c no dice nada de la autocartera. La Dir. 22.5 manda restar de la base los votos propios, pero es derecho al que remite la Ley española, no el AMLR.

**Por qué no determina un comportamiento único.** Con un 10 % de autocartera, quien tiene el 48 % tiene la mitad más uno de los votos que no son de la propia sociedad, pero no la mitad más uno del total. Controla o no según se descuente.

**Qué hace esta implementación.** El control del AMLR usa la participación de la serie completa (C11, C20), que descuenta la autocartera de hecho: 48 / 0,9 = 53,33 %, así que controla.

**Cómo se señala en la salida.** CICLO-SENS. La autocartera es una arista reflexiva, un ciclo, y con el método A no se descuenta (se queda en el 48 %). Si eso cambia quién es titular, la salida lo avisa (N7/N12).

**Régimen.** Solo AMLR. En España, la base de la Dir. 22.5 descuenta la autocartera expresamente, así que CICLO-SENS allí solo cita N7.

## N13. A quién se atribuye el capital de una participación por cuenta de otro, en España

**Qué dice la norma.** CCom 42.1, último párrafo: a la dominante se le añaden los votos que tenga «a través de personas que actúen en su propio nombre pero por cuenta de la entidad dominante». Dir. 22.4.a: se restan al titular formal los derechos de las acciones «de las que se ostente la titularidad por cuenta de una persona distinta». La Ley 4.2.b no menciona a las personas interpuestas.

**Por qué no determina un comportamiento único.** Los dos textos hablan solo de votos. Del capital no dice nada ninguno, así que no hay base para atribuirlo al principal ni al titular formal.

**Qué hace esta implementación.** Lo atribuye al principal, igual que los votos (C2).

**Cómo se señala en la salida.** Con la marca «por cuenta de» y con POS-FORMAL (C29). La lectura contraria atribuye solo el capital al titular formal; los votos siguen en el principal, porque para ellos sí hay texto. Solo cambia la prueba E1 en capital.

**Régimen.** Solo España. En el AMLR, el capital forma parte de N9, porque el 52.1 incluye las «acciones».

## N14. Cómo se mide la «filial participada mayoritariamente» del RD 9.4

**Qué dice la norma.** RD 304/2014, art. 9.4: «No será preceptiva la identificación de los accionistas o titulares reales de empresas cotizadas o de sus filiales participadas mayoritariamente cuando aquéllas estén sometidas a obligaciones de información que aseguren la adecuada transparencia de su titularidad real».

**Por qué no determina un comportamiento único.** No dice con qué magnitud se mide «participada mayoritariamente», ni si cuenta la participación indirecta. Con el capital, con los votos o con una cadena de mayorías directas (el 60 % del 60 %), la misma sociedad puede ser filial o no.

**Qué hace esta implementación.** Según C30:
- es filial si la cotizada, con requisitos de información, tiene más del 50 % de su capital, multiplicando las cadenas;
- cada cotizada cuenta por separado;
- la exención solo se aplica a la entidad objetivo, no a las filiales intermedias: dejaría sin recorrer a sus socios minoritarios, que la transparencia de la cotizada no cubre.

Es la lectura estrecha, porque el RD 9.4 dispensa, no prohíbe: quedarse corto como mucho identifica de más.

**Cómo se señala en la salida.** EXENCION-SENS, si S no es filial según C30 pero lo sería midiendo con los votos o con una cadena de mayorías directas. Los casos 05 y 06 del corpus muestran la exención y la filial intermedia.

**Régimen.** Solo España. En el AMLR, la cotización no cambia el cálculo.

---

## Casos que vienen del formato del dato, no de la norma

Estos casos no son ambigüedades de ningún texto legal. Surgen de cómo se representa la estructura en la entrada: porcentajes con 4 decimales, dos magnitudes, un valor desconocido. Por eso llevan una F y no una N, y se declaran como decisiones del [modelo de datos](modelo-datos.md) (D…), no de la especificación. Afectan a los dos regímenes por igual, salvo F4.

## F1. Valores iguales a un umbral (modelo, D23)

**De dónde viene.** Los porcentajes tienen como mucho 4 decimales (D4), y un valor registrado representa cualquier valor real que, redondeado, dé ese número. La entrada no tiene el número de acciones ni de votos.

**Por qué no determina un resultado único.** Si el valor registrado es exactamente un umbral (25 o 50), no se sabe de qué lado está el real. La mitad más una acción se registra como 50 a partir de 1.000.001 acciones si el número es impar, y de 2.000.002 si es par. Con los umbrales del 25 pasa desde 500.001 acciones.

**Qué hace esta implementación.** Lee el valor como exacto (D4, C6). Como prueba de sensibilidad, repite el cálculo leyendo esos valores justo por encima y justo por debajo del umbral (C28).

**Cómo se señala en la salida.** UMBRAL-EXACTO, si alguna de las dos repeticiones cambia quién es titular real, y UMBRAL-EXACTO-NO-COMPROBADO si la repetición no se ha podido hacer. Solo cubre el valor que coincide exactamente con el umbral. Un valor calculado con varias aristas acumula el error de cada una, y esa banda no se calcula. Es el caso 10 del corpus.

## F2. La tolerancia de redondeo en las sumas (modelo, D15)

**De dónde viene.** Con *n* porcentajes redondeados, la suma de una entidad puede apartarse de 100 hasta ⌊n/2⌋ × 0,0001, por encima o por debajo.

**Por qué no determina un resultado único.** Un defecto dentro de esa tolerancia es redondeo o es un titular sin identificar de una fracción de punto: el dato no permite distinguirlo. Un exceso dentro de la tolerancia puede hacer que la serie de un ciclo no converja aunque haya titulares de fuera.

**Qué hace esta implementación.** Lo trata como redondeo: no crea hueco y no reescala los valores (C4). Si el exceso impide que la serie converja, trata el ciclo como un hueco (§6.4, caso límite).

**Cómo se señala en la salida.** El defecto, con nada: una fracción así solo cambiaría algo en el valor exacto de un umbral, que es F1. El ciclo que no converge, con CICLO-CERRADO.

## F3. Magnitudes desconocidas (modelo, D5)

**De dónde viene.** Una arista puede tener el capital o los votos a `null`, que significa «desconocido». La validación lo avisa (AVI-04), pero el modelo no dice qué hace el cálculo con ello.

**Por qué no determina un resultado único.** El valor real puede ser cualquiera entre 0 y lo que falta para 100 en esa entidad.

**Qué hace esta implementación.** Trata la arista como si no tuviera esa magnitud: su parte acaba en el hueco de la participada (`NO_IDENTIFICADO`, C4). Está marcado con `# AMBIGÜEDAD:` en `propagacion.py`.

**Cómo se señala en la salida.** AVI-04 en la validación. Si el hueco es grande, H1, H2, H3 o POS-HUECO, y el resultado no es completo (C33).

## F4. El capital como medida de las «acciones» en el AMLR (modelo, D7)

**De dónde viene.** La entrada tiene dos magnitudes, capital y votos. El AMLR 52.1 habla de «acciones, derechos de voto u otra participación en la propiedad», incluidos los derechos económicos.

**Por qué no determina un resultado único.** Si las acciones no tienen todas el mismo nominal y los mismos derechos, el porcentaje de capital no coincide con el de acciones ni con el de derechos económicos, y la entrada no los distingue.

**Qué hace esta implementación.** Usa el capital como magnitud de «acciones u otra participación en la propiedad» (D7). La equivalencia es exacta solo en el caso proporcional.

**Cómo se señala en la salida.** No se señala: el dato no permite detectarlo. Es una limitación declarada de v0.1 (modelo, §7).

**Régimen.** Solo AMLR. La Ley española habla de «capital».

---

## Lo que no está aquí

Los puntos en los que la especificación o el modelo de datos no bastan para implementar algo, sin que sea un caso de la norma ni del formato del dato, están marcados en el código con `# AMBIGÜEDAD:`. Por ejemplo: qué código lleva un JSON mal formado, cómo se tratan los cargos de entidades que no son la objetivo o qué pasa si la base de la Dir. 22.5 es 0. Se buscan con:

```
grep -rn "AMBIGÜEDAD:" src/
```
