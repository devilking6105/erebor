# flake-8: noqa
import re
import os

from erebor.errors import (error_response, MISSING_FIELDS, UNAUTHORIZED,  # noqa
                           SMS_VERIFICATION_FAILED, INVALID_CREDENTIALS,
                           INVALID_API_KEY, PASSWORD_TARGET, PASSWORD_CHECK,
                           TICKER_UNAVAILABLE, GENERIC_USER, EXPIRED_TOKEN,
                           INVALID_PLATFORM, RATE_LIMIT_EXCEEDED,
                           INSUFFICIENT_BALANCE, NEGATIVE_AMOUNT,
                           UNSUPPORTED_CURRENCY, INVALID_USERNAME,
                           NO_PUBLIC_KEY, INVALID_EMAIL, USER_NOT_FOUND,
                           USERNAME_EXISTS, EMAIL_ADDRESS_EXISTS,
                           INVALID_TRANSACTION_UID, INVALID_PHONE_NUMBER,
                           INVALID_SWAP_SERVICE, USER_NOT_REGISTERED,
                           ALREADY_NOTIFIED, ALREADY_VOTED, INVALID_ARGS,
                           CURRENCY_ALREADY_SUPPORTED, VOTING_SUSPENDED,
                           CAPTCHA_FAILED, UNSUPPORTED_DEVICE,
                           DEVICE_EXISTS, DEVICE_NOT_FOUND)
from erebor.email import Email  # noqa
from erebor.render import (unsubscribe_template, result_template, # noqa
                           password_template, RESULT_ACTIONS)
from erebor.erebor import authorized, limiter # noqa
from erebor.blockchain import get_symbol, get_balance # noqa
from erebor.utils import fetch, post, send_sms, create_zendesk_ticket, verify # noqa
from erebor.ua import check_channel, send_push_notification  # noqa
from erebor.sql import (CREATE_USER_SQL, SELECT_USER_SQL, UPDATE_USER_SQL,  # noqa
                     ACTIVATE_USER_SQL, PASSWORD_ACCESS_SQL, SET_2FA_CODE_SQL,
                     LOGIN_SQL, VERIFY_SMS_LOGIN, LOGOUT_SQL,
                     SELECT_2FA_SETTINGS_SQL, UPDATE_2FA_SETTINGS_SQL,
                     REGISTER_ADDRESS_SQL, SELECT_ADDRESS_SQL,
                     CREATE_CONTACT_TRANSACTION_SQL,
                     SELECT_EMAIL_AND_FNAME_SQL, SELECT_CONTACT_TRANSACTIONS,
                     SELECT_CONTACT_TRANSACTION_DATA,
                     UPDATE_TRANSACTION_CONFIRMATION_SQL,
                     SELECT_EMAIL_FROM_USERNAME_OR_PHONE_SQL,
                     CHANGE_PASSWORD_SQL, RESET_TOKEN_CREATION_SQL,
                     SELECT_RESET_TOKEN_SQL, EXPIRE_RESET_TOKEN_SQL,
                     SELECT_USERNAME_FNAME_FROM_EMAIL_SQL,
                     SELECT_EMAIL_PREFS_SQL, UPDATE_EMAIL_PREFS_SQL,
                     CREATE_IV_SQL, IV_RESULTS_SQL, SELECT_USER_SQL,
                     SELECT_ALL_CONTACT_TRANSACTIONS,
                     SELECT_CONTACT_TRANSACTION_RENOTIFY,
                     SELECT_RECIPIENT_STATUS_SQL, INSERT_VOTE_SQL,
                     SELECT_ALL_VOTES_SQL, SELECT_ALL_SUPPORTED_COINS_SQL,
                     SELECT_ALL_VOTES_INTERVAL_SQL, PRE_REGISTER_USER_SQL,
                     ACTIVATE_PRE_REG_SQL,
                     SELECT_DEVICE_BY_EMAIL_SQL, REGISTER_DEVICE_SQL,
                     GET_SESSIONS_SQL, DESTROY_SESSIONS_SQL,
                     SELECT_DEVICE_BY_USER_ID_SQL)


DEEPLINK_URL = str(os.environ.get('DEEPLINK_URL'))

email_pattern = re.compile('^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')
username_pattern = re.compile('[^\w]')
hoard_pattern = re.compile('.*hoard.*', flags=re.IGNORECASE)
admin_pattern = re.compile('.*admin.*', flags=re.IGNORECASE)
e164_pattern = re.compile('^\+?[1-9]\d{1,14}$')
uuid_pattern = re.compile(
    '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
