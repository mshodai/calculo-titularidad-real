"""Utilidades de grafos comunes a la validación y al cálculo."""


def componentes_fuertes(nodos, sucesores):
    """Componentes fuertemente conexas (Tarjan, sin recursión).

    `sucesores` debe devolver una lista vacía para los nodos sin sucesores
    (por ejemplo, un defaultdict(list)).
    """
    indice, bajo, en_pila, pila, componentes = {}, {}, set(), [], []
    for raiz in nodos:
        if raiz in indice:
            continue
        indice[raiz] = bajo[raiz] = len(indice)
        pila.append(raiz)
        en_pila.add(raiz)
        trabajo = [(raiz, iter(sucesores[raiz]))]
        while trabajo:
            nodo, hijos = trabajo[-1]
            for hijo in hijos:
                if hijo not in indice:
                    indice[hijo] = bajo[hijo] = len(indice)
                    pila.append(hijo)
                    en_pila.add(hijo)
                    trabajo.append((hijo, iter(sucesores[hijo])))
                    break
                if hijo in en_pila:
                    bajo[nodo] = min(bajo[nodo], indice[hijo])
            else:
                trabajo.pop()
                if trabajo:
                    padre = trabajo[-1][0]
                    bajo[padre] = min(bajo[padre], bajo[nodo])
                if bajo[nodo] == indice[nodo]:
                    componente = []
                    while True:
                        miembro = pila.pop()
                        en_pila.discard(miembro)
                        componente.append(miembro)
                        if miembro == nodo:
                            break
                    componentes.append(componente)
    return componentes
