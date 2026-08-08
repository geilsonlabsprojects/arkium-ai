"""Coleta de metricas do sistema (CPU, RAM, disco)."""

from pathlib import Path

import psutil

from app.core.config import BASE_DIR


def system_stats() -> dict:
    """Snapshot dos recursos da maquina que hospeda a plataforma."""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(str(Path(BASE_DIR).anchor or BASE_DIR))
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": memory.percent,
        "memory_used_mb": round(memory.used / 1024 / 1024, 1),
        "memory_total_mb": round(memory.total / 1024 / 1024, 1),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
        "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
    }
