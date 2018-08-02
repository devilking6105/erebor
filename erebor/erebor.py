from functools import wraps
import json
import os
import logging

import requests
import boto3
from sanic import Sanic, response
from sanic.log import LOGGING_CONFIG_DEFAULTS
from sanic_cors import CORS
from sanic_limiter import Limiter, get_remote_address, RateLimitExceeded
from botocore.exceptions import ClientError

from erebor.errors import (error_response, UNAUTHORIZED,
                           INVALID_API_KEY,
                           RATE_LIMIT_EXCEEDED)
from erebor.logs import logging_config
from erebor.sql import USER_ID_SQL


app = Sanic(log_config=logging_config
            if not os.getenv('erebor_test') else LOGGING_CONFIG_DEFAULTS)
CORS(app, automatic_options=True)

limiter = Limiter(app,
                  global_limits=['50 per minute'],
                  key_func=get_remote_address)


def authorized():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            db = request.app.pg
            cookie = request.cookies.get('session_id')
            if cookie:
                user_ids = await db.fetchrow(USER_ID_SQL, cookie)
                if user_ids is not None:
                    request['session'] = {'user_id': user_ids['id'],
                                          'user_uid': user_ids['uid']}
                    request['db'] = request.app.pg
                    res = await f(request, *args, **kwargs)
                    return res
                else:
                    error_response([INVALID_API_KEY])
            return error_response([UNAUTHORIZED])
        return decorated_function
    return decorator


@app.exception(RateLimitExceeded)
def handle_429(request, exception):
    return error_response([RATE_LIMIT_EXCEEDED])


# REMOVE
@app.route('/jsonrpc', methods=['POST'])
@authorized()
async def json_rpc_bridge(request):
    url = "http://hoard:bombadil@shenron.hoardinvest.com:8332"
    headers = {'content-type': 'application/json'}
    payload = request.json
    rpc_response = requests.post(
        url, data=json.dumps(payload), headers=headers)
    return response.json(rpc_response.json())


def load_aws_secret(secret_name):
    secret = None
    endpoint_url = "https://secretsmanager.us-east-2.amazonaws.com"
    region_name = "us-east-2"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
        endpoint_url=endpoint_url
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("The requested secret " + secret_name + " was not found")
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            print("The request was invalid due to:", e)
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            print("The request had invalid params:", e)
    else:
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
    return json.loads(secret)


def load_env(app):
    zd_credentials = {
        'email': os.environ.get('ZD_EMAIL'),
        'token': os.environ.get('ZD_TOKEN'),
        'subdomain': os.environ.get('ZD_SUBDOMAIN')
    }
    twilio_credentials = {
        'account_sid': os.environ.get('TWILIO_ACCOUNT_SID'),
        'auth_token': os.environ.get('TWILIO_AUTH_TOKEN'),
        'twilio_number': os.environ.get('TWILIO_NUMBER')
    }
    logging.debug("Loading Zendesk credentials...")
    app.config.ZD_CREDENTIALS = (zd_credentials if all(zd_credentials.items())
                                 else None)
    logging.debug("Zendesk credentials: {}".format(
        'LOADED' if app.config.ZD_CREDENTIALS else 'ERROR'))

    logging.debug("Loading Twilio credentials...")
    app.config.TWILIO_CREDENTIALS = (twilio_credentials if
                                     all(twilio_credentials.items()) else None)
    logging.debug("Twilio credentials: {}".format(
        'LOADED' if app.config.TWILIO_CREDENTIALS else 'ERROR'))


if __name__ == '__main__':
    secret_name = os.environ['EREBOR_DB_AWS_SECRET']

    if secret_name:
        from erebor.db import db_bp
        secret = load_aws_secret(secret_name)
        app.db = dict(database=secret['dbname'],
                      user=secret['username'],
                      password=secret['password'],
                      host=secret['host'],
                      port=secret['port'])
        app.blueprint(db_bp)
    else:
        raise Exception("Missing database credentials")

    load_env(app)
    from erebor.api.users import users_bp
    from erebor.api.transactions import transactions_bp
    from erebor.api.support import support_bp
    from erebor.api.misc import misc_bp
    from erebor.api.prices import prices_bp
    app.blueprint(users_bp)
    app.blueprint(transactions_bp)
    app.blueprint(support_bp)
    app.blueprint(misc_bp)
    app.blueprint(prices_bp)
    app.run(host='0.0.0.0',
            port=8000,
            access_log=False if os.environ.get('EREBOR_ENV') == 'PROD'
            else True)
