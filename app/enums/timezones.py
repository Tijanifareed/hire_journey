from enum import Enum
class TimezoneEnum(str, Enum):
    WAT = "Africa/Lagos"          # West Africa Time
    CAT = "Africa/Harare"         # Central Africa Time
    EAT = "Africa/Nairobi"        # East Africa Time
    SAST = "Africa/Johannesburg"  # South Africa Standard Time

    GMT = "Europe/London"         # Greenwich Mean Time
    CET = "Europe/Berlin"         # Central European Time
    CEST = "Europe/Berlin"        # Central European Summer Time
    EET = "Europe/Athens"         # Eastern European Time
    EEST = "Europe/Athens"        # Eastern European Summer Time
    MSK = "Europe/Moscow"         # Moscow Standard Time

    UTC = "UTC"                   # Coordinated Universal Time

    AST = "America/Halifax"       # Atlantic Standard Time
    ADT = "America/Halifax"       # Atlantic Daylight Time
    EST = "America/New_York"      # Eastern Standard Time
    EDT = "America/New_York"      # Eastern Daylight Time
    CST = "America/Chicago"       # Central Standard Time
    CDT = "America/Chicago"       # Central Daylight Time
    MST = "America/Denver"        # Mountain Standard Time
    MDT = "America/Denver"        # Mountain Daylight Time
    PST = "America/Los_Angeles"   # Pacific Standard Time
    PDT = "America/Los_Angeles"   # Pacific Daylight Time
    AKST = "America/Anchorage"    # Alaska Standard Time
    AKDT = "America/Anchorage"    # Alaska Daylight Time
    HST = "Pacific/Honolulu"      # Hawaii Standard Time

    IST = "Asia/Kolkata"          # India Standard Time
    PKT = "Asia/Karachi"          # Pakistan Standard Time
    BST = "Asia/Dhaka"            # Bangladesh Standard Time
    MMT = "Asia/Yangon"           # Myanmar Time
    ICT = "Asia/Bangkok"          # Indochina Time
    WIB = "Asia/Jakarta"          # Western Indonesia Time
    WITA = "Asia/Makassar"        # Central Indonesia Time
    WIT = "Asia/Jayapura"         # Eastern Indonesia Time

    CST_CHINA = "Asia/Shanghai"   # China Standard Time
    HKT = "Asia/Hong_Kong"        # Hong Kong Time
    SGT = "Asia/Singapore"        # Singapore Time
    JST = "Asia/Tokyo"            # Japan Standard Time
    KST = "Asia/Seoul"            # Korea Standard Time

    AFT = "Asia/Kabul"            # Afghanistan Time
    IRST = "Asia/Tehran"          # Iran Standard Time
    GST = "Asia/Dubai"            # Gulf Standard Time
    AST_ARABIA = "Asia/Riyadh"    # Arabia Standard Time

    AEST = "Australia/Sydney"     # Australian Eastern Standard Time
    AEDT = "Australia/Sydney"     # Australian Eastern Daylight Time
    ACST = "Australia/Adelaide"   # Australian Central Standard Time
    ACDT = "Australia/Adelaide"   # Australian Central Daylight Time
    AWST = "Australia/Perth"      # Australian Western Standard Time

    NZST = "Pacific/Auckland"     # New Zealand Standard Time
    NZDT = "Pacific/Auckland"     # New Zealand Daylight Time
    CHAST = "Pacific/Chatham"     # Chatham Standard Time

    # Some extras for completeness
    ART = "America/Argentina/Buenos_Aires"  # Argentina Time
    BRT = "America/Sao_Paulo"               # Brasilia Time
    CLT = "America/Santiago"                # Chile Standard Time
    GYT = "America/Guyana"                  # Guyana Time
