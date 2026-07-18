from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeConfigCheckDTO:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    summary: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.errors
