"""Rate limit por janela deslizante, em memoria.

Simples e sem dependencias externas. Para deploy multi-processo, troque a
implementacao de `_HITS` por Redis mantendo a mesma interface publica.
"""

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

_HITS: Dict[str, Deque[float]] = defaultdict(deque)
_LOCK = threading.Lock()


def check(identity: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
    """Registra um hit e informa se a requisicao e permitida.

    Retorna (permitido, restantes, segundos_para_reset).
    """
    now = time.time()
    with _LOCK:
        bucket = _HITS[identity]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            reset = int(window_seconds - (now - bucket[0])) + 1
            return False, 0, reset
        bucket.append(now)
        return True, max(0, limit - len(bucket)), window_seconds


def reset(identity: str) -> None:
    """Zera o contador de uma identidade (uso administrativo/testes)."""
    with _LOCK:
        _HITS.pop(identity, None)
