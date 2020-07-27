from itertools import islice
from logging import getLogger
from typing import ClassVar, List, Sequence, Type

from pydantic import BaseModel, ValidationError


__all__ = [
    "Model",
    "parse_rows",
]


class Model(BaseModel):
    """Clase base para los objetos leídos de una planilla.

    Esta clase define solamente la presencia de un variable de clase
    COLUMNAS, que indica siempre el nombre de las columnas donde se
    alojan los atributos del modelo.
    """

    COLUMNAS: ClassVar[Sequence[str]]


def parse_rows(rows: List[List[str]], model: Type[Model]) -> List[Model]:
    """Construye objetos de una clase modelo a partir de filas de planilla.

    Argumentos:
      rows: lista de filas de la hoja. Se asume que la primera fila
          son los nombres de las columnas.
      model: Model con que construir los objetos, usando model.COLUMNAS
          como origen (ordenado) de los atributos.

    Returns:
      una lista de los objetos construidos.
    """
    logger = getLogger(__name__)
    fields = model.__fields__.keys()
    indices = []
    objects = []
    headers = rows[0]

    for field in model.COLUMNAS:
        indices.append(headers.index(field))

    for row in islice(rows, 1, None):
        attrs = {field: _safeidx(row, idx) for field, idx in zip(fields, indices)}
        try:
            objects.append(model.parse_obj(attrs))
        except ValidationError as ex:
            errors = ex.errors()
            failed = ", ".join(e["loc"][0] for e in errors)
            logger.warn(ex)
            logger.warn(f"ValidationError: {failed} in {attrs}")

    return objects


def _safeidx(lst, i):
    """Devuelve el índice i-ésimo (columna i-ésima)d e una lista (fila).

    Si la lista no tiene el tamaño suficiente, o contiene la cadena vacía,
    se devuelve None.
    """
    return None if i >= len(lst) or lst[i] == "" else lst[i]
