"""
GeoIP utilities for detecting country and city from IP address.

Uses geoip2 library with free MaxMind GeoLite2 database.

Setup:
1. Install: pip install geoip2
2. Download free GeoLite2 databases from MaxMind:
   https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
3. Set GEOIP_DB_PATH in .env
"""

import os
from typing import Optional, Tuple
from utils.logger import setup_logger

logger = setup_logger(__name__)

try:
    import geoip2.database
    import geoip2.errors
    GEOIP_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ geoip2 not installed. Install with: pip install geoip2")
    GEOIP_AVAILABLE = False


class GeoIPService:
    """GeoIP service for IP geolocation."""

    def __init__(self):
        self.reader = None
        self._init_reader()

    def _init_reader(self):
        """Initialize GeoIP database reader."""
        if not GEOIP_AVAILABLE:
            return

        # Try to find GeoLite2 database
        db_path = os.getenv("GEOIP_DB_PATH")

        if not db_path:
            # Try default locations
            possible_paths = [
                "/usr/share/GeoIP/GeoLite2-City.mmdb",
                "/var/lib/GeoIP/GeoLite2-City.mmdb",
                "./GeoLite2-City.mmdb",
                "./data/GeoLite2-City.mmdb",
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    break

        if db_path and os.path.exists(db_path):
            try:
                self.reader = geoip2.database.Reader(db_path)
                logger.info(f"✅ GeoIP database loaded: {db_path}")
            except Exception as e:
                logger.error(f"❌ Failed to load GeoIP database: {e}")
        else:
            logger.warning(
                "⚠️ GeoIP database not found. Download from:\n"
                "https://dev.maxmind.com/geoip/geolite2-free-geolocation-data"
            )

    def lookup(self, ip_address: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Lookup IP address to get country and city.

        Args:
            ip_address: IP address to lookup

        Returns:
            Tuple of (country_code, city_name) or (None, None) if not found
        """
        if not self.reader:
            return None, None

        # Skip private/local IPs
        if self._is_private_ip(ip_address):
            return None, None

        try:
            response = self.reader.city(ip_address)

            country = response.country.iso_code  # e.g., "US", "GB", "RU"
            city = response.city.name  # e.g., "New York", "London"

            return country, city

        except geoip2.errors.AddressNotFoundError:
            logger.debug(f"IP not found in GeoIP database: {ip_address}")
            return None, None
        except Exception as e:
            logger.error(f"GeoIP lookup error for {ip_address}: {e}")
            return None, None

    def _is_private_ip(self, ip: str) -> bool:
        """
        Check if IP is private/local.

        Args:
            ip: IP address string

        Returns:
            True if private IP
        """
        if not ip or ip == "127.0.0.1" or ip == "localhost":
            return True

        # Check for private IP ranges
        parts = ip.split(".")
        if len(parts) != 4:
            return True

        try:
            first_octet = int(parts[0])
            second_octet = int(parts[1])

            # 10.0.0.0/8
            if first_octet == 10:
                return True

            # 172.16.0.0/12
            if first_octet == 172 and 16 <= second_octet <= 31:
                return True

            # 192.168.0.0/16
            if first_octet == 192 and second_octet == 168:
                return True

            # 169.254.0.0/16 (link-local)
            if first_octet == 169 and second_octet == 254:
                return True

            return False

        except (ValueError, IndexError):
            return True

    def __del__(self):
        """Close database reader on cleanup."""
        if self.reader:
            try:
                self.reader.close()
            except:
                pass


# Global GeoIP service instance
_geoip_service = None


def get_geoip() -> GeoIPService:
    """
    Get global GeoIP service instance (singleton).

    Returns:
        GeoIPService instance
    """
    global _geoip_service
    if _geoip_service is None:
        _geoip_service = GeoIPService()
    return _geoip_service


def get_location_from_ip(ip_address: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Helper function to get location from IP.

    Args:
        ip_address: IP address

    Returns:
        Tuple of (country_code, city_name)
    """
    geoip = get_geoip()
    return geoip.lookup(ip_address)


# Alternative: Using free API (slower, rate-limited)
def get_location_from_ip_api(ip_address: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Get location using free ip-api.com service.

    WARNING: Rate limited to 45 requests per minute.
    Use GeoIP2 database for production.

    Args:
        ip_address: IP address

    Returns:
        Tuple of (country_code, city_name)
    """
    import requests

    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip_address}",
            timeout=2
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                country = data.get("countryCode")
                city = data.get("city")
                return country, city

    except Exception as e:
        logger.error(f"IP API lookup error: {e}")

    return None, None
