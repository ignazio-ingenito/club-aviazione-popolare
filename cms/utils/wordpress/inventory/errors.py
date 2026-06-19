"""Exceptions raised by the read-only inventory contracts."""


class InventoryContractError(ValueError):
    """Base class for invalid inventory data or unsafe assumptions."""


class CanonicalizationError(InventoryContractError):
    """Raised when a value cannot be represented canonically."""


class PaginationContractError(InventoryContractError):
    """Raised when an API page set is incomplete or internally inconsistent."""
