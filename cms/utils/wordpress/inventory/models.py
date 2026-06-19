"""Compatibility imports for inventory model classes."""

from .manifest import InventoryManifest
from .records import InventoryIssue, ManifestRecord

__all__ = ["InventoryIssue", "InventoryManifest", "ManifestRecord"]
