"""
Amazon XLSX import package.

Public surface: AmazonXLSXParser only.
All sheet handler classes are internal implementation details (prefixed with _).
"""

from ._parser import AmazonXLSXParser

__all__ = ["AmazonXLSXParser"]
