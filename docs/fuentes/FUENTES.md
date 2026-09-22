# Fuentes

Documentos oficiales que usa el proyecto. Los PDF no se redistribuyen (están en `.gitignore`), así que cada uno debe descargarse de su URL y guardarse en `docs/fuentes/` con el nombre indicado.

**Qué significa cada columna:**

- **Autor.** Órgano emisor, tal como figura en la cabecera del documento. Entre paréntesis, el editor del PDF según sus metadatos.
- **Versión o fecha declarada.** Copiada literalmente del documento.
- **Fecha de descarga.** Es la fecha de creación del fichero en disco. Los metadatos de origen de macOS (`kMDItemWhereFroms`) confirman que se descargaron de `boe.es` o de `eur-lex.europa.eu`, pero no guardan la URL completa.
- **URL.** Es la dirección canónica deducida del identificador de cada documento. Todas se comprobaron por descarga el 22/09/2026: cada una devolvió un fichero idéntico al local (mismo SHA-256), también las dos de EUR-Lex.
  - EUR-Lex rechaza a veces las descargas automáticas: responde `202` con un cuerpo vacío. Por eso, en la primera comprobación, el 2026-09-15, sus dos URL no se pudieron comprobar (las cuatro del BOE sí), y el 22/09/2026 hicieron falta varios intentos.

## Documentos

| Fichero | Título | Autor | Versión o fecha declarada | Descarga | URL |
|---|---|---|---|---|---|
| `BOE-A-2010-6737-consolidado.pdf` | Ley 10/2010, de 28 de abril, de prevención del blanqueo de capitales y de la financiación del terrorismo | Jefatura del Estado (Agencia Estatal Boletín Oficial del Estado) | Texto consolidado. «Última modificación: 21 de marzo de 2026». Original: «BOE» núm. 103, de 29 de abril de 2010 | 2026-09-15 | https://www.boe.es/buscar/pdf/2010/BOE-A-2010-6737-consolidado.pdf · ficha: https://www.boe.es/buscar/act.php?id=BOE-A-2010-6737 |
| `BOE-A-2014-4742-consolidado.pdf` | Real Decreto 304/2014, de 5 de mayo, por el que se aprueba el Reglamento de la Ley 10/2010, de 28 de abril, de prevención del blanqueo de capitales y de la financiación del terrorismo | Ministerio de Economía y Competitividad (Agencia Estatal Boletín Oficial del Estado) | Texto consolidado. «Última modificación: 24 de abril de 2024». Original: «BOE» núm. 110, de 06 de mayo de 2014 | 2026-09-15 | https://www.boe.es/buscar/pdf/2014/BOE-A-2014-4742-consolidado.pdf · ficha: https://www.boe.es/buscar/act.php?id=BOE-A-2014-4742 |
| `BOE-A-2023-16159-consolidado.pdf` | Real Decreto 609/2023, de 11 de julio, por el que se crea el Registro Central de Titularidades Reales y se aprueba su Reglamento | Ministerio de la Presidencia, Relaciones con las Cortes y Memoria Democrática (Agencia Estatal Boletín Oficial del Estado) | Texto consolidado. «Última modificación: sin modificaciones». Original: «BOE» núm. 165, de 12 de julio de 2023 | 2026-09-15 | https://www.boe.es/buscar/pdf/2023/BOE-A-2023-16159-consolidado.pdf · ficha: https://www.boe.es/buscar/act.php?id=BOE-A-2023-16159 |
| `BOE-A-1885-6627-consolidado.pdf` | Real Decreto de 22 de agosto de 1885 por el que se publica el Código de Comercio | Ministerio de Gracia y Justicia (Agencia Estatal Boletín Oficial del Estado) | Texto consolidado. «Última modificación: 09 de mayo de 2023». Original: «Gaceta de Madrid» núm. 289, de 16 de octubre de 1885 | 2026-09-15 | https://www.boe.es/buscar/pdf/1885/BOE-A-1885-6627-consolidado.pdf · ficha: https://www.boe.es/buscar/act.php?id=BOE-A-1885-6627 |
| `CELEX_02013L0034-20240528_ES_TXT.pdf` | Directiva 2013/34/UE del Parlamento Europeo y del Consejo, de 26 de junio de 2013, sobre los estados financieros anuales, los estados financieros consolidados y otros informes afines de ciertos tipos de empresas | Parlamento Europeo y Consejo (Oficina de Publicaciones de la UE) | Versión consolidada «02013L0034 — ES — 28.05.2024 — 006.003». Última modificación incorporada: M7, Directiva (UE) 2024/1306. Original: DO L 182 de 29.6.2013, p. 19. El propio documento advierte que «no surte efecto jurídico» | 2026-09-15 | https://eur-lex.europa.eu/legal-content/ES/TXT/PDF/?uri=CELEX:02013L0034-20240528 (comprobado el 22/09/2026 por descarga) |
| `OJ_L_202401624_ES_TXT.pdf` | Reglamento (UE) 2024/1624 del Parlamento Europeo y del Consejo, de 31 de mayo de 2024, relativo a la prevención de la utilización del sistema financiero para el blanqueo de capitales o la financiación del terrorismo (AMLR) | Parlamento Europeo y Consejo (Oficina de Publicaciones de la UE) | Texto publicado, no consolidado: «DO L de 19.6.2024». No declara fecha de modificación. Art. 90: aplicable a partir del 10 de julio de 2027 | 2026-09-15 | https://eur-lex.europa.eu/legal-content/ES/TXT/PDF/?uri=OJ:L_202401624 (comprobado el 22/09/2026 por descarga) · ELI impreso en el documento: http://data.europa.eu/eli/reg/2024/1624/oj |

## Huellas SHA-256 de los ficheros usados

Sirven para comprobar que una copia local es la misma versión con la que se hizo el análisis. El BOE y EUR-Lex regeneran los PDF cuando cambia el texto consolidado, así que una huella distinta indica una versión distinta.

```
4782a40bcf44165a97bc361520fd2b348acf7efbdfaa0a8d876c58332ff8601d  BOE-A-2010-6737-consolidado.pdf
59d7be80313780a8cf48e1f3f87b5bd2860855a126472c0374e1c30c7fc19f0d  BOE-A-2014-4742-consolidado.pdf
b86ea6b9092d17a6ca21b6fa7b3ecff100a22650cf3bdc5ae88e6e029e8e9e6a  BOE-A-2023-16159-consolidado.pdf
b90da32c6756b9d856bc2dd3073ae2c81ff58434c334b44dcba4af683fb8e147  BOE-A-1885-6627-consolidado.pdf
889d4357af67e6e2925b43dbaa0326660a0af9a9cf94046822df0e24625c6681  CELEX_02013L0034-20240528_ES_TXT.pdf
666f18e1b5d4dd6bb7e927328bd8d84420d0919e692288f0b917c357df690974  OJ_L_202401624_ES_TXT.pdf
```

## Datos para la vigilancia automática

Repite en formato legible por máquina el fichero, la URL de descarga y la huella SHA-256 de cada documento de las secciones anteriores. Lo lee el script de `vigilancia-fuentes`, que comprueba que coincida con el texto. Si difieren, prevalece el texto.

```json
{
  "documentos": [
    {
      "fichero": "BOE-A-2010-6737-consolidado.pdf",
      "url": "https://www.boe.es/buscar/pdf/2010/BOE-A-2010-6737-consolidado.pdf",
      "sha256": "4782a40bcf44165a97bc361520fd2b348acf7efbdfaa0a8d876c58332ff8601d"
    },
    {
      "fichero": "BOE-A-2014-4742-consolidado.pdf",
      "url": "https://www.boe.es/buscar/pdf/2014/BOE-A-2014-4742-consolidado.pdf",
      "sha256": "59d7be80313780a8cf48e1f3f87b5bd2860855a126472c0374e1c30c7fc19f0d"
    },
    {
      "fichero": "BOE-A-2023-16159-consolidado.pdf",
      "url": "https://www.boe.es/buscar/pdf/2023/BOE-A-2023-16159-consolidado.pdf",
      "sha256": "b86ea6b9092d17a6ca21b6fa7b3ecff100a22650cf3bdc5ae88e6e029e8e9e6a"
    },
    {
      "fichero": "BOE-A-1885-6627-consolidado.pdf",
      "url": "https://www.boe.es/buscar/pdf/1885/BOE-A-1885-6627-consolidado.pdf",
      "sha256": "b90da32c6756b9d856bc2dd3073ae2c81ff58434c334b44dcba4af683fb8e147"
    },
    {
      "fichero": "CELEX_02013L0034-20240528_ES_TXT.pdf",
      "url": "https://eur-lex.europa.eu/legal-content/ES/TXT/PDF/?uri=CELEX:02013L0034-20240528",
      "sha256": "889d4357af67e6e2925b43dbaa0326660a0af9a9cf94046822df0e24625c6681"
    },
    {
      "fichero": "OJ_L_202401624_ES_TXT.pdf",
      "url": "https://eur-lex.europa.eu/legal-content/ES/TXT/PDF/?uri=OJ:L_202401624",
      "sha256": "666f18e1b5d4dd6bb7e927328bd8d84420d0919e692288f0b917c357df690974"
    }
  ]
}
```
