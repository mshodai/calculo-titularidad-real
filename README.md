# calculo-titularidad-real

Cuando una sociedad pertenece a otras sociedades, saber quién es su titular real (la persona física que en último término la posee o la controla) exige recorrer la cadena de participaciones, y la respuesta depende del régimen con el que se calcule.

Un ejemplo. La sociedad S tiene dos socios: la persona R, con el 40 %, y la sociedad C, con el 60 %. C tiene a su vez dos socios: P, con el 30 %, y Q, con el 70 %. ¿Quién es titular real de S? Según la Ley 10/2010, Q y R. Según el Reglamento (UE) 2024/1624, el AMLR, que será aplicable desde el 10 de julio de 2027, también P: C controla S, y el AMLR cuenta como titular a quien tiene el 25 % de quien controla la sociedad. La Ley española no tiene esa regla.

Esta herramienta calcula los dos regímenes sobre la misma estructura, los compara y dice de qué lectura de la norma depende cada resultado. No da una respuesta cerrada: el porqué está en el [ADR 0001](docs/adr/0001-comparar-en-lugar-de-responder.md).

## Ejecútalo en 60 segundos

El repositorio incluye un corpus de doce estructuras sintéticas en `corpus/`, cada una con su resultado esperado. Esto es lo que produce la herramienta con la del ejemplo de arriba:

```
$ calcular-titularidad corpus/03-art54b-participacion-arriba.json
Titularidad real de «S» a 2027-07-10

Resultado de un cálculo bajo las lecturas que declara la especificación
(docs/especificacion-calculo.md), no una determinación jurídica. Donde la norma no resuelve un
caso, se indica con su número (N…), y otra lectura podría dar otro resultado. Las decisiones de la
especificación se citan como C….

ESTADO
  España  determinado
  AMLR    determinado
  ~ España: el resultado no es estable. Cambiaría con otra lectura, o una comprobación no se ha
  podido hacer: POS-T (C32).

COMPARACIÓN (según las lecturas aplicadas)
  Persona  España            AMLR
  P        posible (POS-T)   titular (A4)              ≠
  Q        titular (E1, E2)  titular (A1, A2, A3, A4)
  R        titular (E1, E2)  titular (A1)
  ≠ Resultado distinto en cada régimen para 1 de 3 personas.

EN QUÉ DIFIEREN
  - «P» cumple A4 en el AMLR y no es titular en España: el art. 54.b le basta con el 25 % de una
    entidad que controla la sociedad; España no tiene esa regla (la lectura extensiva L3 solo
    avisa, C19). En España queda como posible (POS-T).

ESPAÑA · Ley 10/2010, art. 4.2.b y b bis
  Estado: determinado. Con la lectura aplicada (L1 ∪ L2, C19), hay titulares reales por E1 o E2.
  Titulares reales según las lecturas aplicadas:
    Q: E1 (L1) capital 42,00 %, votos 42,00 %; E2 (L2) 60,00 %; controla la entidad (CCom 42.1.a)
    R: E1 (L1) capital 40,00 %, votos 40,00 %; E2 (L2) 40,00 %
  Posibles titulares:
    POS-T «P» sería titular real con la lectura extensiva L3: capital 30,00 %, votos 30,00 %
    (N1/N2)
      → N1: España: método para la participación indirecta; N2: España: si el art. 42 sirve para
      medir el porcentaje que alguien «controla»

AMLR · Reglamento (UE) 2024/1624, arts. 51 a 54
  Estado: determinado. Con la unión de pruebas (C14), hay titulares reales por alguna de A1 a A4.
  Titulares reales según las lecturas aplicadas:
    P: A4 (54.b) capital 30,00 %, votos 30,00 % de «C», que controla la entidad
    Q: A1 (52.1) capital 42,00 %, votos 42,00 %; A2 (53.2) controla la entidad; A3 (54.a) capital
    60,00 %, votos 60,00 % de las entidades que controla; A4 (54.b) capital 70,00 %, votos 70,00 %
    de «C», que controla la entidad
    R: A1 (52.1) capital 40,00 %, votos 40,00 %

LECTURAS DE LAS QUE DEPENDE ESTE RESULTADO
[…]
  Casos que la norma no resuelve y que afectan a esta entrada:
    N1: España: método para la participación indirecta
    N2: España: si el art. 42 sirve para medir el porcentaje que alguien «controla»
```

La sección de lecturas, recortada aquí, lista las decisiones de la especificación de las que depende el resultado. El «~» indica que el resultado español no es estable: con otra lectura de la norma (la extensiva, que la Ley no recoge), P también sería titular.

Para obtener esa misma salida en tu máquina, hace falta Python 3.10 o posterior (probado con 3.10, 3.11 y 3.14). No tiene dependencias externas: `pip install` solo descarga setuptools para construir el paquete. Desde la raíz del repositorio:

```sh
python3 -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install .
calcular-titularidad corpus/03-art54b-participacion-arriba.json
```

En la estructura 02, P controla una sociedad con el 30 % de S. Los dos regímenes llegan al mismo resultado, cada uno por su regla:

```
$ calcular-titularidad corpus/02-art54a-control-arriba.json
[…]
ESTADO
  España  determinado
  AMLR    determinado

COMPARACIÓN (según las lecturas aplicadas)
  Persona  España            AMLR
  P        titular (E2)      titular (A3)
  X        titular (E1, E2)  titular (A1, A2)
  Los dos regímenes coinciden en quién es titular real.
[…]
```

**Códigos de salida:**
- **0:** los dos regímenes quedan determinados, estables y completos, y dan los mismos titulares. En el corpus solo pasa en la estructura 02.
- **1:** difieren, o alguno queda en otro estado (supletorio, sin titular identificado, no determinable, exceptuada, fuera de alcance), o el resultado no es estable (otra lectura lo cambiaría) o no es completo (lo cambiarían datos que faltan).
- **2:** la entrada no se puede leer o no es válida.

**Opciones:**
- `--json`: el mismo informe en JSON. Cada valor va como fracción exacta y redondeado, por ejemplo `{"exacto": "1900/47", "redondeado": "40.43"}`.
- `--regimen espana|amlr`: calcula un solo régimen, sin la comparación.

**El corpus.** Cubre, entre otros, cuatro socios al 25 % justo, las dos formas del art. 54, un ciclo que cambia el resultado según el método, una cotizada con filial, un testaferro y dos personas que controlan la misma sociedad, una por capital y otra por votos. La lista está en [corpus/README.md](corpus/README.md). Se regenera con `python corpus/generar.py`, que comprueba cada estructura contra su resultado esperado antes de escribirla.

**Tests:** `pip install pytest` y `pytest` desde la raíz. Necesitan Python 3.11 o posterior, porque uno lee `pyproject.toml` con `tomllib`.

### Con tu propia estructura

La entrada es un JSON con las personas, las sociedades y las participaciones entre ellas, cada una con su porcentaje de capital y de votos. El formato completo, con un ejemplo, está en [docs/modelo-datos.md](docs/modelo-datos.md). La herramienta valida la entrada antes de calcular. Por ejemplo, rechaza que las participaciones de una sociedad sumen más del 100 %, salvo lo que se explica por redondeo.

## Qué calcula

Para cada persona física, con los porcentajes directos e indirectos (cadenas multiplicadas y sumadas), en capital y en votos por separado:

**España (Ley 10/2010, art. 4.2.b):** es titular real quien supera el 25 % del capital o de los votos por alguna de estas dos vías.
- **E1:** multiplicando los porcentajes a lo largo de las cadenas.
- **E2:** sumando enteros los votos de las sociedades que domina, como hace el art. 42 del Código de Comercio para el control, sobre la base de votos de la Directiva 2013/34/UE (art. 22.5).

Si nadie lo supera, se presume que controlan los administradores (art. 4.2.b bis). Quedan exceptuadas las sociedades cotizadas sujetas a requisitos de información equivalentes a los de la Unión y, según el RD 304/2014 (art. 9.4), sus filiales participadas mayoritariamente.

**AMLR (arts. 51 a 54):** es titular real quien alcanza el 25 % o más por alguna de estas cuatro pruebas.
- **A1:** multiplicando los porcentajes (52.1).
- **A2:** controla la sociedad: más del 50 % del capital o de los votos, directamente o a través de sociedades que controla (53.2).
- **A3:** controla sociedades que entre todas tienen el 25 % directo (54.a).
- **A4:** tiene el 25 % de una sociedad que controla la entidad (54.b).

Si nadie lo alcanza, se identifica a los cargos de dirección de alto nivel, que no son titulares reales.

**En los dos regímenes:**
- Con ciclos de participación, suma la serie completa de cadenas.
- Atribuye las participaciones que se tienen por cuenta de otro a quien las tiene por su cuenta.
- Lo que no llega a una persona identificada queda como un titular virtual, que nunca es titular real.

Todo con fracciones exactas, sin coma flotante. Las reglas completas, con cada decisión y su motivo, están en la [especificación del cálculo](docs/especificacion-calculo.md).

## Qué no hace

- **No evalúa el control por otros medios:** pactos de socios, estatutos, derecho a nombrar o cesar administradores, actuación concertada o relaciones familiares. La entrada no los puede representar, y por eso el supuesto supletorio español siempre queda como condicional y el del AMLR como provisional.
- **No calcula fundaciones, asociaciones ni otras entidades que no son sociedades,** que tienen reglas propias (RD 304/2014, art. 8; AMLR, art. 52.4). Si la entidad objetivo no es una sociedad, el resultado es «fuera de alcance». Si lo es una intermedia, no se recorren sus titulares.
- **No trata fideicomisos ni instrumentos jurídicos análogos.**
- **No distingue los derechos económicos del capital.** El AMLR habla de «acciones, derechos de voto u otra participación en la propiedad», incluidos los derechos sobre beneficios, y aquí se usa el porcentaje de capital. Coincide solo si todas las acciones tienen los mismos derechos.
- **No tiene en cuenta el control potencial** (opciones, convertibles).
- **No consulta registros:** trabaja con la estructura que recibe.

**Un resultado «determinado» no es una determinación jurídica.** Significa que, con los datos de la entrada y las lecturas que declara la especificación, las pruebas dan esos titulares. La herramienta hace aritmética sobre un grafo de participaciones. Lo que depende de hechos que ese grafo no contiene, o de un juicio que la norma deja a quien la aplica, lo señala sin resolverlo.

## Los catorce casos que la norma no resuelve

Al analizar los textos aparecieron catorce puntos en los que la norma admite más de una lectura y el resultado cambia según cuál se elija. Por ejemplo: cómo se calcula el porcentaje indirecto en España, qué hacer con los ciclos de participación, o si el art. 54 del AMLR sustituye a la multiplicación del 52.1 o se le añade. En cada uno, esta implementación aplica una lectura declarada, calcula la alternativa cuando los datos lo permiten y avisa si cambiaría el resultado.

El AMLR es más detallado que la norma española, y aun así afecta a más casos abiertos: nueve, siete de ellos exclusivos (el art. 54, el control a través de varias sociedades, los nominatarios, la autocartera…). La norma española afecta a siete, cinco exclusivos. Las reglas más detalladas crean más puntos en los que la norma tiene que decidir.

Los catorce casos, y cuatro más que vienen del formato del dato y no de la norma, están en [docs/ambiguedades.md](docs/ambiguedades.md), con qué dice la norma, qué hace esta implementación y cómo se señala en la salida.

## Fuentes

| Documento | Versión |
|---|---|
| Ley 10/2010, de 28 de abril, de prevención del blanqueo de capitales y de la financiación del terrorismo | Texto consolidado, última modificación de 21 de marzo de 2026 |
| Real Decreto 304/2014, de 5 de mayo, Reglamento de la Ley 10/2010 | Texto consolidado, última modificación de 24 de abril de 2024 |
| Real Decreto 609/2023, de 11 de julio, Registro Central de Titularidades Reales | Texto consolidado, sin modificaciones |
| Código de Comercio (Real Decreto de 22 de agosto de 1885) | Texto consolidado, última modificación de 9 de mayo de 2023 |
| Directiva 2013/34/UE, de 26 de junio de 2013 | Versión consolidada de 28 de mayo de 2024 |
| Reglamento (UE) 2024/1624 (AMLR), de 31 de mayo de 2024 | Texto publicado en el DO L de 19 de junio de 2024, sin consolidar |

**Calendario.** Hoy se aplica el régimen español. El AMLR «será aplicable a partir del 10 de julio de 2027» (art. 90). La herramienta lo calcula también con fechas anteriores, porque la comparación lo necesita, y avisa de que todavía no es aplicable.

Los documentos se descargaron el 15 de septiembre de 2026. Las URL y las huellas SHA-256 de cada versión están en [docs/fuentes/FUENTES.md](docs/fuentes/FUENTES.md). Los PDF no se redistribuyen.

## Otras implementaciones de referencia

[validador-cadena-verifactu](https://github.com/mshodai/validador-cadena-verifactu)
— Comprueba la integridad de una cadena de registros de facturación de
Verifactu: la huella de cada registro y el encadenamiento entre ellos.

## Licencia

MIT; el texto completo está en [LICENSE](LICENSE). Cubre el código y la documentación de este repositorio, no los textos legales de `docs/fuentes/`, que no se incluyen.

---

Es una implementación de referencia, probada sobre datos sintéticos. No es software de cumplimiento normativo y no constituye asesoramiento jurídico.
