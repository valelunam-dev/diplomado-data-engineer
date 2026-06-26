import logging
import re

log = logging.getLogger('demo')
log.setLevel(logging.INFO)
h = logging.StreamHandler()
h.setFormatter(logging.Formatter('%(levelname)s | %(message)s'))
log.addHandler(h)

class SanitizeFilter(logging.Filter):
    """Reemplaza patrones sensibles antes de loggear."""
    PATTERNS = [
        (re.compile(r'password=\S+', re.I), 'password=***'),                # password=cualquier-cosa -> password=***
        (re.compile(r'\b[A-Z0-9]{20,}\b'), '***KEY***'),                    # bloques largos en MAYUS+digitos = AWS access keys
        (re.compile(r'\d{1,2}[.-]\d{3}[.-]\d{3}[-]?\w'), '***RUT***'),      # formato RUT chileno: 12.345.678-9
    ]

    def filter(self, record):
        msg = record.getMessage()                  # obtiene el mensaje ya con args interpolados
        for pat, repl in self.PATTERNS:
            msg = pat.sub(repl, msg)                # reemplaza cada patron por su mascara
        record.msg = msg                            # sobreescribe el mensaje en el record
        record.args = ()                            # limpia args (ya estan dentro de msg)
        return True                                 # deja pasar el record

log.addFilter(SanitizeFilter())

log.info('Conectando con password=supersecreto123')
log.info('AWS_KEY=AKIAIOSFODNN7EXAMPLE en uso')
log.info('Usuario con RUT 12.345.678-9 procesado') 

