from datetime import datetime as dt

from sanic import Blueprint, response

from . import (email_pattern, e164_pattern,
               error_response, Email, limiter, authorized, send_sms,
               get_symbol, get_balance, send_push_notification,
               uuid_pattern, DEEPLINK_URL)

# errors
from . import (UNAUTHORIZED, MISSING_FIELDS, UNSUPPORTED_CURRENCY,
               NEGATIVE_AMOUNT, INSUFFICIENT_BALANCE, NO_PUBLIC_KEY,
               INVALID_TRANSACTION_UID, USER_NOT_FOUND, USER_NOT_REGISTERED,
               ALREADY_NOTIFIED)
# sql
from . import (REGISTER_ADDRESS_SQL, SELECT_ADDRESS_SQL,
               CREATE_CONTACT_TRANSACTION_SQL, SELECT_EMAIL_AND_FNAME_SQL,
               SELECT_CONTACT_TRANSACTION_DATA,
               UPDATE_TRANSACTION_CONFIRMATION_SQL,
               SELECT_EMAIL_FROM_USERNAME_OR_PHONE_SQL,
               SELECT_ALL_CONTACT_TRANSACTIONS, SELECT_RECIPIENT_STATUS_SQL,
               SELECT_CONTACT_TRANSACTION_RENOTIFY, SELECT_DEVICE_BY_EMAIL_SQL,
               SELECT_DEVICE_BY_USER_ID_SQL)

transactions_bp = Blueprint('transactions')
supported_currencies = ['ETH', 'BTC', 'BOAR']
token_list = {'BOAR': '0xcba0b17f1afa724d2a19c040d7f90f0468b662ea'}


async def public_key_for_user(recipient, currency, db):
    # Check if user has any registered public keys
    address = await db.fetchrow(SELECT_ADDRESS_SQL, currency, recipient)
    return address


async def record_contact_transaction(transaction, user_id, db):
    # Record transaction in database
    transaction_uid = await db.fetchrow(
        CREATE_CONTACT_TRANSACTION_SQL,
        user_id, transaction['recipient'],
        transaction['currency'], transaction['amount'],
        transaction['transaction_type'])
    return transaction_uid['uid']


async def notify_contact_transaction(transaction, user_id, db):
    """
    Notifies a contact that does not have Hoard about a pending transaction
    sent from a Hoard member.
    """
    user_info = await db.fetchrow(SELECT_EMAIL_AND_FNAME_SQL, user_id)
    recipient = transaction['recipient']
    if email_pattern.match(recipient):
        from_email_address = user_info['email_address']
        from_first_name = user_info['first_name']
        to_email_address = transaction['recipient']
        notify_email = Email(
            to_email_address,
            'contact_transactions',
            to_email_address=to_email_address,
            from_email_address=from_email_address,
            from_first_name=from_first_name,
            amount=transaction['amount'],
            currency=transaction['currency'] if not transaction.get('symbol')
            else transaction['symbol']
        )
        notify_email.send()
        return True
    elif e164_pattern.match(recipient):
        message = (
            "Hello - your contact {}"
            " ({}) at Hoard wishes to send you {} {}").format(
                user_info['first_name'], user_info['email_address'],
                transaction['amount'], transaction['currency']
            )
        # Send SMS to phone number
        send_sms(recipient, message)
        return True
    return False


@transactions_bp.route('/users/<user_uid>/register_address', methods=['POST'])
@limiter.shared_limit('50 per minute', scope='users/user_uid/register_address')
@authorized()
async def register_public_keys(request, user_uid):
    if user_uid != request['session']['user_uid']:
        return error_response([UNAUTHORIZED])
    if request.json.keys() != {'currency', 'address'}:
        return error_response([MISSING_FIELDS])
    currency = request.json['currency']
    if currency not in supported_currencies:
        return error_response([UNSUPPORTED_CURRENCY])
    address = request.json['address']
    user_id = request['session']['user_id']
    await request['db'].execute(REGISTER_ADDRESS_SQL,
                                user_id, currency, address)
    return response.json({'success': ['Address registered']})


@transactions_bp.route('/contacts/transaction/', methods=['POST'])
@authorized()
async def contact_transaction(request):
    transaction = request.json
    if transaction.keys() != {'sender', 'amount',
                              'recipient', 'currency'}:
        return error_response([MISSING_FIELDS])
    recipient = transaction['recipient']
    currency = transaction['currency']
    sender_address = transaction['sender']
    amount = transaction['amount']
    transaction['transaction_type'] = 'send'
    if amount <= 0:
        return error_response([NEGATIVE_AMOUNT])
    symbol = None
    if len(currency) == 42:
        symbol = get_symbol(currency)
        if symbol is None:
            return error_response([UNSUPPORTED_CURRENCY])
        transaction['symbol'] = symbol
        transaction['currency'] = symbol
    elif currency in token_list.keys():
        symbol = currency
        transaction['symbol'] = symbol
        currency = token_list[currency]
    elif currency not in supported_currencies:
        return error_response([UNSUPPORTED_CURRENCY])
    if get_balance(sender_address, currency) < amount:
        return error_response([INSUFFICIENT_BALANCE])
    recipient_public_key = await public_key_for_user(
        recipient,
        currency if not symbol else 'ETH',
        request['db']
    )
    if recipient_public_key is None:
        # Notify via email or SMS
        notified = await notify_contact_transaction(
            transaction, request['session']['user_id'], request['db'])
        if not notified:
            return error_response([NO_PUBLIC_KEY])

        resp = {"success": ["Recipient has been notified of pending "
                            "transaction"]}
    else:
        devices = await request['db'].fetch(
            SELECT_DEVICE_BY_EMAIL_SQL, recipient_public_key['email_address'])
        for device in devices:
            send_push_notification(
                "You received {amount} {currency}".format(
                    amount=amount,
                    currency=symbol if symbol is not None else currency),
                device,
                deep_link=(DEEPLINK_URL))
        resp = {'public_key': recipient_public_key[0]}
    # Record in DB
    transaction_uid = await record_contact_transaction(
        transaction,
        request['session']['user_id'],
        request['db'])
    resp['transaction_uid'] = transaction_uid
    return response.json(resp)


@transactions_bp.route('/contacts/transaction_data/<transaction_uid>',
                       methods=['GET'])
@limiter.shared_limit(
    '50 per minute',
    scope='/contacts/transaction_data/transaction_uid')
@authorized()
async def contact_transaction_data(request, transaction_uid):
    try:
        transaction = await request['db'].fetchrow(
            SELECT_CONTACT_TRANSACTION_DATA, transaction_uid)
    except ValueError:
        return error_response([INVALID_TRANSACTION_UID])
    return (response.json(dict(transaction)) if transaction else
            error_response([INVALID_TRANSACTION_UID]))


@transactions_bp.route('/contacts/transaction_confirmation/<transaction_uid>',
                       methods=['POST'])
@limiter.shared_limit(
    '50 per minute',
    scope='/contacts/transaction_confirmation/transaction_uid')
@authorized()
async def contact_transaction_confirmation(request, transaction_uid):
    if not uuid_pattern.match(transaction_uid):
        return error_response([INVALID_TRANSACTION_UID])
    confirmation = request.json
    if confirmation.keys() != {'confirmed', 'transaction_hash'}:
        return error_response([MISSING_FIELDS])
    confirmation_value = confirmation['confirmed']
    if not isinstance(confirmation_value, bool):
        return error_response([MISSING_FIELDS])
    transaction_hash = confirmation['transaction_hash']
    try:
        updated_trans = await request['db'].fetchrow(
            UPDATE_TRANSACTION_CONFIRMATION_SQL,
            'confirmed' if confirmation_value else 'denied', transaction_hash,
            transaction_uid)
    except ValueError:
        return error_response([INVALID_TRANSACTION_UID])
    finally:
        if not updated_trans:
            return error_response([INVALID_TRANSACTION_UID])
        elif (updated_trans['transaction_type'] == 'request' and
              not confirmation_value):
            devices = await request['db'].fetch(
                SELECT_DEVICE_BY_USER_ID_SQL, updated_trans['user_id']
            )
            message = (
                "{recipient} has declined your "
                "{amount} {currency} request".format(
                    recipient=updated_trans['recipient'],
                    amount=updated_trans['amount'],
                    currency=updated_trans['currency']
                )
            )
            for device in devices:
                send_push_notification(
                    message,
                    device,
                    deep_link=(DEEPLINK_URL))
    return (response.json({'success': 'You have confirmed the transaction'}) if
            confirmation_value else
            response.json({'success': 'You have denied the transaction'}))


@transactions_bp.route('/users/<user_uid>/contact_transactions',
                       methods=['GET'])
@limiter.shared_limit('50 per minute',
                      scope='/users/user_uid/contact_transactions')
@authorized()
async def contact_transaction_by_user(request, user_uid):
    if user_uid != request['session']['user_uid']:
        return error_response([UNAUTHORIZED])
    db = request['db']
    transactions = await db.fetch(SELECT_ALL_CONTACT_TRANSACTIONS,
                                  request['session']['user_id'])
    transactions = [dict(record) for record in transactions]
    return response.json(transactions)


@transactions_bp.route(
    '/contacts/transaction/<transaction_uid>/recipient_status',
    methods=['GET'])
@limiter.shared_limit('50 per minute',
                      scope='/contact/transaction/trans_uid/recipient_status')
@authorized()
async def recipient_status(request, transaction_uid):
    db = request['db']
    try:
        recipient_status = await db.fetchrow(SELECT_RECIPIENT_STATUS_SQL,
                                             transaction_uid)
    except ValueError:
        return error_response([INVALID_TRANSACTION_UID])
    return (response.json(dict(recipient_status)) if recipient_status else
            error_response([USER_NOT_REGISTERED]))


@transactions_bp.route('/contacts/transaction/<transaction_uid>/notify',
                       methods=['POST'])
@limiter.shared_limit('5 per day',
                      scope='/contact/transaction/trans_uid/notify')
@authorized()
async def renotify(request, transaction_uid):
    db = request['db']
    user_id = request['session']['user_id']
    try:
        transaction = await db.fetchrow(
            SELECT_CONTACT_TRANSACTION_RENOTIFY, transaction_uid)
    except ValueError:
        return error_response([INVALID_TRANSACTION_UID])
    if not transaction:
        return error_response([ALREADY_NOTIFIED])
    await notify_contact_transaction(
        dict(transaction), user_id, db)
    # TODO: Include a push notification here
    return response.json({
        'success': ['User has been notified of pending transaction']})


@transactions_bp.route('/request_funds/', methods=['POST'])
@authorized()
async def request_funds(request):
    fund_request = request.json
    if fund_request.keys() != {'recipient', 'email_address',
                               'currency', 'amount'}:
        return error_response([MISSING_FIELDS])
    currency = fund_request['currency']
    amount = fund_request['amount']
    from_email_address = fund_request['email_address']
    recipient = fund_request['recipient']
    request_time = dt.now().strftime('%B %d, %Y - %I:%M%p')
    if not email_pattern.match(recipient):
        user_record = await request['db'].fetchrow(
            SELECT_EMAIL_FROM_USERNAME_OR_PHONE_SQL, recipient)
        if user_record is None:
            return error_response([USER_NOT_FOUND])
        recipient = user_record['email_address']
    devices = await request['db'].fetch(SELECT_DEVICE_BY_EMAIL_SQL,
                                        recipient)
    for device in devices:
        send_push_notification(
            "{} is requesting {} {} from you".format(
                from_email_address, amount, currency),
            device,
            deep_link=(DEEPLINK_URL +
                       'request_funds/?from={}&amount={}&currency={}'.format(
                        from_email_address, amount, currency)))

    request_email = Email(
        recipient,
        'request_funds',
        to_email_address=recipient,
        from_email_address=from_email_address,
        amount=amount,
        currency=currency,
        request_time=request_time
    )
    request_email.send()

    transaction_uid = await record_contact_transaction(
        {
            "recipient": recipient,
            "currency": currency,
            "amount": amount,
            "transaction_type": "request"
        },
        request['session']['user_id'],
        request['db']
    )

    return response.json({"success": ["Email sent notifying recipient"],
                          "transaction_uid": transaction_uid})
