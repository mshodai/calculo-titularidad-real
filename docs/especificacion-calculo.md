# Especificación del cálculo — v0.1

Estado: borrador. Fecha: 2026-09-15. Sin código.

Este documento define cómo se calcula la titularidad real de la `entidad_objetivo` a partir de una entrada válida según [`modelo-datos.md`](modelo-datos.md) v0.1, en dos regímenes:
- **España:** Ley 10/2010, art. 4.2.b y b bis; RD 304/2014, art. 8.b; CCom art. 42 y Dir. 2013/34/UE art. 22, a los que remite la Ley.
- **AMLR:** Reglamento (UE) 2024/1624, arts. 51 a 54, con los arts. 22.2 y 63.4 para el supuesto supletorio.

No fija el formato de salida, solo su contenido mínimo (§9).

## 0. Convenciones

- Las citas literales van entre comillas «…» con artículo, apartado y letra. Las fuentes y sus versiones están en [`fuentes/FUENTES.md`](fuentes/FUENTES.md).
- **[Cn — decisión propia]** marca una elección de este documento que no viene de los textos. El prefijo C evita confusiones con las decisiones D del modelo de datos. Todas están en el §11, con la alternativa descartada y el motivo.
- **[Nn — no resuelto]** marca un caso que la norma no resuelve. Nunca se resuelve en silencio: el §12 dice, para cada uno, qué hace el cálculo y cómo lo señala la salida.
  - **[C25 — decisión propia]** La salida señala un caso N cuando otra lectura del texto se puede calcular con los datos de la entrada y cambiaría quién es titular real. Lo hace con los avisos del §9; en N9 y N13, además, con la marca «por cuenta de».
  - N10 y N11 no tienen señal propia, porque no hay otra lectura con la que comparar. El §12 explica por qué.
- Los porcentajes van de 0 a 100, como en el modelo (D4).
- **Patrón a vigilar: dar por supuesta una condición o un régimen.** Ha aparecido tres veces. La regla de las cotizadas intermedias (C5) trataba como cotizada a una entidad sin comprobar los requisitos de información. AVI-02 y AVI-03 se rebajaban o se omitían en los dos regímenes por una excepción que solo es española (modelo, D26). Al escribir o revisar una regla, hay que comprobar dos cosas:
  - que se cumplen todas las condiciones del texto en que se basa, no solo la más visible;
  - que se aplica solo en el régimen cuyo texto la justifica. Si vale para los dos, cada régimen necesita su propia base.

**Notación** (m es una magnitud: `capital` o `votos`):

| Símbolo | Significado |
|---|---|
| S | La `entidad_objetivo` |
| h_m(X, Y) | Participación directa de X en Y en la magnitud m, tras la preparación del §2 |
| own_m(X, Y) | Participación multiplicativa de X en Y: todas las cadenas, multiplicadas y sumadas (§3.1) |
| C(X, Y) | X controla Y según el AMLR (§3.3) |
| Dep(X) | Entidades dependientes de X según el art. 42 del Código de Comercio (§3.4) |
| va(X, Y) | Votos agregados de X en Y según el art. 42 (§3.4) |
| base(Y) | Total de votos de Y tras el ajuste de la Dir. 22.5 (§3.4) |

---

## 1. Resumen

| | España (lectura aplicada, C19) | AMLR |
|---|---|---|
| Umbral de titularidad | «superior al 25 por ciento» (Ley 4.2.b): **> 25** | «25 % o más» (52.1): **≥ 25** |
| Umbral de control | «mayoría de los derechos de voto» (CCom 42.1.a): **> 50 en votos** (C10) | «50 % más una de las acciones o los derechos de voto» (53.2.c): **> 50 en capital o en votos** |
| Participación indirecta | La Ley no da método. Se aplica la multiplicación (L1, C17) | Multiplicación y suma de cadenas (52.1) |
| Control a mitad de cadena | Votos de las dependientes, sumados enteros (L2, CCom 42.1, último párrafo) | Art. 54.a y 54.b |
| Ciclos | Multiplicación: serie completa (B). Agregación de votos: base de la Dir. 22.5 (C). Ninguna norma lo resuelve (§6) | Serie completa (B). Ninguna norma lo resuelve (§6) |
| Nadie alcanza el umbral | Administradores (4.2.b bis), con carácter condicional en v0.1 | Cargos de dirección de alto nivel, que no son titulares reales (22.2, 63.4) |

---

## 2. Preparación común

Estos pasos transforman la entrada validada en el grafo sobre el que se calcula. Son iguales para los dos regímenes, salvo el §2.5.

### 2.1 Subgrafo relevante

**[C1 — decisión propia]** Solo se calcula sobre los nodos que tienen un camino de aristas hasta S, además de S. El resto ya generó el aviso AVI-08 en la validación y se ignora (modelo, D21). Los `cargos` de S se conservan para el supuesto supletorio (§8).

### 2.2 Participaciones por cuenta de otro

**[C2 — decisión propia]** En todos los cálculos, una arista con `por_cuenta_de` se atribuye al principal, como si él fuera el titular. El titular formal no recibe nada por esa arista.
- **Apoyo en los textos, solo para los votos:**
  - CCom 42.1, último párrafo: se suman a la dominante los votos que tenga «a través de personas que actúen en su propio nombre pero por cuenta de la entidad dominante»;
  - Dir. 22.4.a: se restan al titular formal los derechos de las acciones «de las que se ostente la titularidad por cuenta de una persona distinta».
- **Lo que queda sin resolver:**
  - **[N9 — no resuelto]** El AMLR clasifica los acuerdos de nominatario como control por otros medios (53.4.c) y no dice si cuentan como propiedad del nominador en el cálculo del 52.1.
  - **[N13 — no resuelto]** En España, ningún texto dice a quién se atribuye el capital de una participación por cuenta de otro. El CCom 42.1 y la Dir. 22.4.a solo hablan de votos, y la Ley 4.2.b no menciona a las personas interpuestas. En el AMLR el capital no es un caso aparte: el 52.1 incluye las «acciones», así que forma parte de N9.
- **Lo que registra la salida.** Cada atribución hecha así lleva la marca «por cuenta de», para que se vea que depende de C2.
  - La marca solo sale en quien recibe la participación, así que no cubre el otro lado de N9 y N13: que, con la lectura contraria, fuera titular real el titular formal.
  - **[C29 — decisión propia]** Se repite el cálculo con la lectura contraria, en la que cada arista con `por_cuenta_de` se atribuye a su `titular` formal:
    - **AMLR (N9):** en las dos magnitudes y en todas las pruebas (A1 a A4).
    - **España (N13):** solo en capital. Los votos siguen atribuidos al principal, porque ahí sí hay texto (CCom 42.1 y Dir. 22.4.a). Por eso solo cambia own_capital y, con él, E1. E2 y el dominio no cambian, porque solo usan votos.
  - Si con eso alguien que no es titular real por las reglas aplicadas cumpliría alguna prueba, la salida lo marca **POS-FORMAL**. Puede ser el propio titular formal o, si es una entidad, quien participe en ella o la controle. Nunca lo cuenta como titular real.
  - Lo que el principal pierde con esa lectura ya lo indica la marca «por cuenta de».

### 2.3 Aristas paralelas

**[C3 — decisión propia]** Si, tras C2, un mismo titular tiene varias aristas hacia la misma entidad (por ejemplo, una propia y otra a través de un testaferro), sus valores se suman en cada magnitud para obtener h_m.

### 2.4 Huecos: participaciones sin titular identificado

**[C4 — decisión propia]** Todo lo que no llega a una persona física identificada se representa con **titulares virtuales**, que se propagan como una persona más pero nunca pueden ser titulares reales:

| Caso | Titular virtual |
|---|---|
| Entidad en la cadena cuya suma en la magnitud m es menor que 100 | `NO_IDENTIFICADO(X)`, con 100 − suma en m. Si la suma se aparta de 100 por el redondeo que admite D15, por encima o por debajo, no hay hueco |
| Entidad en la cadena sin titulares | `NO_IDENTIFICADO(X)`, con 100 en capital y en votos |
| Entidad cuya `clase` no es `sociedad` (modelo, D8) | `OPACA(X)`: sus titulares no se recorren y ella recibe todo lo que le llegue |

El volumen que llega a S a través de estos titulares virtuales se usa en los avisos del §9 y puede impedir el supuesto supletorio (§8).

### 2.5 Sociedades cotizadas

**[C5 — decisión propia]**
- **España:**
  - **Si S tiene `cotizacion` con `requisitos_informacion_ue_o_equivalentes: true`,** el resultado es «exceptuada» y no se calcula. Base: Ley 4.2.b, párr. 3, «Se exceptúan las sociedades que coticen en un mercado regulado y que estén sujetas a requisitos de información acordes con el Derecho de la Unión o a normas internacionales equivalentes».
  - **Si una entidad intermedia tiene `cotizacion` con `requisitos_informacion_ue_o_equivalentes: true`,** sus titulares no se recorren. Lo que llega a través de ella se atribuye a un titular virtual `COTIZADA(X)`, que no genera avisos de hueco.
    - Base: RD 9.4, «No será preceptiva la identificación de los accionistas o titulares reales de empresas cotizadas o de sus filiales participadas mayoritariamente cuando aquéllas estén sometidas a obligaciones de información que aseguren la adecuada transparencia de su titularidad real».
    - La excepción depende de esa condición («cuando aquéllas estén sometidas…»), no solo de cotizar. Es la valoración que D13 pide afirmar por separado, la misma que exige D26 en la validación.
    - **Con `false`, la intermedia se trata como cualquier otra entidad:** se recorren sus titulares, y lo que falte es un hueco (C4).
    - El modelo solo tiene un dato para esa condición, redactado según la Ley 4.2.b, párr. 3 («requisitos de información acordes con el Derecho de la Unión o a normas internacionales equivalentes»). Se usa también para la del RD 9.4, que lo dice de otra forma, igual que en D26.
  - **[C30 — decisión propia] Filiales de cotizadas.** El RD 9.4 exime también a las «filiales participadas mayoritariamente» de las cotizadas, «cuando aquéllas estén sometidas a obligaciones de información». «Aquéllas» son las cotizadas, así que la condición se mira en la cotizada, no en la filial.
    - **[N14 — no resuelto]** El texto no dice cómo se mide «participada mayoritariamente»: con qué magnitud, ni si cuenta la participación indirecta.
    - **Qué es una filial participada mayoritariamente.** X lo es de L si L tiene `cotizacion` con `requisitos_informacion_ue_o_equivalentes: true` y own_capital(L, X) > 50 (§3.1). Es decir, L tiene más de la mitad del capital de X, directamente o sumando cadenas.
    - **Con el capital,** porque «participada» habla de participación. Cuando la Ley y el CCom se refieren a los votos, hablan de «control» o «dominio», y el RD 9.4 no usa esas palabras.
    - **Directa o indirecta, multiplicando.** «Filiales» incluye las indirectas, y la multiplicación es la medida de participación de este documento (C17). Una cadena de mayorías no basta: el 60 % del 60 % es un 36 %, que no es una participación mayoritaria.
    - **Cada cotizada por separado.** Dos cotizadas que juntas pasan del 50 % no hacen filial a nadie: el texto dice «sus filiales».
    - **Por qué la lectura estrecha.** El RD 9.4 dice «no será preceptiva la identificación»: dispensa, no prohíbe. Si la lectura se queda corta, como mucho se identifica a alguien sin necesidad. Si se pasa, deja sin identificar a un titular real que el texto no dispensa.
    - **Si S es filial de una cotizada,** el resultado es «exceptuada», como si cotizara. La salida indica la base (RD 9.4), la cotizada y su participación en S.
    - **Si la filial es una entidad intermedia, no se aplica:** se recorren sus titulares como los de cualquier otra entidad.
      - Lo que llega a través de la propia cotizada ya va a `COTIZADA(L)`, por la regla anterior.
      - La exención solo añadiría dejar de recorrer a los demás socios de la filial, y la transparencia de la cotizada no los cubre. En el Ej. 8b, un socio con el 49 % de la filial tiene el 34,3 % de S y es titular real.
      - El RD 9.4 habla del cliente. Extenderlo a las intermedias es una decisión de este documento, y aquí no hay razón para hacerlo.
    - **Señal de N14.** Si S no es filial según esta regla, pero lo sería con otra lectura, la salida da el aviso **EXENCION-SENS**. Las otras lecturas son dos: medir con los votos (own_votos(L, S) > 50) y aceptar una cadena de participaciones directas de más del 50 % del capital en cada nivel. Con cualquiera de ellas, la identificación no sería preceptiva (C25).
- **AMLR:** la cotización no cambia el cálculo, tampoco la de la sociedad de la que S es filial. El art. 65.a exime a ciertas cotizadas de las obligaciones de los arts. 63 y 64, pero no toca la definición de los arts. 51 a 55. Si S cotiza, la salida lo indica como información.

### 2.6 Aritmética

**[C6 — decisión propia]**
- Todos los cálculos se hacen con **fracciones exactas**: la entrada, que tiene como mucho 4 decimales (D4), es racional, y los sistemas del §3.1 dan resultados racionales.
- Las comparaciones con los umbrales (25 y 50) también son exactas. Solo se redondea al mostrar el resultado, a 2 decimales.
- Motivo: la diferencia entre «> 25» y «≥ 25» se decide justo en el 25. Por ejemplo, 23,5 / 94 vale exactamente 25; con aritmética binaria podría salir ligeramente por encima o por debajo.

**[C28 — decisión propia] Valores iguales a un umbral.** La aritmética es exacta, pero los datos no siempre lo son. Con 4 decimales, a partir de cierto número de acciones un valor registrado como 25 o 50 puede esconder una participación que en realidad está justo al otro lado del umbral (modelo, D23).
- El valor registrado se toma como exacto, y así se decide el resultado.
- Como prueba de sensibilidad, cada régimen se calcula dos veces más:
  - leyendo todo valor comparado que coincida con un umbral como si estuviera justo por encima (todas las comparaciones con 25 y 50 pasan a «≥»);
  - y como si estuviera justo por debajo (pasan a «>»).
- Si alguna de las dos cambia quién es titular real, la salida da el aviso **UMBRAL-EXACTO**.
- El aviso no cambia el estado del resultado. Solo dice que el resultado depende de un valor que, si viene de redondear, podría estar al otro lado.
- Si en una de las repeticiones el dominio no se estabiliza (§3.4), esa repetición queda sin hacer y la salida lo indica.

### 2.7 Fecha de aplicación del AMLR

**[C7 — decisión propia]** Si `fecha_referencia` es anterior al 2027-07-10, el AMLR se calcula igualmente, porque comparar los dos regímenes es el objetivo del proyecto, pero la salida avisa de que todavía no es aplicable. Base: AMLR art. 90, «Será aplicable a partir del 10 de julio de 2027».

---

## 3. Primitivas de cálculo

### 3.1 Participación multiplicativa: own_m(X, Y)

**Qué calcula.** La parte de Y que corresponde a X en la magnitud m, multiplicando los porcentajes a lo largo de cada cadena de X a Y y sumando todas las cadenas. Es la regla del AMLR 52.1: «multiplicando las acciones o los derechos de voto u otra participación en la propiedad de la que sean titulares las entidades intermedias de la cadena […] y sumando los resultados de esas distintas cadenas».

**[C8 — decisión propia] Cómo se calcula:**
- **No se enumeran las cadenas: se resuelve un sistema lineal.** Para cada entidad Y del subgrafo:

  own_m(X, Y) = h_m(X, Y) + Σ_Z own_m(X, Z) · h_m(Z, Y) / 100

  donde Z recorre las entidades que tienen participación en Y. Todo va en porcentaje (0–100), como la entrada.
- **Qué incluye.** Equivale a sumar todas las cadenas de X a Y, también las que dan vueltas a un ciclo (método B del §6).
- **X como origen.** Al calcular la participación de X, se ignoran las aristas que entran en X. Así, si X es una entidad, su participación en Y no se cuenta dos veces a través de sus propios accionistas. Las personas físicas no tienen aristas de entrada, así que para ellas no cambia nada.
- **Si el sistema no tiene solución única** (un ciclo cerrado al 100 %, sin titulares fuera de él), no se puede calcular: ver §6.4.
- **Explicación en la salida.** Se listan las cadenas sin repeticiones y, aparte, lo que aporta cada ciclo.

**[C9 — decisión propia] Las magnitudes se propagan por separado:** own_capital multiplica solo capitales y own_votos solo votos. Dónde se mezclan y qué se hace con la mezcla está en el §7.

### 3.2 Umbral de control

**[C10 — decisión propia]** Hay control cuando se supera estrictamente el 50:
- **AMLR:** en capital **o** en votos. 53.2.c: «la propiedad directa o indirecta del 50 % más una de las acciones o los derechos de voto».
- **España:** solo en votos. CCom 42.1.a: «Posea la mayoría de los derechos de voto».
- **Por qué «> 50».** El texto del AMLR dice «50 % más una» acción y el del Código, «mayoría», pero la entrada solo tiene porcentajes, no número de acciones. Si los porcentajes salen del número de acciones, superar el 50 % equivale a tener al menos la mitad más una. **[N10 — no resuelto]** El Código no dice qué es «mayoría».
- **Límite de los datos.** Con 4 decimales, la mitad más una acción se registra como 50 a partir de 1.000.001 acciones si el número es impar, y de 2.000.002 si es par (modelo, D23). Lo señala el aviso UMBRAL-EXACTO (C28).

### 3.3 Control en el AMLR: C(X, Y)

- **53.2.a:** control es «la posibilidad de ejercer, directa o indirectamente, una influencia significativa e imponer decisiones pertinentes en la entidad».
- **53.2.b:** control indirecto es «el control de entidades jurídicas intermedias en la estructura de propiedad o en diversas cadenas de la estructura de propiedad, cuando se identifica el control directo en cada nivel de la estructura».
- **53.2.c:** control a través de participación es «la propiedad directa o indirecta del 50 % más una».

**[C11 — decisión propia]** C(X, Y) se cumple si ocurre alguna de estas dos cosas (es el cierre transitivo de la relación):
1. own_capital(X, Y) > 50 u own_votos(X, Y) > 50. Es la «propiedad directa o indirecta» del 53.2.c, e incluye la participación directa.
2. Existe una entidad Z tal que C(X, Z) y C(Z, Y). Es el control «en cada nivel» del 53.2.b.

El control por otros medios (53.3 y 53.4) queda fuera de v0.1 (modelo, D19).
- **[N8 — no resuelto]** El AMLR no dice si X controla Y cuando varias entidades controladas por X suman juntas más del 50 % de Y, sin que ninguna lo tenga por sí sola. En v0.1 no se considera control.
  - **[C26 — decisión propia]** Para avisar se calcula también **C⁺**, que añade a C11 una tercera condición: X controla Y si lo que tienen en Y X y las entidades Z con C⁺(X, Z), sumado entero, pasa de 50 en capital o en votos.
    - Es la agregación del art. 42 (§3.4), sin ajuste de base y en cualquiera de las dos magnitudes. Incluye lo que X tiene directamente, como el art. 42: para avisar se toma la lectura más amplia.
    - Se calcula por rondas desde C hasta que no cambia. Como cada ronda solo añade relaciones, termina.
    - Si con C⁺ en lugar de C alguien cumple A2, A3 o A4 (§4.5) y no es titular real por las reglas aplicadas, la salida lo marca **POS-AGREGADO**. Nunca lo cuenta como titular real.
- **[N11 — no resuelto]** Como el 53.2.c dice «acciones o los derechos de voto», dos personas pueden controlar a la vez la misma entidad: una con más del 50 % del capital y otra con más del 50 % de los votos (Ej. 4). El texto lleva a ese resultado y no dice nada sobre él.

### 3.4 Dominio y votos agregados en España: Dep(X) y va(X, Y)

**Base textual:**
- CCom 42.1.a: «Posea la mayoría de los derechos de voto».
- CCom 42.1, último párrafo: «a los derechos de voto de la entidad dominante se añadirán los que posea a través de otras sociedades dependientes o a través de personas que actúen en su propio nombre pero por cuenta de la entidad dominante o de otras dependientes».
- Dir. 22.5: «deben sustraerse de la totalidad de los derechos de voto […] los derechos de voto propios de las acciones o participaciones de las que sea titular esta misma empresa, una empresa filial de esta, o una persona que actúe en su propio nombre pero por cuenta de dichas empresas».

**[C12 — decisión propia] Definición:**
- **Votos neutralizados de Y:** los que tienen Y misma y sus dependientes, es decir, los h_votos(Z, Y) con Z ∈ {Y} ∪ Dep(Y). Es el supuesto de la Dir. 22.5.
- **Base ajustada:** base(Y) = 100 − votos neutralizados de Y.
- **Votos agregados:** va(X, Y) = suma de h_votos(Z, Y) para Z ∈ {X} ∪ Dep(X), **sin contar los votos neutralizados de Y**. Las personas interpuestas ya están incluidas por C2.
  - Sin esa exclusión, los mismos votos saldrían de la base y a la vez se sumarían al dominante de Y. Si P domina S y S domina H, los votos de H en S contarían para P y a la vez se restarían del total.
  - La primera versión de esta definición tenía ese error. Lo detectó la verificación del §6.5: en el ejemplo del modelo, §4.2, daba 81,25 % en lugar de 56,25 %.
- **Dominio:** Y ∈ Dep(X) si va(X, Y) · 100 / base(Y) > 50.
- **Cálculo.** Se empieza con Dep(X) vacío para todo X. En cada ronda se recalculan todas las relaciones a partir de las de la ronda anterior, hasta que no cambie nada.
  - Las dependientes de una dependiente se incorporan solas en el recálculo.
  - No está garantizado que se estabilice: al ampliarse Dep(Y), la exclusión de votos neutralizados puede hacer que otra relación deje de cumplirse.
  - Si una ronda repite el estado de una anterior sin estabilizarse, el cálculo se detiene, la salida avisa (DOMINIO-INESTABLE) y la prueba E2 queda como no determinable. Como hay un número finito de estados, esa comprobación siempre termina.

**Cuatro cosas que esta definición supone:**
- **La persona física como dominante.** El art. 42 está escrito entre sociedades; aplicarlo a personas físicas es la transposición que exige la remisión de la Ley 4.2.b.
- **Solo la letra a) del art. 42.1.** Las letras b) a d) y el concierto necesitan datos de control por otros medios, fuera de v0.1.
- **Mayoría estricta:** «> 50» (C10).
- **La base de la Dir. 22.5 también se usa en España,** porque la Ley remite al art. 22, apartados 1 a 5.

### 3.5 Atribución con transparencia del control (lectura extensiva)

**[C13 — decisión propia]** Se calcula como own_m (§3.1), pero dando peso 1 a cada arista en la que el titular controla directamente a la participada:
- **AMLR:** h_capital > 50 o h_votos > 50.
- **España:** h_votos · 100 / base > 50.
- Las demás aristas pesan h_m / 100.

Se escribe eff_m(P, S).
- **Solo se usa para avisar.** Nunca convierte a nadie en titular real. Sirve para señalar los casos que los textos no regulan (§4.4 y §5.2).
- **Si la serie no converge** (un ciclo formado solo por aristas de control), eff no se puede calcular y se avisa.

---

## 4. AMLR

### 4.1 Reglas

- **51:** son titulares reales las personas físicas que, directa o indirectamente, «a) tengan una participación en la propiedad de la sociedad, o b) controlen la sociedad u otra entidad jurídica a través de una participación en la propiedad o por otros medios». En el documento pone «una participación den la propiedad» (errata).
- **51, párrafo 2:** el control por otros medios se determina «independientemente de la existencia de un derecho de propiedad o de un control a través de una participación en la propiedad, y de manera paralela a esta».
- **52.1:** «participación en la propiedad de la sociedad» es «la propiedad directa o indirecta del 25 % o más de las acciones, derechos de voto u otra participación en la propiedad». La indirecta se calcula multiplicando y sumando cadenas, «salvo que resulte de aplicación el artículo 54». Además, «se tendrán en cuenta todas las participaciones en todos los niveles de propiedad».
- **54:** «Cuando el derecho de propiedad sobre sociedades se ejerza a través de una estructura de propiedad con múltiples niveles, y cuando en una o varias cadenas de dicha estructura coexista la participación en la propiedad y el control en relación con diferentes niveles de la cadena, el titular o titulares reales serán:
  - a) la persona o personas físicas que controlen, directa o indirectamente, a través de participación en la propiedad o por otros medios, entidades jurídicas titulares de una participación en la propiedad directa de la sociedad, ya sea de forma individual o acumulativa;
  - b) la persona o personas físicas que, ya sea individual o acumulativamente, directa o indirectamente, sean titulares de una participación en la propiedad de la sociedad que controle directa o indirectamente la sociedad a través de una participación en la propiedad o por otros medios.»
- **Considerando 108:** «es necesario evaluar simultáneamente si alguna persona física posee una participación directa o indirecta con el 25 % o más de las acciones, derechos de voto u otra participación en la propiedad, y si alguna persona física controla al accionista directo con el 25 % o más».

### 4.2 Cuándo se aplica el 52.1 y cuándo el 54

Una cadena de P a S se puede partir en tramos de dos tipos:
- **tramo C:** aristas en las que el titular controla a la participada;
- **tramo O:** aristas sin control, es decir, de participación.

| Forma de la cadena | Regla que la cubre | Qué se atribuye a P |
|---|---|---|
| Solo O (O…O) | 52.1 | El producto de la cadena |
| Solo C (C…C) | 51.b (control indirecto, 53.2.b) y 54.a | P controla S |
| C…C y después un único O (P controla un accionista directo D) | 54.a | h(D, S) entero, no multiplicado |
| O…O y después C…C (una entidad K controla S) | 54.b | Basta con own(P, K) ≥ 25 |
| Otras formas (C O O…, O C O…, varias alternancias) | **Ninguna** | Ver §4.4 |

**[N3 — no resuelto]** El 52.1 dice «salvo que resulte de aplicación el artículo 54», pero no aclara si el 54 **sustituye** al 52.1 en las cadenas mixtas o si se **añade** a él.

**[C14 — decisión propia]** Se aplican todas las pruebas y el resultado es su unión: una persona es titular real si cumple el 52.1, el 51.b, el 54.a o el 54.b.
- **Por qué:**
  - el considerando 108 pide «evaluar simultáneamente» la participación y el control del accionista directo;
  - el considerando 106 dice que las pruebas «deben realizarse en paralelo»;
  - el art. 51 define al titular real con una disyunción («a) […], o b) […]»).
- **Qué cambia con la lectura contraria** (el 54 sustituye al 52.1): puede dejar fuera a quien llega al 25 % por pura multiplicación a través de una cadena que tiene un tramo de control. Pasa en el Ej. 5b del §10 y con P-CARLOS en el ejemplo del modelo (§6.3).

**[C27 — decisión propia]** La lectura contraria se comprueba en cada entrada:
- Se calcula **own^O_m(P, S)** como own_m (§3.1), pero sin las aristas Z → Y en las que C(Z, Y). Es lo que dan las cadenas sin ningún tramo de control, las únicas a las que se aplicaría el 52.1 si el 54 lo sustituyera.
- Si P es titular real solo por A1 y own^O_m(P, S) < 25 en las dos magnitudes, la salida da el aviso **ART54-SENS**: con la lectura contraria, P dejaría de serlo.
- P sigue siendo titular real (C14).

### 4.3 Control a mitad de cadena

Hay dos formas que el art. 54 sí regula:

**54.a: el control está arriba y la participación abajo.** P controla, directa o indirectamente, una o varias entidades D que son accionistas directos de S.
- La participación directa de esas D en S se atribuye entera a P, sin multiplicar. Se suman las de todas las D que P controla («ya sea de forma individual o acumulativa»).
- **[C15 — decisión propia]** Solo se suman las participaciones de las entidades controladas. La participación directa de P en S no se añade, porque el texto dice «entidades jurídicas titulares».
  - **[N5 — no resuelto]** Si P tiene un 10 % directo y controla una entidad con otro 20 %, el 54.a no dice si eso suma 30 %. La lectura extensiva (§3.5) sí lo suma, y ese caso se avisa.

**54.b: la participación está arriba y el control abajo.** Una entidad K controla S, directa o indirectamente (C(K, S)).
- Son titulares reales quienes tienen al menos el 25 % de K. Ese porcentaje se calcula con el 52.1.
- **[C16 — decisión propia]** «individual o acumulativamente, directa o indirectamente» se interpreta como la suma de cadenas del 52.1 aplicada a K: own(P, K) ≥ 25.
- En la práctica, el control de K sobre S hace que S sea transparente hacia K.

### 4.4 Cadenas con varios tramos de control

**[N4 — no resuelto]** El art. 54 solo contempla un cambio: control arriba y participación abajo (a), o participación arriba y control abajo (b). No dice nada de cadenas como C O C O.

**Ejemplo (Ej. 5):** P —60 %→ A —50 %→ B —60 %→ C —50 %→ S.
- **54.a no se aplica:** P controla A, pero A no controla B. Por tanto P no controla C, que es el accionista directo.
- **54.b no se aplica:** C tiene solo el 50 % de S y no la controla.
- **52.1:** 0,6 × 0,5 × 0,6 × 0,5 = 9 %.
- **Lectura extensiva (§3.5):** 1 × 0,5 × 1 × 0,5 = 25 %, que alcanza el umbral del AMLR (≥ 25).

**Cota útil.** En el AMLR, un tramo sin control tiene tanto el capital como los votos en 50 o menos, porque si no sería control (C10). Por eso, una sola cadena con dos o más tramos O no puede pasar del 25 %, ni multiplicando ni con la lectura extensiva. Consecuencias:
- las formas no reguladas solo cambian el resultado de una cadena aislada si da exactamente el 25 %;
- en los demás casos importan cuando se suman varias cadenas o una participación directa (N5).

**Qué hace el cálculo.** Aplica las reglas literales (§4.5). Si la lectura extensiva da eff_m(P, S) ≥ 25 para alguien que no es titular real por esas reglas, lo marca como «posible titular real: forma de cadena no regulada (N4/N5)». Nunca lo cuenta como titular real (C13).

### 4.5 Algoritmo

1. **Preparar el grafo** (§2).
2. **Calcular own_m(P, X)** para cada persona física P, cada titular virtual y cada entidad X (§3.1).
3. **Calcular la relación de control C** (§3.3).
4. **Aplicar las pruebas a cada persona física P,** en cada magnitud m:

| Prueba | Condición | Base |
|---|---|---|
| A1 | own_m(P, S) ≥ 25 | 51.a y 52.1 |
| A2 | C(P, S) | 51.b y 53.2 |
| A3 | La suma de h_m(D, S) de los accionistas directos D de S que son entidades y cumplen C(P, D) es ≥ 25 | 54.a y C15 |
| A4 | Existe una entidad K de clase `sociedad` con C(K, S) y own_m(P, K) ≥ 25 | 54.b y C16 |

5. **Condición de titular real:** P lo es si cumple alguna prueba en alguna magnitud (C14). La salida guarda qué pruebas y qué magnitudes cumple, con sus valores.
6. **Avisos** (§9):
   - lectura extensiva (C13), si eff_m(P, S) ≥ 25 y P no es titular real;
   - control agregado (C26);
   - sensibilidad al art. 54 (C27);
   - lectura contraria de N9 (C29);
   - mezcla de magnitudes (§7);
   - huecos (§9);
   - sensibilidad al método de ciclos (§6);
   - valores iguales a un umbral (C28).
7. **Si nadie es titular real,** se aplica el supuesto supletorio (§8.2).

---

## 5. España

### 5.1 Qué dice la Ley y qué no dice

- **Ley 4.2.b:** «La persona o personas físicas que en último término posean o controlen, directa o indirectamente, un porcentaje superior al 25 por ciento del capital o de los derechos de voto de una persona jurídica, o que por otros medios ejerzan el control, directo o indirecto, de una persona jurídica. A efectos de la determinación del control serán de aplicación, entre otros, los criterios establecidos en el artículo 42 del Código de Comercio.»
- El RD 304/2014, art. 8.b, repite la fórmula y no añade un método.

**[N1 — no resuelto]** Ni la Ley ni el RD dicen cómo se calcula el porcentaje indirecto.

**[N2 — no resuelto]** La remisión al art. 42 es «a efectos de la determinación del control». No se dice si también sirve para medir el porcentaje que alguien «controla».

### 5.2 Lecturas posibles

| Lectura | Qué significa «posean o controlen, directa o indirectamente, un porcentaje superior al 25 %» | Cálculo |
|---|---|---|
| **L1: multiplicación** | «Poseer indirectamente» es tener la parte proporcional de lo que tienen las sociedades intermedias | own_m(P, S) > 25 (§3.1) |
| **L2: art. 42** | «Controlar un porcentaje» es disponer de los votos de las dependientes, sumados enteros: el control del art. 42 aplicado a medir el porcentaje | va(P, S) · 100 / base(S) > 25 (§3.4). Solo votos |
| **L3: transparencia del control** | Las sociedades que P controla son transparentes (peso 1); el resto se multiplica | eff_m(P, S) > 25 (§3.5) |

Hay una cuarta lectura, **L0 (solo participaciones directas),** que el propio texto descarta: la Ley dice «directa o indirectamente».

**Qué da cada una.** Los números están en el §10:
- **L1** falla cuando hay control a mitad de cadena. En el Ej. 2, quien controla una sociedad con el 30 % de S solo suma 60 % × 30 % = 18 %.
- **L2** cubre el caso del 54.a, pero solo en votos. No cubre el del 54.b: quien tiene el 30 % de una sociedad que controla S no domina esa sociedad, así que no agrega nada (Ej. 3).
- **L3** cubre los dos casos y cualquier alternancia. No tiene ningún apoyo en el texto español.

Dos observaciones:
- Con cualquier lectura, **el art. 42 solo mira los votos.** Una mayoría de capital sin mayoría de votos no es dominio (Ej. 4).
- La cota del §4.4 vale en España **solo para los votos.** Como el capital no da control, una arista con el 90 % del capital y el 10 % de los votos es un tramo sin control con peso 0,9 en capital.

### 5.3 Qué lectura se aplica

**[C17 — decisión propia]** L1 se usa para «posean»: la Ley no da método, y la multiplicación es la única de las tres que atribuye una parte proporcional sin exigir control. Es también la del AMLR 52.1.

**[C18 — decisión propia]** L2 compara con el 25 % sobre la misma base ajustada que usa para decidir el dominio. La Dir. 22.5 está escrita para decidir la mayoría y aquí se extiende a medir el porcentaje.

**[C19 — decisión propia] Elijo L1 ∪ L2 como lectura aplicada.** Una persona es titular real en España si supera el 25 % en L1 (capital o votos) o en L2 (votos).
- **Por qué:**
  - L1 es la forma natural de medir «posean»;
  - L2 es la única lectura de «controlen» basada en un texto al que la Ley remite expresamente (art. 42);
  - L3 amplía más allá de lo que dicen los textos españoles.
- **Qué se hace con L3.** Se calcula solo para avisar: quien sea titular real por L3 y no por L1 ∪ L2 sale como «posible titular real: lectura extensiva (N1/N2)».
  - El aviso cubre N1 y N2 a la vez. L3 es otra respuesta tanto a cómo se mide el porcentaje indirecto (N1) como a si el control sirve para medirlo (N2).
  - De las respuestas a N1 que recoge el §5.2, L0 la descarta el texto, L2 ya se aplica y L3 queda señalada con este aviso.
- **Alternativas descartadas** (§11):
  - **L1 sola:** deja fuera a quien controla una sociedad con el 30 %, a pesar de que la Ley remite al art. 42 para el control;
  - **L3:** convertiría en titular real a quien tiene el 30 % de una sociedad que controla S (Ej. 3), cosa que solo apoya el AMLR.

### 5.4 Algoritmo

1. **Preparar el grafo** (§2). Si S es cotizada exceptuada (C5), o filial participada mayoritariamente de una cotizada (C30, con own_capital del §3.1), el resultado es «exceptuada» y se termina.
2. **Calcular own_m(P, X)** (§3.1).
3. **Calcular Dep, va y base** (§3.4).
4. **Aplicar las pruebas a cada persona física P:**

| Prueba | Condición | Base |
|---|---|---|
| E1 | own_capital(P, S) > 25 u own_votos(P, S) > 25 | Ley 4.2.b («posean») y C17 |
| E2 | va(P, S) · 100 / base(S) > 25 | Ley 4.2.b («controlen»), CCom 42.1, C12 y C18 |

   Si además S ∈ Dep(P), la salida indica que P controla S (CCom 42.1.a). Esto no hace falta para ser titular real, porque ya implica E2.
5. **Condición de titular real:** E1 o E2 (C19).
6. **Avisos** (§9):
   - lectura L3;
   - lectura contraria de N13 (C29);
   - mezcla de magnitudes;
   - huecos;
   - sensibilidad al método de ciclos;
   - valores iguales a un umbral (C28).
7. **Si nadie es titular real,** se aplica el supuesto supletorio (§8.1).

---

## 6. Ciclos

### 6.1 Qué dicen las normas

**Ninguna norma resuelve cómo tratar un ciclo al calcular la titularidad real** **[N7 — no resuelto]**. El análisis de fuentes está en el modelo, §4.1:
- **Ley 10/2010, RD 304/2014, RD 609/2023 y CCom 42:** no dicen nada.
- **AMLR:** tampoco dice nada expreso. El 52.1 manda sumar «los resultados de esas distintas cadenas» y tener en cuenta «todas las participaciones en todos los niveles». Con un ciclo hay infinitas cadenas.
- **Dir. 22.5:** saca de la base los votos que una empresa tiene sobre sí misma o a través de sus filiales. Es la única norma que trata un ciclo, y lo hace para decidir el control, no la titularidad real.

### 6.2 Método que se aplica

**[C20 — decisión propia]**
- **Para la multiplicación (AMLR 52.1 y L1 en España): método B, la serie completa.** Se resuelve el sistema del §3.1. Por qué:
  - es el único que suma *todas* las cadenas, como pide la letra del 52.1; el método A excluye unas cadenas con un criterio que no está en ningún texto;
  - reparte exactamente el 100 %: lo atribuido a titulares últimos más los huecos suma 100. El método A pierde una parte;
  - con autocartera (una arista reflexiva con x %), da p / (1 − x), que es lo mismo que sacar la autocartera de la base. Coincide con la lógica de la Dir. 22.5.
    - **[N12 — no resuelto]** El AMLR no dice si la autocartera se descuenta al decidir el control (53.2.c). Como C11 usa own_m, con el método B se descuenta de hecho: con un 10 % de autocartera, quien tiene el 48 % pasa a tener 48 / 0,9 = 53,33 % y controla. Con el método A no se descuenta: la cadena que pasa por la arista reflexiva repite entidad, y se queda en 48 %. Por eso la prueba de sensibilidad de abajo cubre también N12.
- **Para la agregación de votos (L2 en España): método C, la base de la Dir. 22.5** (§3.4). Por qué:
  - es un texto al que la Ley remite (Dir. 22, apartados 1 a 5);
  - encaja con la lógica del art. 42, que atribuye enteros los votos de las dependientes.
- **Como prueba de sensibilidad se calcula también el método A** (solo cadenas que no repiten entidad) para E1 y para las cuatro pruebas del AMLR. Con own_m del método A se recalcula también la relación de control C (§3.3) y, con ella, A2, A3 y A4. Si cambia quién es titular real, la salida lo avisa: «el resultado depende del método de ciclos (N7/N12)».

### 6.3 Aplicación al ejemplo del modelo de datos

Ejemplo del modelo, §10: ciclo E-OBJETIVO → E-BETA (50 %) → E-HOLDING (40 %) → E-OBJETIVO (30 % de capital / 35 % de votos).
- Cada vuelta al ciclo multiplica por 0,5 × 0,4 × 0,30 = 0,06 en capital y por 0,5 × 0,4 × 0,35 = 0,07 en votos.
- Por C2, la participación de P-BRUNO (arista p03) se atribuye a P-CARLOS.

| Titular | Capital, método B | Votos, método B | Capital, método A | Votos, método A |
|---|---|---|---|---|
| P-ANA | 38/94 = **40,43 %** | 46/93 = **49,46 %** | 38 % | 46 % |
| P-CARLOS | 24/94 = **25,53 %** | 27/93 = **29,03 %** | 24 % | 27 % |
| P-DIEGO | 12/94 = 12,77 % | 20/93 = 21,51 % | 12 % | 20 % |
| NO_IDENTIFICADO(E-FONDO) | 20/94 = 21,28 % | 0 % | 20 % | 0 % |
| P-BRUNO (testaferro) | 0 % | 0 % | 0 % | 0 % |
| **Suma** | **100 %** | **100 %** | 94 % | 93 % |

Cómo se obtienen las cifras del método B: P-ANA tiene 20 % directo y 60 % × 30 % = 18 % a través de E-HOLDING, en total 0,38, dividido entre (1 − 0,06). P-CARLOS tiene 18 % a través del testaferro y 50 % × 40 % × 30 % = 6 % a través de E-BETA, en total 0,24, dividido entre (1 − 0,06). En votos: P-ANA, (0,25 + 0,6 × 0,35) / 0,93; P-CARLOS, (0,20 + 0,5 × 0,4 × 0,35) / 0,93.

**Agregación de votos (método C):**
- E-OBJETIVO no tiene dependientes: su 50 % en E-BETA no es mayoría. Por tanto base(E-OBJETIVO) = 100 y no se ajusta nada.
- P-ANA domina E-HOLDING (60 %), así que va(P-ANA, E-OBJETIVO) = 25 + 35 = 60 → **P-ANA controla E-OBJETIVO** en L2.
- P-CARLOS no domina E-BETA (50 %), así que va(P-CARLOS, E-OBJETIVO) = 20, lo que tiene a través del testaferro.

**Resultado:**

| | AMLR | España |
|---|---|---|
| P-ANA | Titular real: A1 (40,43 / 49,46) y A3 (controla E-HOLDING, que tiene 30 / 35 directo). No controla E-OBJETIVO: 49,46 no pasa de 50 | Titular real: E1 (40,43 / 49,46) y E2 (60 %). Además **controla** E-OBJETIVO (CCom 42.1.a) |
| P-CARLOS | Titular real: A1 (25,53 en capital, 29,03 en votos), por cuenta de | Titular real: E1 (25,53 / 29,03), por cuenta de |
| P-DIEGO | No es titular real (12,77 / 21,51). Aviso de hueco: 12,77 + 21,28 = 34,04 ≥ 25, así que **podría serlo si participa en E-FONDO** | Igual (34,04 > 25) |
| Sensibilidad al método de ciclos | Con el método A, P-CARLOS se queda en 24 % de capital, pero sigue siéndolo por votos (27 %). La relación de control tampoco cambia. **El conjunto de titulares no cambia** | Igual |
| Sensibilidad al art. 54 (N3) | P-CARLOS lleva **ART54-SENS** (ver abajo) | No aplica |

**Por qué no importa aquí el método:** P-CARLOS está cerca del umbral en capital (25,53 con B frente a 24 con A), pero los votos (29,03 y 27) lo mantienen en los dos métodos. Con otros datos, el mismo ciclo sí cambiaría el resultado. Por eso existe el aviso de sensibilidad.

**Lo que sí depende de N3:**
- **P-CARLOS controla E-BETA en el AMLR** (C11). Tiene el 50 % directo y, a través de E-OBJETIVO, la mitad de lo que tiene en ella: en total 62,77 % de capital y 64,52 % de votos.
- **Su cadena por E-BETA es mixta.** Tiene un tramo de control seguido de dos sin control, una forma que el art. 54 no regula (§4.2).
- **Sin esa cadena no llega al umbral:** se queda en 18/94 = 19,15 % de capital y 20/93 = 21,51 % de votos.
- **Resultado.** Es titular real por la unión de pruebas (C14), pero dejaría de serlo si el 54 sustituyera al 52.1. Por eso la salida da ART54-SENS.

**Lectura contraria de N9 y N13 (C29):**
- **AMLR (N9).** Si la arista p03 se atribuyera a P-BRUNO, él tendría 18/94 = 19,15 % de capital y 20/93 = 21,51 % de votos. No llega al 25 ni controla nada, así que no hay POS-FORMAL. Con esa lectura, P-CARLOS dejaría de ser titular real, cosa que ya indica la marca «por cuenta de».
- **España (N13), solo capital.** P-BRUNO tendría el mismo 19,15 % de capital, que no pasa de 25: tampoco hay POS-FORMAL. P-CARLOS se quedaría en 6/94 = 6,38 % de capital, pero seguiría siendo titular real por votos (29,03 %), que no cambian.

**Valores iguales a un umbral (C28):** el ejemplo tiene dos del 50 % en E-BETA, pero leerlos por encima o por debajo no cambia quién es titular real en ninguno de los dos regímenes. No hay UMBRAL-EXACTO.

**Los regímenes no discrepan en quién es titular real, pero sí en el criterio:** en España P-ANA controla E-OBJETIVO porque se suman sus votos y los de E-HOLDING, que domina; en el AMLR nadie la controla.

### 6.4 Ciclos cerrados

Si un grupo de entidades se tiene entre sí al 100 %, sin ningún titular de fuera, el sistema del §3.1 no tiene solución única. Esas entidades se tratan como un hueco (`NO_IDENTIFICADO`) y la salida avisa de «ciclo cerrado: sin titulares externos».
- **Cómo se detecta:** por la estructura, antes de resolver el sistema. Es un grupo de entidades conectadas en ciclo en el que ninguna tiene titulares de fuera del grupo, ni reales ni huecos.
- **Caso límite:** si hay titulares de fuera pero, por el exceso de redondeo que admite D15, la serie no converge, se trata igual.

### 6.5 Verificación de las cifras

Las cifras del §6.3 y las de la tabla del §4.2 del modelo de datos se recalculan con fracciones exactas en [`verificacion/test_cifras_ciclos.py`](../verificacion/test_cifras_ciclos.py). Desde la raíz del repositorio:

```
python3 -m unittest discover -s verificacion -v
```

- **Qué comprueba.**
  - Los métodos A, B y C, la atribución «por cuenta de» (C2), el aviso de hueco de P-DIEGO y la agregación española.
  - El aviso ART54-SENS de P-CARLOS, y que el método A no cambia la relación de control del AMLR.
  - Las cifras de P-BRUNO y P-CARLOS con la lectura contraria de N9 y N13 (C29).
  - Que cada cifra redondeada aparece en el documento que la cita. Si alguien cambia una cifra sin recalcularla, la comprobación falla.
- **De dónde sale el ejemplo.** Se lee del bloque JSON del modelo de datos, así que no hay una segunda copia que pueda quedar desactualizada.
- **Es provisional.** Implementa solo lo necesario para estas cifras. Cuando exista la implementación, estas comprobaciones pasarán a ser tests de ella.
- **Lo que no cubre:** los ejemplos del §10. Son productos de dos o cuatro factores que se comprueban a mano.

---

## 7. Capital y votos

**Cómo se propagan.** Por separado, con la misma regla (C9): el capital se multiplica por capital y los votos por votos.

**Dónde se mezclan:**

| Punto | España | AMLR |
|---|---|---|
| Umbral final | En cualquiera de las dos: «del capital o de los derechos de voto» (Ley 4.2.b) | En cualquiera de las dos: «acciones, derechos de voto u otra participación» (52.1) |
| Control | Solo votos (CCom 42.1.a). No hay mezcla | Capital **o** votos (53.2.c). Hay mezcla: el control conseguido con capital transmite también los votos de la controlada (54.a) |
| Agregación | Solo votos (art. 42) | No hay regla de agregación (N8) |

**Si una cadena supera el umbral en una magnitud y no en la otra,** la persona es titular real en los dos regímenes, porque basta con una. La salida indica en qué magnitud y con qué valor. No se pondera ni se combina.

**[N6 — no resuelto]** Ningún texto dice si una misma cadena puede **mezclar** magnitudes al multiplicar. Por ejemplo, el capital en el primer tramo y los votos en el segundo. El 52.1 dice «multiplicando las acciones o los derechos de voto» sin aclararlo.

**[C21 — decisión propia]** No se mezcla al multiplicar. Como aviso se calcula el **producto mixto**: en cada arista se toma el mayor de capital y votos. Si con él alguien alcanza el umbral y no es titular real por las reglas aplicadas, la salida indica «posible titular real: mezcla de magnitudes (N6)».
- En el AMLR ese aviso casi nunca aparece, porque una arista con más del 50 % en cualquier magnitud ya es control y entra por el 54.a.
- En España sí aparece (Ej. 6).

---

## 8. Supuestos supletorios

### 8.1 España: administradores

**Base textual:**
- **Ley 4.2.b bis:** «Cuando no exista una persona física que posea o controle, directa o indirectamente, un porcentaje superior al 25 por ciento del capital o de los derechos de voto de la persona jurídica, o que por otros medios ejerza el control, directo o indirecto, de la persona jurídica, se considerará que ejerce dicho control el administrador o administradores. Cuando el administrador designado fuera una persona jurídica, se entenderá que el control es ejercido por la persona física nombrada por el administrador persona jurídica.»
- **RD 8.b, párrafo 4:** «Las presunciones a las que se refiere el párrafo anterior se aplicarán salvo prueba en contrario».

**[C22 — decisión propia]** Si nadie es titular real por E1 ni por E2:
- **Quiénes salen.** Todos los `cargos` de S con `cargo: "miembro_organo_administracion"`, sean o no ejecutivos. Si el cargo lo ocupa una entidad, sale su `representante` (modelo, D12).
- **Estado «condicional».** Siempre en v0.1, porque la Ley exige que nadie ejerza el control «por otros medios» y v0.1 no lo evalúa (D19). Además, la presunción admite prueba en contrario.
- **Estado «no determinable» en su lugar** si hay avisos de hueco (§9, H1 o H2): con parte del capital o de los votos sin identificar no se puede afirmar que «no exista» una persona por encima del umbral. La salida recuerda además la Ley 4.4, párr. 2: «no establecerán o mantendrán relaciones de negocio con personas jurídicas […] cuya estructura de propiedad y de control no haya podido determinarse».
- **Si S no tiene `cargos`,** se da el aviso AVI-07 y el estado es «no determinable».
- **Si hay avisos de lectura L3,** se mantiene el supuesto supletorio y se indica que, con la lectura extensiva, habría titulares reales.

### 8.2 AMLR: cargos de dirección de alto nivel

**Base textual:**
- **22.2, párrafo 2:** si, «una vez agotados todos los medios posibles de identificación, no se identifique a ninguna persona física como el titular real […], las entidades obligadas indicarán que no se ha identificado a ningún titular real e identificarán a todas las personas físicas que ejerzan un cargo de dirección de alto nivel».
- **63.4:** «cargos de dirección de alto nivel» son «las personas físicas que son miembros ejecutivos del órgano de dirección, así como […] las personas físicas que ejercen funciones ejecutivas en una entidad jurídica y que son responsables de la gestión cotidiana».
- **Considerando 125:** «Aunque sean identificados en esas situaciones, los cargos de dirección de alto nivel no son los titulares reales.»

**[C23 — decisión propia]** Si nadie es titular real por A1 a A4:
- **Qué sale.** «No se ha identificado titular real» y la lista de los `cargos` de S con `ejecutivo: true` ocupados por personas físicas (modelo, D12 y D22). **No se presentan como titulares reales.**
- **Cargos ejecutivos ocupados por una entidad:** se excluyen, con un aviso. El 63.4 habla solo de personas físicas y el AMLR no tiene una regla como la del representante de la Ley 4.2.b bis.
- **Estado «provisional».** Siempre en v0.1, porque no se han «agotado todos los medios»: el control por otros medios no se evalúa.
- **Estado «no determinable»** si hay avisos de hueco, como en el §8.1.

---

## 9. Contenido mínimo de la salida y avisos

**Para cada régimen, la salida contiene:**
- **Estado:**
  - `determinado`;
  - `supletorio (condicional)` en España, o `sin titular real identificado (provisional)` en el AMLR;
  - `no determinable`;
  - `exceptuada`, solo en España: S cotiza (C5) o es filial de una cotizada (C30). La salida indica cuál de las dos.
- **Titulares reales.** Cada uno con la persona, las pruebas que cumple (A1–A4 o E1–E2), la magnitud, el valor exacto y el redondeado, las cadenas que lo explican y la marca «por cuenta de» si procede.
- **Posibles titulares reales.** Personas que no lo son por las reglas aplicadas, pero sí por una lectura no resuelta, con el código correspondiente:

| Código | Condición | Norma no resuelta |
|---|---|---|
| POS-T | eff_m(P, S) alcanza el umbral del régimen (§3.5) | N1 y N2 en España; N4 y N5 en el AMLR |
| POS-AGREGADO | Con el control agregado C⁺, P cumpliría A2, A3 o A4 (§3.3). Solo AMLR | N8 |
| POS-MEZCLA | El producto mixto alcanza el umbral (§7) | N6 |
| POS-FORMAL | Con las aristas `por_cuenta_de` atribuidas al titular formal, P cumpliría A1, A2, A3 o A4 en el AMLR, o E1 en España, donde la atribución al titular formal es solo en capital (§2.2) | N9 en el AMLR; N13 en España |
| POS-HUECO | own_m(P, S) + U_m alcanza el umbral, siendo U_m lo que llega a S desde los titulares `NO_IDENTIFICADO` y `OPACA` (C4) | Estructura incompleta |

- **Avisos:**

| Código | Condición |
|---|---|
| H1 | U_m alcanza por sí solo el umbral: puede haber un titular real sin identificar |
| H2 | Se da algún POS-HUECO |
| CICLO-SENS | El método A cambia quién es titular real (§6.2). Cubre N7 y N12 |
| ART54-SENS | Un titular real lo es solo por A1 y dejaría de serlo si el 54 sustituyera al 52.1 (§4.2). Solo AMLR. Cubre N3 |
| UMBRAL-EXACTO | Leer por encima o por debajo los valores que coinciden con un umbral cambia quién es titular real (§2.6). Es un límite de los datos (modelo, D23), no de la norma |
| CICLO-CERRADO | Hay un ciclo cerrado (§6.4) |
| T-NO-CONVERGE | La lectura extensiva no se puede calcular (§3.5) |
| DOMINIO-INESTABLE | El cálculo de dominio del §3.4 no se estabiliza; E2 queda como no determinable |
| AMLR-NO-APLICABLE | La fecha de referencia es anterior al 10-07-2027 (C7) |
| COTIZADA | Lo que llega a través de cotizadas con requisitos de información en España (C5), a título informativo |
| EXENCION-SENS | S no es filial de una cotizada según C30, pero lo sería midiendo con los votos o con una cadena de mayorías directas de capital: la identificación podría no ser preceptiva (RD 9.4). Solo España. Cubre N14 |

«Alcanza el umbral» significa **> 25 en España** y **≥ 25 en el AMLR**. **[C24 — decisión propia]** Todos los avisos usan el umbral del régimen en el que se calculan.

---

## 10. Ejemplos numéricos

En todos los ejemplos, capital y votos coinciden salvo que se indique lo contrario. P, Q, R y las demás letras con número son personas físicas; A, B, C, D, H y K son sociedades.

### Ej. 1: exactamente el 25 %

S: P1, P2, P3 y P4 tienen el 25 % cada uno.

| | AMLR | España |
|---|---|---|
| P1 a P4 | Titulares reales por A1: 25 ≥ 25 | No: 25 no es > 25 (E1) y va = 25 no es > 25 (E2) |
| Estado | `determinado`: cuatro titulares reales | `supletorio (condicional)`: los administradores de S (4.2.b bis) |
| UMBRAL-EXACTO (C28) | Sí: leídos justo por debajo del 25, nadie sería titular real | Sí: leídos justo por encima, P1 a P4 serían titulares reales |

### Ej. 2: control arriba, participación abajo (54.a)

S: H 30 %, X 70 %. H: P 60 %, Q 40 %.

| Lectura | P | Q | X |
|---|---|---|---|
| AMLR, A1 (52.1) | 18 % → no | 12 % → no | 70 % → sí |
| AMLR, A3 (54.a) | Controla H, que tiene 30 % ≥ 25 → **sí** | No controla H | — |
| España, L1 | 18 % → no | 12 % → no | 70 % → sí |
| España, L2 | Domina H → va = 30 > 25 → **sí** | 0 → no | sí |
| **Titulares reales** | **AMLR: sí · España: sí (solo por L2)** | No | Sí |

Variante con acumulación: P controla A1 y A2 (60 % de cada una), que tienen cada una el 15 % de S.
- **AMLR, 54.a:** 15 + 15 = 30 ≥ 25 → **sí**.
- **España, L2:** 30 > 25 → **sí**.
- **España, L1:** 9 + 9 = 18 → no.

Con la lectura «L1 sola», que se descarta en C19, P no sería titular real en España.

### Ej. 3: participación arriba, control abajo (54.b)

S: C 60 %, R 40 %. C: P 30 %, Q 70 %.

| | P | Q | R |
|---|---|---|---|
| AMLR | **Sí**, por A4: C controla S y own(P, C) = 30 ≥ 25. Por A1 no (18 %) | Sí, por A1 (42 %) y A2 (controla C, que controla S) | Sí (40 %) |
| España, L1 ∪ L2 | **No**: L1 = 18; L2 = 0, porque no domina C | Sí: L1 = 42; L2 = 60, controla S | Sí (40 %) |
| España, L3 | 0,3 × 1 = 30 > 25 → **POS-T** | — | — |

**Diferencia entre regímenes:** P es titular real en el AMLR y en España solo figura como posible (lectura extensiva, N1/N2).

### Ej. 4: mayoría de capital sin mayoría de votos

S: A 30 %, R 70 %. A: P tiene 60 % del capital y 40 % de los votos; Q tiene 40 % del capital y 60 % de los votos.

| | P | Q | R |
|---|---|---|---|
| AMLR | **Sí**, por A3: controla A por capital (60 > 50, según 53.2.c) y A tiene 30 ≥ 25 | Sí, por A3: controla A por votos (60 > 50) | Sí |
| España | **No**: L1 da 18 de capital y 12 de votos; L2, 0, porque con 40 % de votos no domina A | Sí, por L2: domina A → va = 30 | Sí |

**Diferencias:**
- en el AMLR dos personas controlan A a la vez (N11). No hay aviso (§12);
- el art. 42 solo reconoce el control por votos.

### Ej. 5: varios tramos de control (N4)

P —60 %→ A —50 %→ B —60 %→ C —50 %→ S. Los demás titulares: A2 tiene el 40 % de A, B2 el 50 % de B, C2 el 40 % de C y S2 el 50 % de S.

| | P | S2 |
|---|---|---|
| AMLR literal (A1–A4) | No: 52.1 da 9 %; ni 54.a ni 54.b se aplican (§4.4) | Sí (50 %) |
| AMLR, lectura extensiva | 1 × 0,5 × 1 × 0,5 = 25 ≥ 25 → **POS-T** | — |
| España (L1, L2 y L3) | L1 = 9; L2 = 0, porque A no domina B con 50 %; L3 = 25, que no es > 25 → **ni titular ni aviso** | Sí (50 %) |

**UMBRAL-EXACTO (C28), en los dos regímenes.** Las aristas del 50 % (A→B, B2→B, C→S y S2→S), leídas justo por encima, darían control. Con eso, en el AMLR también serían titulares reales P, A2, B2 y C2, y en España, P y B2.

### Ej. 5b: el 54 como sustitución o como suma (N3)

P y A2 tienen el 50 % de A cada uno. A tiene el 100 % de D. D tiene el 50 % de S y S2 el otro 50 %.

| | P (y A2, simétrico) | S2 |
|---|---|---|
| AMLR con unión de pruebas (C14) | **Sí**, por A1: 0,5 × 1 × 0,5 = 25 ≥ 25. Aviso **ART54-SENS**: la única cadena tiene un tramo de control (A→D) y sin ella queda 0 | Sí |
| AMLR si el 54 sustituye al 52.1 | **No**: la cadena mezcla control (A→D) y participación, así que solo valdría el 54; y P no controla A (50 %) ni D controla S (50 %) | Sí |
| España | No: 25 no es > 25 | Sí |

**UMBRAL-EXACTO (C28), en los dos regímenes.** En el AMLR, leyendo el 25 justo por debajo, P y A2 dejarían de ser titulares reales. En España, leyéndolo justo por encima, lo serían.

### Ej. 6: mezcla de magnitudes (N6)

A: P tiene 60 % del capital y 10 % de los votos; Q, 40 % del capital y 90 % de los votos. S: A tiene 10 % del capital y 45 % de los votos; R, 90 % del capital y 55 % de los votos.

| | P | Q | R |
|---|---|---|---|
| AMLR | **Sí**, por A3: controla A por capital, y A tiene 45 % de votos en S ≥ 25 | Sí, por A3 (controla A por votos) | Sí |
| España | **No**: L1 da 6 de capital y 4,5 de votos; L2, 0. Producto mixto: 0,6 × 0,45 = 27 > 25 → **POS-MEZCLA** | Sí, por L2 (va = 45) | Sí |

### Ej. 7: el ejemplo del modelo de datos

Ver §6.3. Los dos regímenes identifican a P-ANA y P-CARLOS. P-DIEGO lleva aviso de hueco (POS-HUECO). El resultado no depende del método de ciclos. En el AMLR, P-CARLOS lleva ART54-SENS (N3). En España, P-ANA además controla E-OBJETIVO.

### Ej. 8: filiales de cotizadas (C30, N14)

L es una sociedad con `cotizacion` y `requisitos_informacion_ue_o_equivalentes: true`, sin titulares en la entrada.

**Ej. 8a: S es filial.** S: L 60 %, P 40 %.

| | AMLR | España |
|---|---|---|
| S | Se calcula: la cotización no cambia nada | own_capital(L, S) = 60 > 50: S es filial de L → **exceptuada** (RD 9.4) |
| P | Titular real por A1 (40 %) | No se calcula |
| Avisos | H1: lo que llega a través de L (60 %) va a `NO_IDENTIFICADO(L)` | — |

Variante: si L tuviera el 40 % del capital y el 60 % de los votos, S no sería filial según C30 y se calcularía: P sería titular real (60 % del capital). Midiendo con los votos sí sería filial, así que la salida daría **EXENCION-SENS**.

**Ej. 8b: la filial es una intermedia.** X: L 51 %, P 49 %. S: X 70 %, R 30 %.

| | AMLR | España |
|---|---|---|
| S | Se calcula | own_capital(L, S) = 0,51 × 70 = 35,7: S no es filial. X sí lo es, pero es intermedia y se recorre (C30) |
| P | Titular real por A1 (0,49 × 70 = 34,3 %) y A4 (X controla S y P tiene el 49 % de X) | **Titular real** por E1 (34,3 %) |
| R | Titular real (30 %) | Titular real (30 %) |
| L | Su 35,7 % en S va a `NO_IDENTIFICADO(L)`: aviso H1 | Su 35,7 % va a `COTIZADA(L)`, sin aviso de hueco |
| Avisos | H1 | **EXENCION-SENS**: con una cadena de mayorías directas (51 % de X, 70 % de S), S sería filial de L |

Si la exención se aplicara también a la filial intermedia, los socios de X no se recorrerían y P, con el 34,3 % de S, quedaría sin identificar en España.

### Resumen de diferencias

| Ej. | AMLR | España | Por qué difieren |
|---|---|---|---|
| 1 | P1 a P4 | Supletorio: administradores | Umbral ≥ 25 frente a > 25 |
| 2 | P, X | P, X | No difieren, pero en España P solo sale por L2 |
| 3 | P, Q, R | Q, R (P posible) | El 54.b no tiene equivalente en L1 ∪ L2 |
| 4 | P, Q, R | Q, R | Control por capital (53.2.c) frente a solo votos (CCom 42.1.a) |
| 5 | S2 (P posible) | S2 | Forma no regulada: vale 25 exacto, que en el AMLR alcanza el umbral |
| 5b | P, A2, S2 | S2 | Umbral y lectura del «salvo» del 52.1 |
| 6 | P, Q, R | Q, R (P posible) | Control por capital y mezcla de magnitudes |
| 7 | Ana, Carlos | Ana, Carlos | Solo difiere el criterio: en España Ana controla S |
| 8a | P | Exceptuada | La exención del RD 9.4 no tiene equivalente en el AMLR |
| 8b | P, R | P, R | No difieren en titulares: lo que llega a través de L es un hueco en el AMLR y va a `COTIZADA(L)` en España |

---

## 11. Decisiones propias

| # | Decisión | Sección | Alternativa descartada | Motivo |
|---|---|---|---|---|
| C1 | Solo se calcula sobre los nodos con camino hasta S | §2.1 | Calcular sobre todo el grafo | Los nodos sin camino no pueden aportar nada a S; es coherente con D21 |
| C2 | La arista `por_cuenta_de` se atribuye al principal en todos los cálculos; el titular formal no recibe nada | §2.2 | (a) Atribuirla al titular formal. (b) En el AMLR, tratarla solo como control por otros medios (53.4.c), fuera de v0.1 | (a) Da falsos positivos y negativos. (b) Dejaría sin atribuir una participación conocida. El CCom 42 y la Dir. 22.3–22.4 la atribuyen al principal |
| C3 | Las aristas paralelas del mismo titular, tras C2, se suman | §2.3 | Tratarlas por separado | Sumarlas es lo que hace el CCom 42.1: «se añadirán» |
| C4 | Los huecos son titulares virtuales que se propagan | §2.4 | Ignorar los huecos | Ignorarlos haría que la regla de los administradores (4.2.b bis) se aplicara sin tener en cuenta a quien puede estar en el hueco |
| C5 | España: S cotizada con requisitos de información se exceptúa, y las intermedias en ese caso no se recorren; sin esos requisitos, se tratan como cualquier otra entidad. AMLR: la cotización no cambia el cálculo | §2.5 | (a) Aplicar el 65.a del AMLR como excepción. (b) Que baste con cotizar en las intermedias (versión anterior) | (a) El 65.a exime de obligaciones (arts. 63 y 64), no de la definición (51–55). (b) El RD 9.4 condiciona la excepción a las obligaciones de información; bastar con cotizar las daría por cumplidas, contra D13 |
| C6 | Aritmética con fracciones exactas; solo se redondea al mostrar | §2.6 | Coma flotante binaria | Los umbrales > 25 y ≥ 25 se deciden en el valor exacto |
| C7 | El AMLR se calcula aunque la fecha sea anterior a 2027-07-10, con aviso | §2.7 | No calcularlo | Comparar los dos regímenes es el objetivo del proyecto |
| C8 | own_m se calcula resolviendo un sistema lineal (serie completa), con el titular como origen | §3.1 | Enumerar cadenas | Con ciclos hay infinitas cadenas; el sistema da su suma exacta |
| C9 | Capital y votos se propagan por separado | §3.1 | Mezclarlos al multiplicar | Ningún texto lo autoriza (N6); la mezcla solo se usa para avisar (C21) |
| C10 | Hay control si se supera el 50: en el AMLR en cualquier magnitud, en España solo en votos | §3.2 | ≥ 50 | «50 % más una» y «mayoría» exigen más de la mitad |
| C11 | Control en el AMLR = cierre transitivo de own > 50 | §3.3 | Solo control directo en cada nivel | El 53.2.c incluye la «propiedad directa o indirecta» del 50 % más una |
| C12 | Dominio en España: art. 42.1.a aplicado a personas físicas, con agregación y base de la Dir. 22.5; los votos neutralizados no cuentan en los agregados; rondas hasta estabilizarse, con aviso si no lo hace | §3.4 | Solo votos directos, sin agregación | La Ley remite al art. 42 y a la Dir. 22 (1 a 5), y el art. 42 manda agregar |
| C13 | La lectura extensiva (transparencia del control) solo genera avisos | §3.5 | Contarla como titularidad real | No tiene apoyo literal fuera de las formas del art. 54 |
| C14 | En el AMLR se unen las pruebas 52.1, 51.b, 54.a y 54.b | §4.2 | El 54 sustituye al 52.1 en las cadenas mixtas | Considerandos 106 y 108; la sustitución deja fuera a quien llega al 25 % por multiplicación (Ej. 5b) |
| C15 | 54.a: se suman solo las entidades controladas, no la participación directa propia | §4.3 | Sumar también la directa | El texto dice «entidades jurídicas titulares»; el caso mixto se avisa (N5) |
| C16 | 54.b: own(P, K) según el 52.1 | §4.3 | Exigir participación directa en K | El texto dice «directa o indirectamente» |
| C17 | España, «posean»: multiplicación (L1) | §5.3 | Solo participaciones directas (L0) | La Ley dice «directa o indirectamente»; la multiplicación es la única que atribuye una parte proporcional sin exigir control |
| C18 | España: el umbral de L2 se mide sobre la base ajustada por la Dir. 22.5 | §5.3 | Medirlo sobre 100 | Usar la misma medida para el dominio y para el umbral |
| C19 | España: la lectura aplicada es L1 ∪ L2; L3 solo avisa | §5.3 | (a) L1 sola. (b) L3 | (a) Ignora la remisión al art. 42 para el control. (b) Solo tiene apoyo en el AMLR |
| C20 | Ciclos: método B para multiplicar, C para agregar votos, A como prueba de sensibilidad, también para el control del AMLR | §6.2 | Rechazar las entradas con ciclos, o usar solo el método A | B suma todas las cadenas y reparte el 100 %; C es un texto al que la Ley remite; A pierde parte de la participación |
| C21 | No se mezclan magnitudes al multiplicar; el producto mixto solo avisa | §7 | Usar el producto mixto como regla | N6: ningún texto lo autoriza |
| C22 | Supletorio en España: administradores, siempre condicional; no determinable si hay huecos | §8.1 | Aplicarlo sin condiciones | v0.1 no evalúa el control por otros medios, y la Ley exige que «no exista» nadie por encima del umbral |
| C23 | Supletorio en el AMLR: cargos ejecutivos que sean personas físicas, siempre provisional; nunca como titulares reales | §8.2 | Presentarlos como titulares reales | Considerando 125 |
| C24 | Los avisos usan el umbral del régimen en el que se calculan | §9 | Un umbral único | Evitar avisos que el propio régimen no reconocería |
| C25 | Un caso N se señala en la salida cuando otra lectura se puede calcular con la entrada y cambiaría quién es titular real. N10 y N11 solo se documentan | §0 | Un aviso por cada caso N | Un aviso que no compara con nada no dice nada del caso concreto: o salta siempre, o compara con una regla que no está en ningún texto (§12) |
| C26 | AMLR: control agregado C⁺ (C11 más la suma de lo que tienen X y sus controladas), solo para avisar (POS-AGREGADO) | §3.3 | Contar C⁺ como control | N8: el AMLR no lo dice; en v0.1 no se considera control |
| C27 | AMLR: se comprueba si el titular lo sería sin las cadenas con tramos de control (own^O); si no, aviso ART54-SENS | §4.2 | No avisar, porque C14 ya es la lectura más amplia | La lectura contraria quita titulares, y quien lo es solo por C14 debe saberse |
| C28 | Un valor igual a un umbral se toma como exacto; se repite el cálculo leyéndolo justo por encima y justo por debajo, y si cambia quién es titular real, aviso UMBRAL-EXACTO | §2.6 | (a) Avisar siempre que un valor coincida con un umbral. (b) Declarar «no determinable» | (a) Saltaría en cualquier sociedad al 50/50 aunque no cambie nada. (b) Casi siempre un 50 registrado es la mitad justa; el límite solo aparece a partir de cientos de miles de acciones (modelo, D23) |
| C29 | Se repite el cálculo con las aristas `por_cuenta_de` en su titular formal: en el AMLR, en las dos magnitudes; en España, solo en capital. Si alguien pasa a cumplir alguna prueba, POS-FORMAL | §2.2 | (a) Dejar N9 y N13 señalados solo con la marca «por cuenta de». (b) En España, atribuir también los votos al titular formal | (a) La marca solo sale en el principal; no avisa si con la otra lectura el titular formal sería titular real. (b) Para los votos hay texto: CCom 42.1 y Dir. 22.4.a |
| C30 | España: S es «exceptuada» si es filial participada mayoritariamente de una cotizada con requisitos de información: own_capital(L, S) > 50, por cada cotizada. No se aplica a las filiales intermedias. EXENCION-SENS si otra lectura la haría filial | §2.5 | (a) Medir con los votos, o con capital o votos. (b) Cadena de mayorías directas. (c) Aplicarlo también a las filiales intermedias | El RD 9.4 dispensa, no prohíbe: una lectura estrecha como mucho identifica de más, y una amplia puede dejar sin identificar a un titular real. (a) «Participada» habla de participación, no de control. (b) El 60 % del 60 % no es una participación mayoritaria. (c) Dejaría sin recorrer a los socios minoritarios de la filial, que la transparencia de la cotizada no cubre (Ej. 8b) |

## 12. Casos que la norma no resuelve

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
| N10 | España: qué es «mayoría» en el CCom 42.1.a | §3.2 | C10 (> 50) | Ninguna propia (ver abajo) |
| N11 | AMLR: dos personas que controlan a la vez, una por capital y otra por votos (53.2.c) | §3.3, Ej. 4 | Se acepta tal como sale del texto | Ninguna (ver abajo) |
| N12 | AMLR: si la autocartera se descuenta al decidir el control | §6.2 | La serie completa la descuenta de hecho; ninguna norma del AMLR lo dice | CICLO-SENS: el método A no la descuenta (§6.2) |
| N13 | España: a quién se atribuye el capital de una participación por cuenta de otro | §2.2, §6.3 | C2 (al principal) | Marca «por cuenta de» y POS-FORMAL (C29) |
| N14 | España: cómo se mide la «filial participada mayoritariamente» del RD 9.4 | §2.5, Ej. 8 | C30 (más del 50 % del capital, multiplicando) | EXENCION-SENS (C30) |

**Por qué N10 y N11 no tienen señal.** En los dos casos no hay otra lectura con la que comparar la entrada (C25).
- **N10.** La única alternativa a «> 50» sería «≥ 50», y el 50 % no es mayoría: con esa lectura, dos socios al 50 % dominarían a la vez la misma sociedad (C10).
  - Con porcentajes a 4 decimales, a partir de cierto número de acciones un 50 registrado no distingue la mitad justa de la mitad más una. Eso no es un caso de la norma, sino un límite de los datos. Afecta igual al «50 % más una» del AMLR y a los umbrales del 25.
  - Está documentado en el modelo (D23), y la salida lo señala con UMBRAL-EXACTO (C28). En la práctica, ese aviso también calcula la lectura «≥ 50», pero por el dato y no por la norma.
- **N11.** El texto sí da el resultado: con «acciones o los derechos de voto» (53.2.c), las dos personas controlan. Lo único que falta es que el AMLR comente esa consecuencia.
  - El 53.2.a define el control en general como poder «imponer decisiones pertinentes», pero el 53.2.c no condiciona a eso el control a través de participación.
  - Una regla que eligiera a una de las dos personas (que prevalezcan los votos, o el capital) no está en ningún texto. Comparar con ella sería inventar la alternativa.
