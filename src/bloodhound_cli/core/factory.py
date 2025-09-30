"""
Factory for creating BloodHound clients
"""
from typing import Union
from .base import BloodHoundClient
from .legacy import BloodHoundLegacyClient
from .ce import BloodHoundCEClient


def create_bloodhound_client(edition: str, **kwargs) -> BloodHoundClient:
    """
    Factory function to create the appropriate BloodHound client
    
    Args:
        edition: 'legacy' or 'ce'
        **kwargs: Client-specific parameters
    
    Returns:
        BloodHoundClient instance
    """
    if edition.lower() == 'legacy':
        return BloodHoundLegacyClient(**kwargs)
    elif edition.lower() == 'ce':
        return BloodHoundCEClient(**kwargs)
    else:
        raise ValueError(f"Unsupported edition: {edition}. Use 'legacy' or 'ce'")
