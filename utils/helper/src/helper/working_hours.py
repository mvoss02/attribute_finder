from datetime import datetime
import pytz


def is_working_hours(timezone_str="UTC"):
    """
    Check if current time is within working hours.
    
    Working hours: 6 AM to 9 PM, Monday through Saturday (excluding Sunday)
    
    Args:
        timezone_str (str): Timezone string (e.g., "UTC", "US/Eastern", "Europe/Berlin")
        
    Returns:
        bool: True if within working hours, False otherwise
    """
    # Get current time in specified timezone
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)
    
    # Check if it's Sunday (weekday() returns 6 for Sunday)
    if now.weekday() == 6:
        return False
    
    # Check if time is between 6 AM and 9 PM
    current_hour = now.hour
    return 6 <= current_hour < 21  # 21 is 9 PM in 24-hour format  