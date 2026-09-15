# Modelo de datos de entrada — v0.1

Estado: borrador. Fecha: 2026-09-15. Sin código.

Este documento define el JSON con el que se describe una estructura de propiedad para calcular la titularidad real de una entidad jurídica. Define solo la **entrada**: no fija cómo se calcula ni el formato de salida.

## 0. Convenciones

- Las citas literales van entre comillas «…» con artículo, apartado y letra.
- Todo lo que no viene de los textos y es elección de diseño va marcado como **[Dn — decisión propia]** y se recoge en la tabla del §8, junto con la alternativa descartada y el motivo.
  - Los números (D1–D23) son identificadores estables: no siguen el orden de aparición y no se reutilizan.
- Lo que los textos no resuelven y queda para la especificación del cálculo va marcado como **[Pendiente]** y se recoge en el §9.

### Fuentes (en `docs/fuentes/`)

| Documento | Fecha que declara |
|---|---|
| Ley 10/2010 (BOE-A-2010-6737, consolidado) | «Última modificación: 21 de marzo de 2026» |
| RD 304/2014 (BOE-A-2014-4742, consolidado) | «Última modificación: 24 de abril de 2024» |
| RD 609/2023 (BOE-A-2023-16159, consolidado) | «Última modificación: sin modificaciones» |
| Código de Comercio (BOE-A-1885-6627, consolidado) | «Última modificación: 09 de mayo de 2023» |
| Directiva 2013/34/UE (CELEX 02013L0034, consolidado) | «02013L0034 — ES — 28.05.2024 — 006.003» |
| Reglamento (UE) 2024/1624, AMLR (DO L de 19.6.2024) | Sin consolidar. Art. 90: «Será aplicable a partir del 10 de julio de 2027» |

---

## 1. Principios del modelo

1. **La entrada recoge hechos, no conclusiones.** **[D1 — decisión propia]** El JSON dice quién tiene qué porcentaje de qué entidad, quién ocupa qué cargo y por cuenta de quién se tiene una participación. No lleva campos como «es titular real», «controla» o «criterio». Todo eso lo deduce el cálculo, y depende del régimen.
2. **El régimen no forma parte de la entrada.** **[D2 — decisión propia]** La misma estructura debe poder calcularse con la Ley 10/2010 y con el AMLR, porque la comparación entre ambos es el objetivo del proyecto. El régimen es un parámetro del cálculo.
3. **Las dos magnitudes se registran siempre por separado.** La Ley habla de «un porcentaje superior al 25 por ciento del capital o de los derechos de voto» (Ley 10/2010, art. 4.2.b; RD 304/2014, art. 8.b). El AMLR, de «acciones, derechos de voto u otra participación en la propiedad» (art. 52.1). En ambos casos basta con una. Capital y votos pueden no coincidir (p. ej., participaciones sin voto), así que no se deduce una de la otra.
4. **Lo que v0.1 no puede representar, se dice.** Ver §7.

---

## 2. Qué datos exige el cálculo en cada régimen

### 2.1 Tabla comparativa

| Dato | España (Ley 10/2010, RD 304/2014, remisiones) | AMLR | En el modelo v0.1 |
|---|---|---|---|
| % de capital | Ley 4.2.b: «del capital» | 52.1: «acciones […] u otra participación en la propiedad» | `capital` en cada arista |
| % de derechos de voto | Ley 4.2.b: «de los derechos de voto» | 52.1: «derechos de voto» | `votos` en cada arista |
| Derechos económicos (beneficios, liquidación) | No se mencionan | 52.1: «incluidos los derechos de participación en los beneficios u otros recursos internos o saldo de liquidación» | **No representable** (§7) |
| Cadenas y entidades interpuestas | Ley 4 bis.4.h: «información sobre las personas jurídicas interpuestas y su participación en cada una de ellas». Igual en RD 609/2023, art. 4.1.i | 62.1.d: descripción de la estructura, «que incluya la proporción del interés que se tiene» | Nodos `entidad_juridica` y aristas |
| Control en cada nivel intermedio | Sin regla expresa | 53.2.c: «50 % más una»; art. 54: cadenas mixtas | Se deduce de las aristas |
| Participación por cuenta de otro | CCom 42.1, último párrafo; Dir. 22.3 y 22.4.a | 53.4.c (nominatarios) y art. 66 | `por_cuenta_de` en la arista (§5) |
| Control por otros medios (acuerdos, estatutos, derecho a nombrar administradores) | Ley 4.2.b; RD 8.b; CCom 42.1.b–d; Dir. 22.1.b–d | 53.3 y 53.4.a | **No representable** (§7) |
| Actuación concertada | CCom 42.1, último párrafo: «concertadamente con cualquier otra persona» | 53.3.a: «personas que actúen de manera concertada» | **No representable** (§7) |
| Relaciones familiares | No se mencionan | 53.4.b: «relaciones entre familiares» | **No representable** (§7) |
| Tipo de entidad | RD 8: reglas distintas para 8.c (entidades que administran fondos) y para fundaciones y asociaciones | 52.4: entidades que no son sociedades; arts. 55 y 57 | `clase` en el nodo |
| Cotización en mercado regulado | Ley 4.2.b, párr. 3: «Se exceptúan las sociedades que coticen en un mercado regulado y que estén sujetas a requisitos de información acordes con el Derecho de la Unión o a normas internacionales equivalentes»; RD 9.4 | 65.a: excepción a los arts. 63 y 64 con tres condiciones | `cotizacion` en el nodo |
| Administradores de la entidad (supletorio) | Ley 4.2.b bis; RD 8.b, párr. 3; RD 609/2023, art. 4.1, párr. final. Si el administrador es persona jurídica, cuenta «la persona física nombrada por el administrador persona jurídica» | — | `cargos` en la entidad objetivo |
| Cargos de dirección de alto nivel (supletorio) | — | 22.2 y 63.4: «miembros ejecutivos del órgano de dirección, así como […] las personas físicas que ejercen funciones ejecutivas […] y que son responsables de la gestión cotidiana» | `cargos` con el indicador `ejecutivo` |
| Autocartera y votos de sus filiales | Solo por la remisión a la Dir. 22.5 | — | Arista reflexiva y ciclos (§4) |
| Identificación de la persona física | Ley 4 bis.4.a–g; RD 609/2023, art. 4.1.a–j | 62.1.a: añade lugar de nacimiento, domicilio y número de identificación personal único | `identificacion`, opcional y sin validar en v0.1 |
| Identificación de la entidad | RD 609/2023, art. 4.3: razón social, EUID, NIF o número de registro, forma jurídica, nacionalidad, domicilio social | 62.1.d: nombres y números de identificación de las entidades de la estructura | Atributos del nodo |
| Fecha desde la que se tiene el interés | No aparece en la lista del art. 4 bis.4 | 62.1.b: «la fecha a partir de la cual se tiene dicho interés real» | `desde` en la arista, opcional |

### 2.2 Qué pide un régimen y no el otro

**Pide el AMLR y no el régimen español:**
- **Derechos económicos** como tercera magnitud (52.1).
- **Relaciones familiares** (53.4.b).
- **Nominatarios** con definición propia (53.4.c) y obligación de revelar al nominador (art. 66).
- **Umbral de control del 50 % más una en cada nivel** (53.2.c). Hace falta para aplicar el art. 54. Se deduce de los mismos datos, no exige datos nuevos, salvo en el límite de precisión de D23.
- **Distinguir cargos ejecutivos de no ejecutivos** para el supuesto supletorio (63.4).
- **Fecha de inicio del interés** (62.1.b), lugar de nacimiento, domicilio y número de identificación personal (62.1.a).

**Pide el régimen español y no el AMLR:**
- **La persona física que representa al administrador persona jurídica** (Ley 4.2.b bis). En los arts. 22 y 63 del AMLR no aparece una regla equivalente.
- **País de expedición del documento** (Ley 4 bis.4.d) y **correo electrónico** (RD 609/2023, art. 4.1.j).
- **«Capital»** como magnitud. El AMLR dice «acciones». Si todas las acciones tienen el mismo nominal y derechos proporcionales, las dos cosas coinciden; si no, pueden diferir.
  - **[D7 — decisión propia]** En v0.1, `capital` es el porcentaje del capital social y se usa también como magnitud de «acciones u otra participación en la propiedad» en el AMLR. Esa equivalencia es exacta solo en el caso proporcional.

---

## 3. Esquema

Tras la tabla de cada objeto se indica de dónde sale cada campo. Se usará un JSON Schema formal cuando haya código.

### 3.1 Documento raíz

| Campo | Tipo | Oblig. | Significado |
|---|---|---|---|
| `version_modelo` | string | sí | `"0.1"` |
| `fecha_referencia` | fecha ISO 8601 (`AAAA-MM-DD`) | sí | Fecha a la que se refiere la foto de la estructura |
| `entidad_objetivo` | string (id de nodo) | sí | Entidad cuya titularidad real se calcula |
| `nodos` | array de nodos | sí | Personas físicas y entidades jurídicas |
| `participaciones` | array de aristas | sí | Puede estar vacío |

- **[D3 — decisión propia]** `fecha_referencia` es obligatoria por dos motivos.
  - Los regímenes se aplican en fechas distintas (AMLR, art. 90).
  - Obliga a que todos los datos se refieran al mismo momento. Mezclar fechas es una causa habitual de sumas que superan el 100 % (§6).

### 3.2 Nodo `persona_fisica`

| Campo | Tipo | Oblig. | Significado |
|---|---|---|---|
| `id` | string | sí | Único entre todos los nodos |
| `tipo` | `"persona_fisica"` | sí | |
| `nombre` | string | sí | Nombre y apellidos |
| `identificacion` | objeto | no | `fecha_nacimiento`, `lugar_nacimiento`, `documento` {`tipo`, `numero`, `pais_expedicion`}, `pais_residencia`, `nacionalidades` [ ], `domicilio`, `email` |

**[D18 — decisión propia]** `identificacion` recoge la unión de lo que piden la Ley 4 bis.4.a–f, el RD 609/2023 (art. 4.1) y el AMLR (62.1.a). En v0.1 solo se comprueban los tipos de dato: al cálculo no le hacen falta, y a la salida sí.

### 3.3 Nodo `entidad_juridica`

| Campo | Tipo | Oblig. | Significado |
|---|---|---|---|
| `id` | string | sí | Único entre todos los nodos |
| `tipo` | `"entidad_juridica"` | sí | |
| `denominacion` | string | sí | Razón social (RD 609/2023, art. 4.3) |
| `clase` | `"sociedad"` \| `"fundacion"` \| `"asociacion"` \| `"otra"` | sí | Ver D8 |
| `forma_juridica` | string | no | Texto libre (RD 609/2023, art. 4.3) |
| `pais` | ISO 3166-1 alfa-2 | no | Nacionalidad (RD 609/2023, art. 4.3) |
| `nif`, `euid` | string | no | Identificadores (RD 609/2023, art. 4.3) |
| `cotizacion` | objeto o ausente | no | `{ "mercado": string, "requisitos_informacion_ue_o_equivalentes": boolean }` |
| `cargos` | array | no | Solo se usa en la entidad objetivo (§3.5) |

- **[D8 — decisión propia]** `clase` existe porque ambos regímenes tratan distinto a las entidades que no son sociedades:
  - RD 8, párrafos sobre fundaciones y asociaciones: «25 por ciento o más de los derechos de voto del Patronato».
  - AMLR 52.4: entidades en las que «no sea adecuado o posible calcular la propiedad».
  - v0.1 solo calcula a través de nodos de clase `sociedad`. Cualquier otra clase en la cadena genera un aviso de «fuera de alcance».
- **[D13 — decisión propia]** `cotizacion` separa dos cosas que la Ley 4.2.b, párr. 3 exige juntas: que la sociedad cotice en un mercado regulado y que esté sujeta a requisitos de información acordes con el Derecho de la Unión o equivalentes. La segunda es una valoración y la tiene que afirmar quien prepara la entrada.
  - Las condiciones del AMLR 65.a no se piden aquí. La ii) («ninguna otra entidad o instrumento jurídicos formen parte de la estructura») se puede deducir del grafo. La i) es una valoración de control y queda fuera de v0.1.

### 3.4 Arista (elemento de `participaciones`)

| Campo | Tipo | Oblig. | Significado |
|---|---|---|---|
| `id` | string | sí | Único entre todas las aristas |
| `titular` | id de nodo | sí | Quien figura como titular formal |
| `participada` | id de nodo `entidad_juridica` | sí | |
| `capital` | número en [0, 100] o `null` | sí | % del capital social de `participada` |
| `votos` | número en [0, 100] o `null` | sí | % del total de derechos de voto de `participada`, sin descontar la autocartera |
| `por_cuenta_de` | id de nodo o `null` | no | Por cuenta de quién se tiene la participación (§5) |
| `desde` | fecha ISO 8601 | no | Desde cuándo (AMLR 62.1.b) |
| `fuente` | string | no | De dónde sale el dato |

- **[D4 — decisión propia] Formato de los porcentajes.** Van en escala 0–100, como en los textos («25 por ciento», «25 %»), con un máximo de 4 decimales. Deben leerse como **decimales exactos, no como números en coma flotante binaria**.
  - Motivo: la diferencia entre «superior al 25» (Ley 4.2.b) y «25 % o más» (AMLR 52.1) se decide justo en el 25. Un error de redondeo binario en ese punto cambiaría quién es titular real.
- **[D23 — decisión propia] Límite de precisión en los umbrales.** Un porcentaje con 4 decimales representa cualquier valor real que, redondeado, dé ese número: como mucho 0,00005 por encima o por debajo (D15). Eso solo importa cuando el valor registrado es exactamente un umbral (25 o 50), porque entonces no se sabe de qué lado está el real. No es un caso que la norma deje abierto: «50 % más una» y «mayoría» son claros. El límite está en la representación.
  - **El «50 % más una» del AMLR 53.2.c.** La mayoría mínima es la primera cantidad de acciones que supera la mitad: así lee la especificación el «50 % más una» (C10).
    - Con N acciones, la mayoría mínima está a 50/N puntos del 50 si N es impar y a 100/N si es par.
    - Cuando esa distancia es menor que 0,00005, se registra como 50 y no se distingue de la mitad justa. Con N impar, a partir de 1.000.001 acciones. Con N par, a partir de 2.000.002.
    - Con exactamente 2.000.000 de acciones, la distancia es justo 0,00005 y depende de cómo se redondee el empate.
    - Vale lo mismo para los votos, con N = número de votos, y para la «mayoría» de los derechos de voto del CCom 42.1.a.
  - **Los umbrales del 25.** Pasa lo mismo, y con sociedades más pequeñas, porque el 25 % de N acciones pocas veces es entero. La cantidad más próxima al 25 está a 25/N, 50/N, 75/N o 100/N puntos, según el resto de dividir N entre 4. Por eso ocurre con algunos tamaños a partir de 500.001 acciones, y con todos por encima de 2.000.000 (con 2.000.000 exactas hay empate):
    - «superior al 25» (Ley 4.2.b): la participación mínima por encima del 25 % se registra como 25 y no alcanza el umbral. El primer tamaño afectado es 500.003;
    - «25 % o más» (AMLR 52.1): la participación máxima por debajo del 25 % se registra como 25 y lo alcanza. El primer tamaño afectado es 500.001.
  - **Qué hace el cálculo.**
    - Lee el valor registrado como exacto (D4; especificación, C6). Un 50 es la mitad justa y no da control; un 25 es el 25 justo.
    - La entrada no tiene el número de acciones, así que el cálculo no puede saber si ese valor esconde el otro lado. Por eso repite el cálculo leyendo los valores que coinciden con un umbral como si estuvieran justo por encima, y otra vez como si estuvieran justo por debajo.
    - Si en alguna de las dos repeticiones cambia quién es titular real, la salida da el aviso UMBRAL-EXACTO (especificación, C28).
  - **Lo que no cubre.** Solo el valor que coincide exactamente con el umbral. Un valor que se calcula con varias aristas acumula el error de cada una (en una suma de *n* aristas, hasta *n* × 0,00005). Por eso puede estar en realidad al otro lado del umbral aunque no dé exactamente el umbral. v0.1 no calcula esa banda.
  - Las cifras de este punto se comprueban en [`verificacion/test_precision_umbrales.py`](../verificacion/test_precision_umbrales.py).
- **[D5 — decisión propia] Las dos claves son obligatorias.** `null` significa «desconocido».
  - No se deduce `votos` a partir de `capital` ni al revés: presumir que coinciden ocultaría, por ejemplo, las participaciones sin voto.
  - Una arista con las dos a `null` es un error. Una con una sola a `null` genera un aviso.
- **[D6 — decisión propia] Los votos se registran en bruto.** `votos` es el porcentaje sobre el total de votos sin descontar la autocartera. Los ajustes que dependen del régimen (Dir. 22.5, §4) los hace el cálculo.
- **[D16 — decisión propia]** `id` es obligatorio para que el cálculo pueda explicar cada resultado indicando la cadena de aristas.
- **[D17 — decisión propia]** `fuente` es opcional y sirve para la trazabilidad que piden los textos:
  - RD 8.b, párr. 2: «El sujeto obligado deberá documentar las acciones que ha realizado»;
  - Ley 4.2.b bis: «consignarán las medidas tomadas».

### 3.5 Cargo (elemento de `cargos`)

| Campo | Tipo | Oblig. | Significado |
|---|---|---|---|
| `persona` | id de nodo | sí | Persona física o jurídica que ocupa el cargo |
| `cargo` | `"miembro_organo_administracion"` \| `"directivo"` | sí | |
| `ejecutivo` | boolean | sí | Si ejerce funciones ejecutivas (AMLR 63.4) |
| `representante` | id de nodo `persona_fisica` | si `persona` es una entidad jurídica | Ley 4.2.b bis: «la persona física nombrada por el administrador persona jurídica» |

**[D12 — decisión propia]** Una sola lista de cargos sirve para los dos supuestos supletorios:
- **España:** todos los `miembro_organo_administracion`, sean o no ejecutivos, ya que la Ley dice «el administrador o administradores» sin distinguir. Si el cargo lo ocupa una persona jurídica, cuenta su `representante`.
- **AMLR:** los `miembro_organo_administracion` con `ejecutivo: true` y los `directivo` con `ejecutivo: true`.

**[D22 — decisión propia]** Para aplicar el AMLR, se trata el «órgano de administración» español como el «órgano de dirección» del art. 63.4.
- Es un supuesto: los textos no establecen esa equivalencia.
- Los propios textos europeos distinguen ambos órganos. El AMLR 53.3.b habla del «consejo de administración o del órgano de administración, de dirección o de control», y la Dir. 22.1.b, del «órgano de administración, de dirección o de supervisión».
- Si una entidad tiene órganos separados, el supuesto puede no valer.

---

## 4. Ciclos de participación

### 4.1 Qué dicen los textos

He buscado en las seis fuentes «recíproc», «circular», «cruzad», «autocartera», «acciones propias» y «participaciones propias».

- **Ley 10/2010, RD 304/2014, RD 609/2023 y CCom art. 42:** no dicen nada sobre ciclos. Las pocas coincidencias no tienen relación con el tema («sociedades de garantía recíproca», «comunicaciones recíprocas»).
- **AMLR:** no dice nada expreso. El art. 52.1 manda multiplicar a lo largo de cada cadena y sumar «los resultados de esas distintas cadenas», teniendo en cuenta «todas las participaciones en todos los niveles de propiedad».
  - Si hay un ciclo, hay infinitas cadenas. El texto no dice si se suman todas, lo que da una serie que converge, o si una cadena no puede pasar dos veces por la misma entidad.
- **Directiva 2013/34/UE, art. 22.5:** es lo único que trata un ciclo, y solo para los votos y para decidir el control. Dice: «deben sustraerse de la totalidad de los derechos de voto de los accionistas o socios de la empresa filial los derechos de voto propios de las acciones o participaciones de las que sea titular esta misma empresa, una empresa filial de esta, o una persona que actúe en su propio nombre pero por cuenta de dichas empresas».
  - Es decir, los votos que una entidad tiene sobre sí misma, directamente o a través de sus filiales, salen del total.
- **Directiva 2013/34/UE, art. 24.3.a:** es una norma contable de consolidación y no forma parte de la remisión de la Ley. Las acciones de la matriz que tenga «esa misma empresa u otra empresa incluida en la consolidación» deben «tratarse como acciones o participaciones propias».

### 4.2 Ejemplo: el resultado depende del método

S tiene tres socios: P (45 %), Q (35 %) y H (20 %). A su vez, S tiene el 60 % de H y R tiene el 40 % restante de H. Hay un ciclo: S → H → S.

| Método | P | Q | R | Suma |
|---|---|---|---|---|
| A. Solo cadenas que no repiten entidad | 45 % | 35 % | 8 % (40 % × 20 %) | 88 % |
| B. Todas las cadenas: serie infinita, cada vuelta multiplica por 0,6 × 0,2 = 0,12 | 51,14 % (45/0,88) | 39,77 % | 9,09 % | 100 % |
| C. Votos por analogía con la Dir. 22.5: se quita el 20 % de H del total porque H es filial de S | 56,25 % (45/80) | 43,75 % | 0 % | 100 % |

Estas cifras se recalculan con fracciones exactas en [`verificacion/test_cifras_ciclos.py`](../verificacion/test_cifras_ciclos.py) (especificación del cálculo, §6.5).

**Lectura (mía):**
- Por el umbral del 25 %, los tres métodos dan el mismo resultado: P y Q son titulares reales y R no.
- Por el umbral de control del «50 % más una» (AMLR 53.2.c), P controla S con los métodos B y C, y no con el A. Si S fuera una entidad intermedia de una cadena más larga, eso cambiaría el resultado del art. 54.
- El método C es una analogía: el art. 22.5 está escrito para decidir si hay que consolidar cuentas.

### 4.3 Qué hace el modelo

- **[D10 — decisión propia]** Los ciclos se **admiten** en la entrada, porque existen en estructuras reales y porque el art. 22.5 necesita verlos. La validación los detecta y avisa (AVI-01), pero no los rechaza.
- **[D9 — decisión propia] La autocartera se representa como una arista reflexiva** (`titular` = `participada`). Así los tres casos del art. 22.5 (la propia entidad, sus filiales y las personas que actúan por su cuenta) se representan todos con aristas, sin campos especiales.
- **[Pendiente]** El método para tratar los ciclos (A, B, C u otro) se decidirá en la especificación del cálculo, para cada régimen.
  - Propuesta: calcular con los tres métodos. Si coinciden en quién es titular real, dar el resultado. Si no coinciden, indicarlo en lugar de elegir uno sin decirlo.

---

## 5. Participaciones por cuenta de otro

### 5.1 Qué dicen los textos

**Código de Comercio, art. 42.1, último párrafo:** a los votos de la dominante se añaden los que tenga «a través de personas que actúen en su propio nombre pero por cuenta de la entidad dominante o de otras dependientes». Esto está **dentro del cálculo de votos**, no en el control por otros medios.

**Directiva 2013/34/UE:**
- **22.3:** hace la misma suma, y además incluye los derechos de nombramiento y cese.
- **22.4.a:** resta al titular formal los derechos de las acciones «de las que se ostente la titularidad por cuenta de una persona distinta de la sociedad matriz o de una filial de esa matriz».
- **22.4.b:** hace lo mismo con las acciones recibidas en garantía o vinculadas a operaciones de préstamo, cuando los votos se ejercen según instrucciones o en interés de quien da la garantía.

**AMLR:**
- **53.4.c:** clasifica expresamente «el uso de acuerdos de nominatario formales o informales» como **control por otros medios**, y define «acuerdo formal de nominatario».
- **Art. 66:** los nominatarios deben revelar «la identidad de su nominador» a la entidad jurídica.
- **Art. 52.1:** no dice si lo que el nominatario tiene cuenta como propiedad del nominador.

**Ley 10/2010:**
- **Art. 4.2.b:** dice «posean o controlen, directa o indirectamente» y no menciona a las personas interpuestas.
- **Arts. 4.2.a y 4.3:** tratan de quien actúa por cuenta de terceros, pero en la relación con el cliente, no dentro de la estructura de propiedad.

### 5.2 Conclusión

- **No se puede dejar fuera de v0.1 diciendo que es «control por otros medios».**
  - El AMLR sí lo clasifica así.
  - Las normas a las que remite la Ley española (CCom 42 y Dir. 22.3–22.4) lo tratan como parte del cálculo de votos.
- **No representarlo da resultados erróneos sin avisar:**
  - el testaferro que figura como titular formal podría salir como titular real;
  - la persona por cuya cuenta actúa podría no salir.

**[D11 — decisión propia]** `por_cuenta_de` entra en v0.1:
- **Quién es `titular`.** Es siempre quien figura formalmente, como en el libro registro de socios. `por_cuenta_de` apunta a la persona o entidad por cuya cuenta se tiene.
- **Por qué esa dirección.** Coincide con cómo lo formulan la Dir. 22.4.a («se ostente la titularidad por cuenta de») y el art. 66 del AMLR (el nominatario revela a su nominador).
- **Garantías.** Una prenda en la que el acreedor tiene la titularidad y vota según las instrucciones del deudor (Dir. 22.4.b.i) se representa igual, con `por_cuenta_de` apuntando al deudor.
- **[Pendiente]** El tratamiento en el cálculo se fija por régimen:
  - si la participación se atribuye al principal, y en qué magnitudes (la Directiva solo habla de derechos de voto y de nombramiento; del capital no dice nada);
  - o si se evalúa como control por otros medios (AMLR).
  - **Requisito mínimo desde v0.1:** una arista con `por_cuenta_de` nunca se puede tratar como una participación normal sin avisar (AVI-06).

---

## 6. Validaciones de entrada

### 6.1 ¿Puede una entidad tener participaciones que sumen más del 100 %?

- **En los textos:** ninguno contempla que las participaciones en una entidad sumen más del 100 %. Los porcentajes son partes de un único capital y de un único total de votos.
- **Qué suele haber detrás de una suma superior al 100 % (fuera de los textos):**
  - fechas distintas mezcladas;
  - redondeos;
  - que se haya anotado a la vez al testaferro y a la persona por cuya cuenta actúa, o al acreedor pignoraticio y al deudor. Estos son justo los casos que la Dir. 22.4 separa.
- **Derechos repartidos sobre las mismas acciones.** Como capital y votos son magnitudes independientes, el modelo puede expresar que el capital de unas acciones sea de uno y los votos de otro. Se hacen dos aristas: una con el capital y `votos: 0`, y otra con `capital: 0` y los votos. Así la suma de cada magnitud no pasa del 100 %.
- **[D15 — decisión propia]** Por eso, que una magnitud sume más del 100 % es un **error**, salvo el exceso que se explica por redondeo. La tolerancia sale de D4:
  - cada porcentaje, redondeado al valor más próximo con 4 decimales, se desvía como mucho 0,00005 de su valor real;
  - con *n* aristas con valor (no `null`) en esa entidad y esa magnitud, la suma puede pasar de 100 como mucho en *n* × 0,00005;
  - como la suma de valores con 4 decimales es múltiplo de 0,0001, eso equivale a admitir hasta **100 + ⌊n/2⌋ × 0,0001**: nada con 1 arista, 0,0001 con 2 o 3, 0,0003 con 6;
  - ejemplo: seis socios con un sexto cada uno, redondeado a 16,6667, suman 100,0002 y se admite. En cambio, 100,01 no puede salir de redondear y se rechaza;
  - el cálculo usa los valores tal cual, sin reescalarlos a 100. Admitir ese exceso no cambia ningún porcentaje individual: solo evita rechazar entradas bien redondeadas.
- **Sumar menos del 100 % sí puede ser legítimo.** Puede haber titulares no identificados, capital flotante en una cotizada o acciones al portador (la Ley 4.4 las menciona). Pero tiene consecuencias legales:
  - Ley 4.4, párr. 2: «no establecerán o mantendrán relaciones de negocio con personas jurídicas […] cuya estructura de propiedad y de control no haya podido determinarse»;
  - lo mismo en el RD 9.3;
  - además, el supuesto supletorio (Ley 4.2.b bis) solo se aplica cuando «no exista» una persona que alcance el umbral. Con parte del capital sin identificar no se puede afirmar eso.
  - Por eso sumar menos del 100 % genera un **aviso**, no un error.

### 6.2 Lista de validaciones

**Errores (la entrada se rechaza):**

| Código | Regla | Origen |
|---|---|---|
| ERR-01 | Faltan campos obligatorios, hay tipos incorrectos o **campos desconocidos** | D20 |
| ERR-02 | Hay `id` de nodo o de arista repetidos | D16 |
| ERR-03 | `entidad_objetivo` no existe o no es `entidad_juridica` | Requisito |
| ERR-04 | Una arista o un cargo apunta a un nodo que no existe (`titular`, `participada`, `por_cuenta_de`, `persona`, `representante`) | Integridad |
| ERR-05 | `participada` es una `persona_fisica` | Una persona física no puede tener dueños |
| ERR-06 | Un porcentaje está fuera de [0, 100] o tiene más de 4 decimales | D4 |
| ERR-07 | Una arista tiene `capital` y `votos` los dos a `null` | D5 |
| ERR-08 | Hay dos aristas con la misma combinación (`titular`, `participada`, `por_cuenta_de`) | D14 |
| ERR-09 | La suma de `capital` en una entidad supera 100 + ⌊n/2⌋ × 0,0001, siendo *n* el número de aristas con `capital` no nulo | D15 |
| ERR-10 | La suma de `votos` en una entidad supera 100 + ⌊n/2⌋ × 0,0001, siendo *n* el número de aristas con `votos` no nulo | D15 |
| ERR-11 | `por_cuenta_de` es igual a `titular`, o es no nulo en una arista reflexiva | D9, D11 |
| ERR-12 | Un cargo lo ocupa una entidad jurídica sin `representante`, o el `representante` no es una persona física | Ley 4.2.b bis |

- **[D14 — decisión propia]** Solo puede haber una arista por combinación de titular, participada y `por_cuenta_de`. Si alguien tiene varias clases de participaciones, se suman en una sola arista.
- **[D20 — decisión propia]** Se rechazan los campos desconocidos para detectar erratas. Importa sobre todo en los campos opcionales: si se escribe `por_cuenta` en lugar de `por_cuenta_de`, la arista se trataría como una participación normal sin avisar.

**Avisos (la entrada se acepta y el aviso acompaña al resultado):**

| Código | Regla | Origen |
|---|---|---|
| AVI-01 | Hay un ciclo, incluida la arista reflexiva. Se indican los nodos | §4 |
| AVI-02 | En una entidad de la cadena, la suma de `capital` o de `votos` es menor que 100. Se indica el porcentaje sin identificar. Si la entidad cotiza, es solo informativo | Ley 4.4; RD 9.3 |
| AVI-03 | Una entidad de la cadena no tiene titulares y no cotiza: la cadena termina sin llegar a una persona física | Ley 4.4; RD 9.3 |
| AVI-04 | Una arista tiene `capital` o `votos` a `null` | D5 |
| AVI-05 | Hay en la cadena una entidad cuya `clase` no es `sociedad` | D8; RD 8; AMLR 52.4 |
| AVI-06 | Hay aristas con `por_cuenta_de`: su tratamiento depende del régimen | §5 |
| AVI-07 | La entidad objetivo no tiene `cargos`: no se puede aplicar el supuesto supletorio | Ley 4.2.b bis; AMLR 22.2 y 63.4 |
| AVI-08 | Hay nodos que no están conectados con la entidad objetivo ni por aristas ni por cargos: se ignoran | D21 |

«En la cadena» significa que la entidad tiene un camino de aristas que llega hasta la entidad objetivo.

- **[D21 — decisión propia]** Los nodos no conectados se ignoran con un aviso en lugar de rechazar la entrada. Es habitual pasar los datos de todo un grupo, y esos nodos no afectan al cálculo.

---

## 7. Qué no puede representar v0.1

**[D19 — decisión propia]** Estos casos quedan fuera. Si en la estructura real se da alguno, el resultado de v0.1 es incompleto.

| Qué | Dónde está en los textos |
|---|---|
| Control por otros medios: acuerdos, estatutos, derecho a nombrar o cesar administradores, influencia dominante, dirección única | Ley 4.2.b; RD 8.b; CCom 42.1.b–d; Dir. 22.1.b–d y 22.2; AMLR 53.3 y 53.4.a |
| Actuación concertada | CCom 42.1, último párrafo; AMLR 53.3.a |
| Relaciones familiares | AMLR 53.4.b |
| Derechos económicos distintos del capital | AMLR 52.1 |
| Control potencial (opciones, convertibles) | CCom 42.1: «pueda ostentar»; Dir. 22.2.a: «puede ejercer» |
| Fideicomisos e instrumentos jurídicos análogos | Ley 4.2.c y d; art. 4 ter; AMLR 55 y 57 |
| Reglas propias de fundaciones y asociaciones | RD 8, párrafos finales; AMLR 52.4 |
| Diferencias de menos de 0,00005 puntos con un umbral: por ejemplo, la mitad más una acción en una sociedad con más de un millón de acciones (D23) | AMLR 52.1 y 53.2.c; Ley 4.2.b; CCom 42.1.a |

**Consecuencia importante.** El supuesto supletorio español exige que no haya nadie que «por otros medios ejerza el control» (Ley 4.2.b bis). Como v0.1 no evalúa ese control, cuando aplique ese supuesto tendrá que decir que es **condicional**.

---

## 8. Decisiones propias

La columna «Origen» indica cuándo se planteó la alternativa descartada:
- **diseño:** se sopesó al diseñar el modelo;
- **revisión:** se formuló después, al revisar las decisiones (2026-09-15). Es la opción obvia que la decisión deja fuera, o un cambio respecto a la versión anterior de este documento.

| # | Decisión | Sección | Alternativa descartada | Motivo | Origen |
|---|---|---|---|---|---|
| D1 | La entrada recoge hechos, no conclusiones | §1 | Incluir conclusiones: «controla», «es titular real» o el «criterio» de la Ley 4 bis.4.g | La conclusión depende del régimen. Si va en la entrada, el cálculo solo la repite y no se pueden comparar los regímenes | revisión |
| D2 | El régimen es un parámetro del cálculo, no de la entrada | §1 | Un campo `regimen` en el JSON | Obligaría a duplicar la estructura para calcularla con los dos regímenes | diseño |
| D3 | `fecha_referencia` obligatoria, en la raíz | §3.1 | Opcional, o solo fechas en cada arista | Los regímenes se aplican en fechas distintas (AMLR, art. 90), y mezclar fechas es la causa típica de sumas por encima del 100 % | revisión |
| D4 | Porcentajes de 0 a 100, máximo 4 decimales, leídos como decimales exactos | §3.4 | (a) Escala 0–1. (b) Porcentajes como texto (`"25.00"`). (c) Fracciones exactas (`"1/3"`) | (a) Los textos hablan de «25 por ciento». (b) Es más seguro frente al redondeo binario, pero hace el JSON menos natural; basta exigir lectura decimal exacta. (c) Añade complejidad para un caso raro (tercios, sextos) | diseño |
| D5 | `capital` y `votos` obligatorios; `null` = desconocido; no se deducen el uno del otro | §3.4 | Tomar los votos iguales al capital cuando falten | Ocultaría las participaciones sin voto, y el umbral puede superarse en cualquiera de las dos magnitudes | diseño |
| D6 | `votos` en bruto; los ajustes de la Dir. 22.5 los hace el cálculo | §3.4 | Votos ya ajustados, sin la autocartera | El ajuste depende del régimen y de qué entidades son filiales, cosa que calcula el propio programa. Si viniera hecho, no se sabría con qué criterio | diseño |
| D7 | `capital` = % del capital social; se usa también como «acciones» en el AMLR | §2.2 | Una tercera magnitud, `derechos_economicos` (AMLR 52.1) | El requisito del modelo son dos magnitudes. Pérdida conocida: con el AMLR, v0.1 falla si los derechos económicos no son proporcionales al capital | diseño |
| D8 | `clase` de entidad; v0.1 solo calcula a través de sociedades | §3.3 | Sin `clase`, tratando todas las entidades como sociedades | El RD 8 (fundaciones y asociaciones) y el AMLR 52.4 tienen reglas propias. Tratarlas como sociedades daría resultados erróneos sin avisar | revisión |
| D9 | Autocartera como arista reflexiva | §4.3 | Un atributo `autocartera` en la entidad | La Dir. 22.5 trata juntas la autocartera, las acciones en manos de filiales y las que se tienen por cuenta de ellas. Con aristas, las tres se representan igual | diseño |
| D10 | Los ciclos se admiten y se avisan | §4.3 | (a) Rechazar la entrada. (b) Romper los ciclos al leerla | (a) Existen en estructuras reales. (b) Cómo tratarlos es una decisión del cálculo, y cambia el resultado del umbral del 50 % (§4.2) | diseño |
| D11 | `por_cuenta_de` entra en v0.1; `titular` es el titular formal | §5.2 | (a) Dejarlo fuera como control por otros medios. (b) Arista desde el principal, con un campo `a_traves_de`. (c) Un campo `motivo` (testaferro, garantía, préstamo) | (a) El CCom 42 y la Dir. 22.3 lo tratan dentro del cálculo de votos; omitirlo da falsos positivos y negativos. (b) Los registros muestran al titular formal, y así lo formulan la Dir. 22.4.a y el AMLR 66. (c) Hoy ninguna regla lo necesita | diseño |
| D12 | Una sola lista de `cargos`, con `ejecutivo` y `representante` | §3.5 | Dos listas: administradores (España) y cargos de dirección de alto nivel (AMLR) | La misma persona aparecería en las dos; separarlas duplicaría datos | revisión |
| D13 | `cotizacion` con dos condiciones separadas | §3.3 | Un simple `cotizada: true` | La Ley 4.2.b, párr. 3 exige dos condiciones y la segunda es una valoración. Con un booleano se daría por hecha | diseño |
| D14 | Una arista por (titular, participada, `por_cuenta_de`) | §6.2 | Admitir aristas repetidas y sumarlas | Una arista repetida suele ser un dato duplicado por error, y sumarla lo taparía | diseño |
| D15 | Más del 100 % en una magnitud es un error, salvo el exceso de redondeo: hasta 100 + ⌊n/2⌋ × 0,0001. Menos del 100 % es un aviso | §6.1 | (a) Tolerancia fija de 0,01 (versión anterior). (b) Sin tolerancia. (c) Un campo `accionariado_completo` | (a) Es 100 veces la resolución de D4 y deja pasar errores que no son de redondeo. (b) Rechaza entradas bien redondeadas: seis sextos suman 100,0002. (c) Sobra: el aviso ya da el porcentaje sin identificar | revisión (a); diseño (b, c) |
| D16 | `id` obligatorio en las aristas | §3.4 | `id` opcional | El cálculo tiene que poder explicar cada resultado indicando la cadena exacta | diseño |
| D17 | `fuente` y `desde` opcionales | §3.4 | Dejarlos fuera | `desde` lo pide el AMLR 62.1.b; `fuente` sirve para documentar las comprobaciones (RD 8.b, Ley 4.2.b bis) | diseño |
| D18 | `identificacion` opcional y sin validar en v0.1 | §3.2 | (a) Omitirla. (b) Validar su contenido (DNI, fechas…) | (a) La necesitará la salida. (b) El cálculo no la usa, y validar documentos de identidad es trabajo aparte | diseño |
| D19 | Lo del §7 queda fuera de v0.1 | §7 | Reservar campos (p. ej., `controles_otros_medios`) aunque v0.1 no los use | Un campo que el cálculo ignora da la falsa impresión de que se tiene en cuenta | diseño |
| D20 | Se rechazan los campos desconocidos | §6.2 | Ignorarlos | Una errata en un campo opcional pasaría inadvertida (p. ej., `por_cuenta` en lugar de `por_cuenta_de`) | diseño |
| D21 | Los nodos no conectados con la entidad objetivo se ignoran con aviso | §6.2 | Rechazar la entrada | Es habitual pasar los datos de todo un grupo, y esos nodos no afectan al cálculo | revisión |
| D22 | El «órgano de administración» español se trata como el «órgano de dirección» del AMLR 63.4 | §3.5 | (a) No suponer nada y dejar sin calcular el supuesto supletorio del AMLR. (b) Un campo que indique qué órgano es | (a) Dejaría sin resultado el supuesto del AMLR para cualquier entidad española. (b) Se podrá añadir si aparecen entidades con órganos separados, que los textos europeos distinguen (AMLR 53.3.b; Dir. 22.1.b) | revisión |
| D23 | Un valor igual a un umbral (25 o 50) se lee como exacto; el cálculo avisa si leerlo al otro lado cambia quién es titular real | §3.4 | (a) Registrar el número de acciones y de votos, o fracciones exactas (D4, alternativa c). (b) Más decimales | (a) Cambia la base del modelo para un caso que solo aparece en el valor exacto del umbral y que el cálculo puede detectar. (b) Solo desplaza el límite: con cualquier número fijo de decimales hay un tamaño a partir del cual pasa lo mismo | revisión |

## 9. Pendiente para la especificación del cálculo

Nada de lo siguiente está resuelto en los textos. La [especificación del cálculo](especificacion-calculo.md) fija cómo se trata cada punto en v0.1; la referencia va al final de cada uno.

1. **Ciclos:** qué método se usa en cada régimen (§4.2). → Especificación §6 (C20).
2. **Participaciones por cuenta de otro:** se atribuyen al principal o se tratan como control por otros medios, y en qué magnitudes (§5.2). → Especificación §2.2 (C2). Quedan abiertos N9 (AMLR) y N13 (España, capital), que se señalan con POS-FORMAL (C29).
3. **España, participación indirecta:** si se multiplica a lo largo de la cadena o se suman los votos completos de las entidades controladas, como en el CCom 42.1 y la Dir. 22.3. La Ley no da método. → Especificación §5 (C17 a C19).
4. **Mezcla de magnitudes en una cadena:** si se multiplica capital por capital y votos por votos, o si se pueden mezclar. Ni la Ley 4.2.b ni el AMLR 52.1 lo dicen. Por eso el modelo guarda las dos magnitudes en cada arista y no una sola. → Especificación §7 (C21).
5. **AMLR, «acciones» frente a «capital»** cuando no son proporcionales (D7). → La especificación no lo trata: v0.1 sigue con la aproximación de D7.

---

## 10. Ejemplo completo

```json
{
  "version_modelo": "0.1",
  "fecha_referencia": "2026-09-15",
  "entidad_objetivo": "E-OBJETIVO",
  "nodos": [
    {
      "id": "E-OBJETIVO",
      "tipo": "entidad_juridica",
      "denominacion": "Objetivo Ejemplo, S.L.",
      "clase": "sociedad",
      "forma_juridica": "sociedad de responsabilidad limitada",
      "pais": "ES",
      "nif": "B00000000",
      "cargos": [
        {
          "persona": "E-GESTORA",
          "cargo": "miembro_organo_administracion",
          "ejecutivo": false,
          "representante": "P-ELENA"
        },
        {
          "persona": "P-FERNANDO",
          "cargo": "miembro_organo_administracion",
          "ejecutivo": true
        },
        {
          "persona": "P-GLORIA",
          "cargo": "directivo",
          "ejecutivo": true
        }
      ]
    },
    {
      "id": "E-HOLDING",
      "tipo": "entidad_juridica",
      "denominacion": "Holding Norte Ejemplo, S.L.",
      "clase": "sociedad",
      "pais": "ES"
    },
    {
      "id": "E-BETA",
      "tipo": "entidad_juridica",
      "denominacion": "Beta Ejemplo, Lda.",
      "clase": "sociedad",
      "pais": "PT"
    },
    {
      "id": "E-FONDO",
      "tipo": "entidad_juridica",
      "denominacion": "Fondo Ejemplo S.à r.l.",
      "clase": "sociedad",
      "pais": "LU"
    },
    {
      "id": "E-GESTORA",
      "tipo": "entidad_juridica",
      "denominacion": "Gestora Ejemplo, S.A.",
      "clase": "sociedad",
      "pais": "ES"
    },
    {
      "id": "P-ANA",
      "tipo": "persona_fisica",
      "nombre": "Ana Ejemplo Uno",
      "identificacion": {
        "fecha_nacimiento": "1970-01-01",
        "documento": { "tipo": "DNI", "numero": "00000000T", "pais_expedicion": "ES" },
        "pais_residencia": "ES",
        "nacionalidades": ["ES"]
      }
    },
    { "id": "P-BRUNO",    "tipo": "persona_fisica", "nombre": "Bruno Ejemplo Dos" },
    { "id": "P-CARLOS",   "tipo": "persona_fisica", "nombre": "Carlos Ejemplo Tres" },
    { "id": "P-DIEGO",    "tipo": "persona_fisica", "nombre": "Diego Ejemplo Cuatro" },
    { "id": "P-ELENA",    "tipo": "persona_fisica", "nombre": "Elena Ejemplo Cinco" },
    { "id": "P-FERNANDO", "tipo": "persona_fisica", "nombre": "Fernando Ejemplo Seis" },
    { "id": "P-GLORIA",   "tipo": "persona_fisica", "nombre": "Gloria Ejemplo Siete" }
  ],
  "participaciones": [
    {
      "id": "p01",
      "titular": "P-ANA",
      "participada": "E-OBJETIVO",
      "capital": 20,
      "votos": 25,
      "desde": "2019-05-10",
      "fuente": "Libro registro de socios a 30-06-2026"
    },
    { "id": "p02", "titular": "E-HOLDING", "participada": "E-OBJETIVO", "capital": 30, "votos": 35 },
    {
      "id": "p03",
      "titular": "P-BRUNO",
      "participada": "E-OBJETIVO",
      "capital": 18,
      "votos": 20,
      "por_cuenta_de": "P-CARLOS",
      "fuente": "Declaración del nominatario"
    },
    { "id": "p04", "titular": "E-FONDO",    "participada": "E-OBJETIVO", "capital": 20, "votos": 0 },
    { "id": "p05", "titular": "P-DIEGO",    "participada": "E-OBJETIVO", "capital": 12, "votos": 20 },
    { "id": "p06", "titular": "P-ANA",      "participada": "E-HOLDING",  "capital": 60, "votos": 60 },
    { "id": "p07", "titular": "E-BETA",     "participada": "E-HOLDING",  "capital": 40, "votos": 40 },
    { "id": "p08", "titular": "P-CARLOS",   "participada": "E-BETA",     "capital": 50, "votos": 50 },
    { "id": "p09", "titular": "E-OBJETIVO", "participada": "E-BETA",     "capital": 50, "votos": 50 }
  ]
}
```

### 10.1 Qué casos cubre el ejemplo

| Caso | Dónde |
|---|---|
| Persona con participación directa e indirecta a la vez | P-ANA: p01 directa; p06 → p02 a través de E-HOLDING, que controla con el 60 % |
| Varias cadenas hasta la misma entidad | E-OBJETIVO recibe cinco aristas; P-CARLOS llega por dos vías distintas |
| Capital y votos distintos | p01 (20/25), p02 (30/35), p05 (12/20) y p04 sin voto (20/0) |
| Participación por cuenta de otro | p03: P-BRUNO es el titular formal por cuenta de P-CARLOS |
| Ciclo | E-OBJETIVO → E-BETA (p09) → E-HOLDING (p07) → E-OBJETIVO (p02) |
| Cadena que termina sin persona física | E-FONDO no tiene titulares |
| Administrador persona jurídica con representante | E-GESTORA, representada por P-ELENA |
| Los supuestos supletorios dan resultados distintos | España: P-ELENA (por E-GESTORA) y P-FERNANDO. AMLR: P-FERNANDO y P-GLORIA |

### 10.2 Resultado esperado de la validación

- **Errores:** ninguno.
  - E-OBJETIVO suma 100 en capital (20+30+18+20+12) y 100 en votos (25+35+20+0+20).
  - E-HOLDING y E-BETA suman 100 en las dos magnitudes.
- **Avisos:**
  - **AVI-01:** ciclo E-OBJETIVO → E-BETA → E-HOLDING → E-OBJETIVO.
  - **AVI-02 y AVI-03:** E-FONDO está en la cadena, no tiene titulares identificados (0 %) y no cotiza.
  - **AVI-06:** la arista p03 tiene `por_cuenta_de`.
