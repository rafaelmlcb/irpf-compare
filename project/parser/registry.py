from typing import Dict, Optional
from project.parser.fixed_width import RecordSpec
from project.parser.layouts.specs import LAYOUTS

class LayoutRegistry:
    """
    Registry for record layouts (specs).
    Preloaded with default specifications for DIRPF registers.
    Allows dynamic registration of new layouts.
    """
    def __init__(self) -> None:
        self._registry: Dict[str, RecordSpec] = dict(LAYOUTS)

    def register(self, spec: RecordSpec) -> None:
        """
        Registers a new RecordSpec.
        """
        self._registry[spec.record_type] = spec

    def get(self, record_type: str) -> Optional[RecordSpec]:
        """
        Gets a registered RecordSpec by its record_type.
        """
        return self._registry.get(record_type)

    def has(self, record_type: str) -> bool:
        """
        Checks if a record_type is registered.
        """
        return record_type in self._registry

    def list_registered_types(self) -> list[str]:
        """
        Returns a list of all registered record types.
        """
        return list(self._registry.keys())
