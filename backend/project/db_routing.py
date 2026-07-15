from contextvars import ContextVar


_force_primary_reads: ContextVar[bool] = ContextVar(
    "force_primary_reads",
    default=False,
)


def force_primary_reads() -> None:
    _force_primary_reads.set(True)


def clear_force_primary_reads() -> None:
    _force_primary_reads.set(False)


def should_read_from_primary() -> bool:
    return _force_primary_reads.get()