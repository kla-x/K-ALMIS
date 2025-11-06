from .schemas.main import UserStatus

ACCESS_TOKEN_EXPIERY = 60

#response params
httponly=True
secure=False
samesite="none"

send_emails = True
sys_logger = True
debugging = True
user_default_pass = "ChangeMeNow"


default_new_user_status= UserStatus.active
default_new_department_status = UserStatus.active
default_role_id= "0a76806dc312733ae4dd271b271048"


KNOWN_DEVICE_MAX_ATTEMPTS = 5
UNKNOWN_DEVICE_MAX_ATTEMPTS = 2

UNLOCK_ACCOUNT_TOKEN_EXPIRY_MINUTES = 60 

TEMP_DISABLE_DURATION_HOURS = 24
FINAL_ATTEMPTS_BEFORE_LOCK = 2
PASSWORD_EXPIRY_DAYS = 90
FRAUD_SCORE_LIMIT = 70
WORKING_HOURS_START = 8
WORKING_HOURS_END = 17
EXPECTED_TIMEZONE = "EAT"
EXPECTED_LANGUAGE = "en"
IP_WHITELIST_THRESHOLD = 2
MFA_CODE_EXPIRY_MINUTES = 20
TEMP_SESSION_TOKEN_EXPIRY_MINUTES = 30
INACTIVE_ACCOUNT_DAYS = 60
MFA_CODE_LENGTH = 6