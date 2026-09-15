"""Estructuras de datos de la entrada, según docs/modelo-datos.md v0.1.

Describen la entrada ya validada y no contienen ninguna regla de cálculo.
Los porcentajes son Decimal (D4), y None en `capital` o `votos` significa
«desconocido» (D5).
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

VERSION_MODELO = "0.1"
ESPANA = "espana"
AMLR = "amlr"
MAGNITUDES = ("capital", "votos")
CLASES = ("sociedad", "fundacion", "asociacion", "otra")
TIPOS_CARGO = ("miembro_organo_administracion", "directivo")


@dataclass(frozen=True)
class Documento:
    tipo: str | None = None
    numero: str | None = None
    pais_expedicion: str | None = None


@dataclass(frozen=True)
class Identificacion:
    """Datos de identificación de la persona física (§3.2, D18)."""

    fecha_nacimiento: str | None = None
    lugar_nacimiento: str | None = None
    documento: Documento | None = None
    pais_residencia: str | None = None
    nacionalidades: tuple[str, ...] = ()
    domicilio: str | None = None
    email: str | None = None


@dataclass(frozen=True)
class PersonaFisica:
    id: str
    nombre: str
    identificacion: Identificacion | None = None


@dataclass(frozen=True)
class Cotizacion:
    """Las dos condiciones de la Ley 4.2.b, párr. 3, por separado (D13)."""

    mercado: str
    requisitos_informacion_ue_o_equivalentes: bool


@dataclass(frozen=True)
class Cargo:
    """Cargo en la entidad (§3.5, D12)."""

    persona: str
    cargo: str
    ejecutivo: bool
    representante: str | None = None


@dataclass(frozen=True)
class EntidadJuridica:
    id: str
    denominacion: str
    clase: str
    forma_juridica: str | None = None
    pais: str | None = None
    nif: str | None = None
    euid: str | None = None
    cotizacion: Cotizacion | None = None
    cargos: tuple[Cargo, ...] = ()


Nodo = PersonaFisica | EntidadJuridica


@dataclass(frozen=True)
class Participacion:
    """Arista del grafo: `titular` es siempre el titular formal (D11)."""

    id: str
    titular: str
    participada: str
    capital: Decimal | None
    votos: Decimal | None
    por_cuenta_de: str | None = None
    desde: date | None = None
    fuente: str | None = None


@dataclass(frozen=True)
class Entrada:
    version_modelo: str
    fecha_referencia: date
    entidad_objetivo: str
    nodos: dict[str, Nodo]
    participaciones: tuple[Participacion, ...]


@dataclass(frozen=True)
class Incidencia:
    """Error o aviso del §6.2. `ids` son los nodos o aristas afectados.

    La validación no depende del régimen (D2). `informativo_en` dice en qué
    regímenes el aviso es solo informativo (ESPANA, AMLR); en los demás es un
    aviso normal.
    """

    codigo: str
    mensaje: str
    ids: tuple[str, ...] = ()
    informativo_en: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResultadoCarga:
    """La entrada validada, o None si hay algún error, con errores y avisos."""

    entrada: Entrada | None
    errores: tuple[Incidencia, ...]
    avisos: tuple[Incidencia, ...]

    @property
    def valida(self) -> bool:
        return not self.errores
