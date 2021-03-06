### Authentication

Most endpoints require authentication. To authenticate a request, you can
obtain a session_id HttpOnly cookie by creating a new user via the /users/
endpoint, or using the /login/ endpoint.

### Users

#### /users/

POST:
  - first_name
  - last_name
  - phone_number
  - email_address
  - username
  - password
  - device_info (dict containing device_type and channel)
      - device_type (either ios or android)
      - channel (the channel id provided by UA)

  Response: {'uid': UUID,
             'email_address': STRING,
             'username': STRING,
             'first_name': STRING,
             'last_name': STRING,
             'phone_number': STRING}
  Response Cookie: session_id

#### /users/{uid}/

UPDATE:
  - first_name
  - last_name
  - phone_number
  - email_address
  - username

 GET:
  {'uid': UUID,
   'first_name': STRING,
   'last_name': STRING,
   'phone_number': STRING,
   'email_address': STRING,
   'username': STRING}

#### /activate/{activation_key}

GET
  HTML Response: 200 OK, HTML template

  OR if account is active OR token is invalid

  Response: 403

#### /change_password/

POST:
  - password
  - username_or_email
  - new_password

  Response: 200 OK, empty body

#### /password/

POST:
  - email_address

  Response: {'success': ['If our records match you will receive an email']}

#### /reset_password/{token}/

GET:

  HTML Response: 200 OK, form template

POST:
  - new_password

  Response: {'success': ['Your password has been changed']}

#### /logout/

POST (empty body)

  Response: {'success': ['Your session has been invalidated']}

#### /destroy_sessions/

POST (empty body)

  Response: {'success': ['Your sessions across all devices have been invalidated']}

#### /login/

POST:
  - username_or_email
  - password
  - device_info (dict containing device_type and channel)
      - device_type (either ios or android)
      - channel (the channel id provided by UA)

  Response: {'success': ['Login successful']}
  Response Cookie: session_id

    OR if 2fa is enabled

  Response: {'success': ['2FA has been sent']}

#### /2fa/sms_login/

POST:
  - username_or_email
  - sms_verification

  Response: {'success': ['Login successful']}
  Response Cookie: session_id

#### /2fa/settings/

PUT:
  - sms_2fa_enabled

  Response: 200 OK, empty body

GET:

  Response: {'sms_2fa_enabled': BOOL}

#### /request_funds/

POST:
  - recipient (can be a valid email address, username, or or E164 format phone number)
  - email_address (the email address of the sender)
  - currency
  - amount

  Response: {"success": ["Email sent notifying recipient"]}

#### /email_preferences/

PUT:
  - receive_emails_enabled

  Response: 200 OK, empty body

GET:

  Response: {'receive_emails_enabled': BOOL}

#### /users/{user_uid}/register_address/

POST:
  - currency
  - address

  Response: {'success': ['Address registered']}

#### /contacts/transaction/

POST:
  - sender (the public address of the sender)
  - recipient (can be a valid email address, username, or E164 format phone number)
  - currency
  - amount

  Response: {"success": ["Email sent notifying recipient"]}

    OR if they are a user and have a registered public key for the currency

  Response: {'public_key': recipient_public_key}

#### /contacts/transaction_data/{transaction_uid}

GET:
  {'to_email_address': STRING,
   'currency': STRING,
   'amount': FLOAT,
   'created': INTEGER (EPOCH timestamp)}

#### /contacts/transaction_confirmation/{transaction_uid}

POST:
  - confirmed (BOOLEAN)

  Response: {"success": "You have confirmed the transaction"}

  OR if confirmed is FALSE

  Response: {"success": "You have denied the transaction"}

### KYC/AML/Identity Verification

#### /ca_search/

Bridge to POST/GET /searches on Comply Advantage API

POST:
  - see Comply Advantage documentation

  Response: 200 OK, body according to Comply Advantage documentation

GET:

  Response: 200 OK, body according to Comply Advantage documentation

#### /ca_search/{search_id}/

Bridge to GET /searches/{search_id}/ on Comply Advantage API

GET:

  Response: 200 OK, body according to Comply Advantage documentation

#### /jumio_results/{scan_reference}/

GET:

  Response: {'results': [LIST OF JUMIO RESULTS]}

### Ticker

#### /ticker/

GET:

  Response {'btc_usd': USD Currency,
            'eth_usd': USD Currency}

### Updates

#### /updates/{platform}/

A continually updated list of app updates, along with the criticality for
updating each version. The versions here correspond to mobile app versions.
The status is either 'critical', or 'normal'. If the user is using a version of
the app marked as 'critical', the mobile app should cease operating until the
user makes the update. If the current version is not listed, it is considered
the latest version.

The platform contained in the URI will either be 'ios' or 'android', and the
response is particular to the platform submitted.

GET:

  Response {'1.0.0': 'critical',
            '1.0.1': 'critical',
            '1.1.0': 'critical',
            '1.1.1': 'normal',
            '1.2.0': 'normal',
            '2.0.0': 'normal'}

### Support

#### /support/

POST:
  - email_address
  - name
  - description
  - subject (optional)

  Response: {"success": ["Ticket submitted"]}

### JSON RPC Bitcoind Bridge

#### /jsonrpc/

POST:

  JSON-RPC Payload (https://bitcoin.org/en/developer-reference#remote-procedure-calls-rpcs)

  Response {'error': ERROR
            'id': SUBMITTED ID
            'result': [RESULTS]}
