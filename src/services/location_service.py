# location_service.py - Single Responsibility: Handle location detection
from typing import Dict, List, Callable
import geocoder
from ..interfaces import ILocationService

class LocationService(ILocationService):
    """Service for detecting user location"""
    
    def __init__(self):
        self.geocoders: List[Callable] = [
            lambda: geocoder.ip('me'),
            lambda: geocoder.freegeoip('me'),
            lambda: geocoder.ipinfo('me')
        ]
    
    def get_location(self) -> Dict[str, any]:
        """Get location using multiple geocoding services as fallback"""
        location_info = {
            'latitude': None,
            'longitude': None,
            'city': None,
            'country': None
        }
        
        for geocoder_func in self.geocoders:
            try:
                g = geocoder_func()
                if g.ok and g.latlng:
                    location_info = {
                        'latitude': g.latlng[0],
                        'longitude': g.latlng[1],
                        'city': g.city,
                        'country': g.country
                    }
                    print(f"Location found: {g.city}, {g.country}")
                    break
            except Exception as e:
                print(f"Geocoder attempt failed: {e}")
                continue
        
        return location_info
    
    def add_geocoder(self, geocoder_func: Callable):
        """Open/Closed: Add new geocoders without modifying existing code"""
        self.geocoders.append(geocoder_func)
