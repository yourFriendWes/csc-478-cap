import pytest
from app import location

def test_location_returns_hardcoded_value():
    assert location.supported_locations() == [{'country': 'United States'}]
