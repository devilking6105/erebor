from sanic import Blueprint, response
from zenpy.lib.api_objects import User

from . import error_response, create_zendesk_ticket

# errors
from . import (MISSING_FIELDS)


support_bp = Blueprint('support')


@support_bp.route('/support', methods=['POST'])
async def zen_support(request):
    if not all(item in list(request.json.keys()) for
               item in ['description', 'email_address', 'name']):
        return error_response([MISSING_FIELDS])
    description = request.json['description']
    email_address = request.json['email_address']
    name = request.json['name']
    subject = request.json.get('subject')
    user_info = {'email_address': email_address}
    create_zendesk_ticket(description, user_info,
                          subject=subject,
                          requester=User(
                              name=name,
                              email=email_address,
                              verified=True
                          ))
    return response.json({'success': 'Ticket submitted'})
