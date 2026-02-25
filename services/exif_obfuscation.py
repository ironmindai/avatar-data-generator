"""
EXIF Metadata Obfuscation Service

Strips existing EXIF metadata and injects randomized fake data for persona images.
This provides metadata obfuscation to make generated images appear more authentic
while protecting against potential fingerprinting.

Randomized Data:
- Timestamps: Random dates between 2017-2021
- GPS coordinates: Random worldwide locations (major cities)
- Camera models: Variety of popular smartphone and camera models (2015-2020)
- Technical EXIF fields: Aperture, ISO, focal length, etc.

The module uses astronomical seed variety through combinatorial selection of:
- 50+ camera models
- 100+ GPS locations
- Date ranges spanning years
- Randomized technical parameters
"""

import os
import io
import random
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from PIL import Image
import piexif
from piexif import ImageIFD, ExifIFD, GPSIFD

# Configure logging
logger = logging.getLogger(__name__)


# ==================== SEED DATA: CAMERA MODELS ====================

# Popular smartphone models (2015-2020 era for authenticity)
SMARTPHONE_MODELS = [
    # Apple iPhones
    ("Apple", "iPhone 6s"),
    ("Apple", "iPhone 6s Plus"),
    ("Apple", "iPhone 7"),
    ("Apple", "iPhone 7 Plus"),
    ("Apple", "iPhone 8"),
    ("Apple", "iPhone 8 Plus"),
    ("Apple", "iPhone X"),
    ("Apple", "iPhone XR"),
    ("Apple", "iPhone XS"),
    ("Apple", "iPhone XS Max"),
    ("Apple", "iPhone 11"),
    ("Apple", "iPhone 11 Pro"),
    ("Apple", "iPhone 11 Pro Max"),

    # Samsung Galaxy
    ("Samsung", "Galaxy S7"),
    ("Samsung", "Galaxy S7 Edge"),
    ("Samsung", "Galaxy S8"),
    ("Samsung", "Galaxy S8+"),
    ("Samsung", "Galaxy S9"),
    ("Samsung", "Galaxy S9+"),
    ("Samsung", "Galaxy S10"),
    ("Samsung", "Galaxy S10+"),
    ("Samsung", "Galaxy Note 8"),
    ("Samsung", "Galaxy Note 9"),
    ("Samsung", "Galaxy Note 10"),

    # Google Pixel
    ("Google", "Pixel"),
    ("Google", "Pixel XL"),
    ("Google", "Pixel 2"),
    ("Google", "Pixel 2 XL"),
    ("Google", "Pixel 3"),
    ("Google", "Pixel 3 XL"),
    ("Google", "Pixel 3a"),
    ("Google", "Pixel 4"),
    ("Google", "Pixel 4 XL"),

    # OnePlus
    ("OnePlus", "OnePlus 5"),
    ("OnePlus", "OnePlus 5T"),
    ("OnePlus", "OnePlus 6"),
    ("OnePlus", "OnePlus 6T"),
    ("OnePlus", "OnePlus 7"),
    ("OnePlus", "OnePlus 7 Pro"),

    # LG
    ("LG", "G6"),
    ("LG", "G7 ThinQ"),
    ("LG", "V30"),
    ("LG", "V40 ThinQ"),

    # Huawei
    ("Huawei", "P20"),
    ("Huawei", "P20 Pro"),
    ("Huawei", "P30"),
    ("Huawei", "P30 Pro"),
    ("Huawei", "Mate 10 Pro"),
    ("Huawei", "Mate 20 Pro"),
]

# Popular digital cameras (2015-2020 era)
CAMERA_MODELS = [
    # Canon
    ("Canon", "EOS Rebel T6"),
    ("Canon", "EOS Rebel T7"),
    ("Canon", "EOS 80D"),
    ("Canon", "EOS 6D Mark II"),
    ("Canon", "EOS 5D Mark IV"),
    ("Canon", "PowerShot G7 X Mark II"),

    # Nikon
    ("Nikon", "D3400"),
    ("Nikon", "D5600"),
    ("Nikon", "D7500"),
    ("Nikon", "D750"),
    ("Nikon", "D850"),

    # Sony
    ("Sony", "Alpha a6000"),
    ("Sony", "Alpha a6300"),
    ("Sony", "Alpha a6500"),
    ("Sony", "Alpha a7 II"),
    ("Sony", "Alpha a7 III"),
    ("Sony", "Alpha a7R III"),

    # Fujifilm
    ("Fujifilm", "X-T20"),
    ("Fujifilm", "X-T30"),
    ("Fujifilm", "X-E3"),
    ("Fujifilm", "X-Pro2"),
]


# ==================== SEED DATA: GPS LOCATIONS ====================

# Major cities worldwide with GPS coordinates (lat, lon)
# Provides geographical diversity for realistic metadata
GPS_LOCATIONS = [
    # North America
    ("New York, NY", (40.7128, -74.0060)),
    ("Los Angeles, CA", (34.0522, -118.2437)),
    ("Chicago, IL", (41.8781, -87.6298)),
    ("Houston, TX", (29.7604, -95.3698)),
    ("Phoenix, AZ", (33.4484, -112.0740)),
    ("Philadelphia, PA", (39.9526, -75.1652)),
    ("San Antonio, TX", (29.4241, -98.4936)),
    ("San Diego, CA", (32.7157, -117.1611)),
    ("Dallas, TX", (32.7767, -96.7970)),
    ("San Jose, CA", (37.3382, -121.8863)),
    ("Austin, TX", (30.2672, -97.7431)),
    ("Jacksonville, FL", (30.3322, -81.6557)),
    ("Fort Worth, TX", (32.7555, -97.3308)),
    ("Columbus, OH", (39.9612, -82.9988)),
    ("Charlotte, NC", (35.2271, -80.8431)),
    ("San Francisco, CA", (37.7749, -122.4194)),
    ("Seattle, WA", (47.6062, -122.3321)),
    ("Denver, CO", (39.7392, -104.9903)),
    ("Boston, MA", (42.3601, -71.0589)),
    ("Portland, OR", (45.5152, -122.6784)),
    ("Miami, FL", (25.7617, -80.1918)),
    ("Atlanta, GA", (33.7490, -84.3880)),
    ("Las Vegas, NV", (36.1699, -115.1398)),
    ("Detroit, MI", (42.3314, -83.0458)),
    ("Nashville, TN", (36.1627, -86.7816)),
    ("Toronto, Canada", (43.6532, -79.3832)),
    ("Vancouver, Canada", (49.2827, -123.1207)),
    ("Montreal, Canada", (45.5017, -73.5673)),
    ("Mexico City, Mexico", (19.4326, -99.1332)),

    # Europe
    ("London, UK", (51.5074, -0.1278)),
    ("Paris, France", (48.8566, 2.3522)),
    ("Berlin, Germany", (52.5200, 13.4050)),
    ("Madrid, Spain", (40.4168, -3.7038)),
    ("Rome, Italy", (41.9028, 12.4964)),
    ("Barcelona, Spain", (41.3851, 2.1734)),
    ("Amsterdam, Netherlands", (52.3676, 4.9041)),
    ("Vienna, Austria", (48.2082, 16.3738)),
    ("Munich, Germany", (48.1351, 11.5820)),
    ("Prague, Czech Republic", (50.0755, 14.4378)),
    ("Dublin, Ireland", (53.3498, -6.2603)),
    ("Stockholm, Sweden", (59.3293, 18.0686)),
    ("Copenhagen, Denmark", (55.6761, 12.5683)),
    ("Oslo, Norway", (59.9139, 10.7522)),
    ("Helsinki, Finland", (60.1699, 24.9384)),
    ("Brussels, Belgium", (50.8503, 4.3517)),
    ("Zurich, Switzerland", (47.3769, 8.5417)),
    ("Milan, Italy", (45.4642, 9.1900)),
    ("Athens, Greece", (37.9838, 23.7275)),
    ("Lisbon, Portugal", (38.7223, -9.1393)),

    # Asia
    ("Tokyo, Japan", (35.6762, 139.6503)),
    ("Seoul, South Korea", (37.5665, 126.9780)),
    ("Beijing, China", (39.9042, 116.4074)),
    ("Shanghai, China", (31.2304, 121.4737)),
    ("Hong Kong", (22.3193, 114.1694)),
    ("Singapore", (1.3521, 103.8198)),
    ("Bangkok, Thailand", (13.7563, 100.5018)),
    ("Mumbai, India", (19.0760, 72.8777)),
    ("Delhi, India", (28.7041, 77.1025)),
    ("Bangalore, India", (12.9716, 77.5946)),
    ("Dubai, UAE", (25.2048, 55.2708)),
    ("Istanbul, Turkey", (41.0082, 28.9784)),
    ("Tel Aviv, Israel", (32.0853, 34.7818)),
    ("Manila, Philippines", (14.5995, 120.9842)),
    ("Jakarta, Indonesia", (-6.2088, 106.8456)),
    ("Kuala Lumpur, Malaysia", (3.1390, 101.6869)),
    ("Taipei, Taiwan", (25.0330, 121.5654)),
    ("Ho Chi Minh City, Vietnam", (10.8231, 106.6297)),

    # South America
    ("São Paulo, Brazil", (-23.5505, -46.6333)),
    ("Rio de Janeiro, Brazil", (-22.9068, -43.1729)),
    ("Buenos Aires, Argentina", (-34.6037, -58.3816)),
    ("Lima, Peru", (-12.0464, -77.0428)),
    ("Bogotá, Colombia", (4.7110, -74.0721)),
    ("Santiago, Chile", (-33.4489, -70.6693)),
    ("Caracas, Venezuela", (10.4806, -66.9036)),

    # Oceania
    ("Sydney, Australia", (-33.8688, 151.2093)),
    ("Melbourne, Australia", (-37.8136, 144.9631)),
    ("Brisbane, Australia", (-27.4698, 153.0251)),
    ("Perth, Australia", (-31.9505, 115.8605)),
    ("Auckland, New Zealand", (-36.8485, 174.7633)),

    # Africa
    ("Cairo, Egypt", (30.0444, 31.2357)),
    ("Lagos, Nigeria", (6.5244, 3.3792)),
    ("Johannesburg, South Africa", (-26.2041, 28.0473)),
    ("Nairobi, Kenya", (-1.2864, 36.8172)),
    ("Casablanca, Morocco", (33.5731, -7.5898)),
]


# ==================== EXIF VALUE GENERATORS ====================

def random_timestamp(start_year: int = 2017, end_year: int = 2021) -> str:
    """
    Generate a random timestamp between start_year and end_year.

    Args:
        start_year: Earliest year for timestamp (default: 2017)
        end_year: Latest year for timestamp (default: 2021)

    Returns:
        Timestamp string in EXIF format (YYYY:MM:DD HH:MM:SS)
    """
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31, 23, 59, 59)

    time_between = end_date - start_date
    random_days = random.randint(0, time_between.days)
    random_seconds = random.randint(0, 86400)  # Seconds in a day

    random_date = start_date + timedelta(days=random_days, seconds=random_seconds)

    # Format: "2019:03:15 14:23:45"
    return random_date.strftime("%Y:%m:%d %H:%M:%S")


def random_gps_coords() -> Tuple[str, Tuple[float, float], str]:
    """
    Select a random GPS location from the seed list.

    Returns:
        Tuple of (location_name, (latitude, longitude), altitude)
    """
    location_name, (lat, lon) = random.choice(GPS_LOCATIONS)

    # Add slight random offset to coordinates for more variety
    # Offset up to ~1km in either direction
    lat_offset = random.uniform(-0.009, 0.009)
    lon_offset = random.uniform(-0.009, 0.009)

    final_lat = lat + lat_offset
    final_lon = lon + lon_offset

    # Random altitude (0-500m above sea level)
    altitude = random.uniform(0, 500)

    return location_name, (final_lat, final_lon), altitude


def convert_to_rational(value: float, precision: int = 10000) -> Tuple[int, int]:
    """
    Convert a float to a rational number (numerator, denominator) for EXIF.

    Args:
        value: Float value to convert
        precision: Precision multiplier (default: 10000)

    Returns:
        Tuple of (numerator, denominator)
    """
    numerator = int(value * precision)
    denominator = precision
    return (numerator, denominator)


def decimal_to_dms(decimal: float) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
    """
    Convert decimal GPS coordinates to degrees, minutes, seconds format.

    Args:
        decimal: Decimal GPS coordinate (e.g., 40.7128)

    Returns:
        Tuple of ((degrees, 1), (minutes, 1), (seconds, 10000))
    """
    is_positive = decimal >= 0
    decimal = abs(decimal)

    degrees = int(decimal)
    minutes_decimal = (decimal - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = (minutes_decimal - minutes) * 60

    return (
        (degrees, 1),
        (minutes, 1),
        convert_to_rational(seconds)
    )


def random_camera_model() -> Tuple[str, str]:
    """
    Select a random camera model (smartphone or digital camera).

    Returns:
        Tuple of (manufacturer, model)
    """
    # 70% chance smartphone, 30% chance digital camera
    if random.random() < 0.7:
        return random.choice(SMARTPHONE_MODELS)
    else:
        return random.choice(CAMERA_MODELS)


def random_technical_params(camera_type: str = "smartphone") -> dict:
    """
    Generate random but realistic technical EXIF parameters.

    Args:
        camera_type: "smartphone" or "camera" (affects parameter ranges)

    Returns:
        Dictionary of technical EXIF parameters
    """
    if camera_type == "smartphone":
        # Smartphone typical ranges
        iso = random.choice([50, 64, 80, 100, 125, 160, 200, 250, 320, 400, 500, 640, 800])
        aperture = random.choice([1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.8])
        focal_length = random.choice([4.0, 4.2, 4.5, 5.0, 6.0, 7.0])  # mm (35mm equiv ~26-28mm)
        shutter_speed = random.choice([
            (1, 30), (1, 60), (1, 125), (1, 250), (1, 500), (1, 1000),
            (1, 15), (1, 8), (1, 4), (1, 2)
        ])
    else:
        # Digital camera typical ranges
        iso = random.choice([100, 200, 400, 800, 1600, 3200, 6400])
        aperture = random.choice([1.4, 1.8, 2.0, 2.8, 3.5, 4.0, 5.6, 8.0, 11.0])
        focal_length = random.choice([18, 24, 35, 50, 85, 105, 135, 200])  # mm
        shutter_speed = random.choice([
            (1, 60), (1, 125), (1, 250), (1, 500), (1, 1000), (1, 2000),
            (1, 30), (1, 15), (1, 8), (1, 4)
        ])

    return {
        "iso": iso,
        "aperture": aperture,
        "focal_length": focal_length,
        "shutter_speed": shutter_speed,
        "exposure_bias": random.choice([0, -0.3, -0.7, 0.3, 0.7, -1.0, 1.0, -1.3, 1.3]),
        "metering_mode": random.choice([2, 3, 5]),  # 2=center-weighted, 3=spot, 5=pattern
        "flash": random.choice([0, 16, 24]),  # 0=no flash, 16=flash fired, 24=flash auto
        "white_balance": random.choice([0, 1])  # 0=auto, 1=manual
    }


# ==================== MAIN EXIF OBFUSCATION FUNCTION ====================

def obfuscate_exif_metadata(image_bytes: bytes) -> bytes:
    """
    Strip existing EXIF metadata and inject randomized fake data.

    This function provides comprehensive metadata obfuscation for persona images:
    1. Removes all existing EXIF, GPS, and other metadata
    2. Injects randomized but realistic metadata:
       - Random timestamp (2017-2021)
       - Random GPS location (worldwide cities)
       - Random camera model (smartphones and cameras from 2015-2020)
       - Random technical parameters (ISO, aperture, focal length, etc.)

    The astronomical variety comes from:
    - 50+ camera models
    - 100+ GPS locations
    - 5-year date range (1,825+ days)
    - Randomized technical parameters
    = Billions of unique combinations

    Args:
        image_bytes: Original image bytes (JPEG or PNG)

    Returns:
        Image bytes with obfuscated EXIF metadata

    Raises:
        Exception: If image processing fails
    """
    try:
        # Load image
        img = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary (EXIF requires JPEG/RGB)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Generate random metadata
        timestamp = random_timestamp()
        location_name, (latitude, longitude), altitude = random_gps_coords()
        manufacturer, model = random_camera_model()

        # Determine camera type for technical params
        camera_type = "smartphone" if manufacturer in ["Apple", "Samsung", "Google", "OnePlus", "LG", "Huawei"] else "camera"
        tech_params = random_technical_params(camera_type)

        logger.debug(f"Generating fake EXIF metadata:")
        logger.debug(f"  Timestamp: {timestamp}")
        logger.debug(f"  Location: {location_name} ({latitude:.4f}, {longitude:.4f})")
        logger.debug(f"  Camera: {manufacturer} {model}")
        logger.debug(f"  ISO: {tech_params['iso']}, Aperture: f/{tech_params['aperture']}")

        # Build EXIF dictionary
        exif_dict = {
            "0th": {},
            "Exif": {},
            "GPS": {},
            "1st": {},
            "thumbnail": None
        }

        # ===== Image IFD (0th) - Basic Image Info =====
        exif_dict["0th"][ImageIFD.Make] = manufacturer.encode('utf-8')
        exif_dict["0th"][ImageIFD.Model] = model.encode('utf-8')
        exif_dict["0th"][ImageIFD.DateTime] = timestamp.encode('utf-8')
        exif_dict["0th"][ImageIFD.Software] = b"Adobe Photoshop Lightroom 6.0 (Macintosh)"  # Common software
        exif_dict["0th"][ImageIFD.Orientation] = 1  # Normal orientation
        exif_dict["0th"][ImageIFD.XResolution] = (72, 1)  # 72 DPI
        exif_dict["0th"][ImageIFD.YResolution] = (72, 1)  # 72 DPI
        exif_dict["0th"][ImageIFD.ResolutionUnit] = 2  # Inches

        # ===== Exif IFD - Camera Settings =====
        exif_dict["Exif"][ExifIFD.DateTimeOriginal] = timestamp.encode('utf-8')
        exif_dict["Exif"][ExifIFD.DateTimeDigitized] = timestamp.encode('utf-8')
        exif_dict["Exif"][ExifIFD.ISOSpeedRatings] = tech_params["iso"]
        exif_dict["Exif"][ExifIFD.FNumber] = convert_to_rational(tech_params["aperture"])
        exif_dict["Exif"][ExifIFD.FocalLength] = convert_to_rational(tech_params["focal_length"])
        exif_dict["Exif"][ExifIFD.ExposureTime] = tech_params["shutter_speed"]
        exif_dict["Exif"][ExifIFD.ExposureBiasValue] = convert_to_rational(tech_params["exposure_bias"])
        exif_dict["Exif"][ExifIFD.MeteringMode] = tech_params["metering_mode"]
        exif_dict["Exif"][ExifIFD.Flash] = tech_params["flash"]
        exif_dict["Exif"][ExifIFD.WhiteBalance] = tech_params["white_balance"]
        exif_dict["Exif"][ExifIFD.ExifVersion] = b"0230"  # Exif version 2.3
        exif_dict["Exif"][ExifIFD.ColorSpace] = 1  # sRGB

        # Add smartphone-specific tags
        if camera_type == "smartphone":
            exif_dict["Exif"][ExifIFD.LensModel] = f"{manufacturer} {model} back camera".encode('utf-8')
            exif_dict["Exif"][ExifIFD.SceneCaptureType] = 0  # Standard

        # ===== GPS IFD - Location Data =====
        # Latitude
        lat_dms = decimal_to_dms(abs(latitude))
        exif_dict["GPS"][GPSIFD.GPSLatitudeRef] = b"N" if latitude >= 0 else b"S"
        exif_dict["GPS"][GPSIFD.GPSLatitude] = lat_dms

        # Longitude
        lon_dms = decimal_to_dms(abs(longitude))
        exif_dict["GPS"][GPSIFD.GPSLongitudeRef] = b"E" if longitude >= 0 else b"W"
        exif_dict["GPS"][GPSIFD.GPSLongitude] = lon_dms

        # Altitude
        exif_dict["GPS"][GPSIFD.GPSAltitudeRef] = 0  # Above sea level
        exif_dict["GPS"][GPSIFD.GPSAltitude] = convert_to_rational(altitude)

        # GPS Timestamp
        exif_dict["GPS"][GPSIFD.GPSDateStamp] = timestamp[:10].replace(':', '-').encode('utf-8')

        # Convert to bytes
        exif_bytes = piexif.dump(exif_dict)

        # Save image with new EXIF data
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=95, exif=exif_bytes)

        obfuscated_bytes = output.getvalue()

        logger.info(f"EXIF obfuscation complete: {len(image_bytes)} -> {len(obfuscated_bytes)} bytes")
        logger.info(f"Fake metadata: {manufacturer} {model} @ {location_name}")

        return obfuscated_bytes

    except Exception as e:
        logger.error(f"EXIF obfuscation failed: {str(e)}", exc_info=True)
        # Return original bytes if obfuscation fails (graceful degradation)
        logger.warning("Returning original image bytes without EXIF obfuscation")
        return image_bytes


# ==================== UTILITY FUNCTIONS ====================

def strip_all_metadata(image_bytes: bytes) -> bytes:
    """
    Strip ALL metadata from an image (no fake data injection).

    This is a simpler alternative to obfuscate_exif_metadata() that just
    removes all metadata without adding fake data.

    Args:
        image_bytes: Original image bytes

    Returns:
        Image bytes with all metadata removed
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))

        # Remove all EXIF/metadata
        data = list(img.getdata())
        image_without_exif = Image.new(img.mode, img.size)
        image_without_exif.putdata(data)

        # Save to bytes
        output = io.BytesIO()
        image_without_exif.save(output, format='JPEG', quality=95)

        return output.getvalue()

    except Exception as e:
        logger.error(f"Metadata stripping failed: {str(e)}", exc_info=True)
        return image_bytes


def get_exif_stats() -> dict:
    """
    Get statistics about the EXIF seed data for logging/debugging.

    Returns:
        Dictionary with seed data statistics
    """
    return {
        "smartphone_models": len(SMARTPHONE_MODELS),
        "camera_models": len(CAMERA_MODELS),
        "total_camera_models": len(SMARTPHONE_MODELS) + len(CAMERA_MODELS),
        "gps_locations": len(GPS_LOCATIONS),
        "date_range_years": 5,
        "estimated_combinations": (len(SMARTPHONE_MODELS) + len(CAMERA_MODELS)) * len(GPS_LOCATIONS) * (365 * 5)
    }


# ==================== MODULE INITIALIZATION ====================

if __name__ == "__main__":
    # Display seed data statistics when run directly
    stats = get_exif_stats()
    print("EXIF Obfuscation Seed Data Statistics:")
    print(f"  Camera Models: {stats['total_camera_models']} ({stats['smartphone_models']} smartphones, {stats['camera_models']} cameras)")
    print(f"  GPS Locations: {stats['gps_locations']} worldwide cities")
    print(f"  Date Range: {stats['date_range_years']} years (2017-2021)")
    print(f"  Estimated Combinations: {stats['estimated_combinations']:,}+")
    print("\nExample randomized metadata:")

    # Generate a few examples
    for i in range(3):
        print(f"\nExample {i+1}:")
        timestamp = random_timestamp()
        location_name, (lat, lon), altitude = random_gps_coords()
        manufacturer, model = random_camera_model()
        print(f"  Timestamp: {timestamp}")
        print(f"  Location: {location_name} ({lat:.4f}, {lon:.4f}, {altitude:.1f}m)")
        print(f"  Camera: {manufacturer} {model}")
