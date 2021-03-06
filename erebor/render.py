from jinja2 import Environment, PackageLoader, select_autoescape


jinja_env = Environment(
    loader=PackageLoader('erebor', 'templates'),
    autoescape=select_autoescape(['html'])
)

unsubscribe_template = jinja_env.get_template('unsubscribe.html')
signup_email_template = jinja_env.get_template('emails/signup_email.html')
activated_email_template = jinja_env.get_template(
    'emails/activated_email.html')
result_template = jinja_env.get_template('result.html')
password_template = jinja_env.get_template('password.html')
reset_password_email_template = jinja_env.get_template(
    'emails/reset_password_email.html')
contact_transaction_email_template = jinja_env.get_template(
    'emails/contact_transaction_email.html')
pending_transactions_email = jinja_env.get_template(
    'emails/pending_transactions_email.html')
request_funds_email_template = jinja_env.get_template(
    'emails/request_funds_email.html'
)
forgot_username_template = jinja_env.get_template(
    'emails/forgot_username_email.html'
)
pre_register_email_template = jinja_env.get_template(
    'emails/pre_register_email.html'
)
activate_pre_register_email_template = jinja_env.get_template(
    'emails/activate_pre_register_email.html'
)

RESULT_ACTIONS = {
    'unsubscribe': {
        'true': 'You will no longer receive emails from Hoard.',
        'false': 'You are still set to receive emails from Hoard.'
    },
    'change_password': {
        'true': 'Your password has been changed!',
        'false': ('There was an error handling the request\n'
                  'Your password has not bee changed')
    },
    'activate': {
        'true': ('Your account is now active!\n'
                 'You can now log in with your credentials'),
        'false': ''
    },
    'pre_reg_activate': {
        'true': ('Your username is now reserved!\n'),
        'false': ''
    }
}
