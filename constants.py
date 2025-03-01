# Conversation states
MESSAGE, DATE_TYPE, DATE, TIME, CUSTOM_DAYS = range(5)

# Task type constants
ONE_TIME = 'one_time'
DAILY = 'daily'

# Day name mappings
DAY_NAMES = {
    'Mo': 'Monday', 
    'Tu': 'Tuesday', 
    'We': 'Wednesday',
    'Th': 'Thursday', 
    'Fr': 'Friday', 
    'Sa': 'Saturday', 
    'Su': 'Sunday'
}

# Valid day codes
VALID_DAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']

# Weekday mapping (for reminder checking)
WEEKDAY_MAP = {0: 'Mo', 1: 'Tu', 2: 'We', 3: 'Th', 4: 'Fr', 5: 'Sa', 6: 'Su'}