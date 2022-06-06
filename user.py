from flask import Blueprint, request
from common_functions import *
from google.cloud import datastore


client = datastore.Client()
bp = Blueprint('user', __name__, url_prefix='/users')


@bp.route('', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def get_user_collection():
    if request.method == 'GET':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        query = client.query(kind=USER)
        res = list(query.fetch())
        for e in res:
            e['id'] = e.key.id
        if AJSON in request.accept_mimetypes:
            return json.dumps(res), 200
        return {'Error': BAD_RES}, 406

    elif request.method == 'POST':
        return {'Error': NOT_SUPPORTED + 'POST'}, 405

    elif request.method == 'PUT':
        return {'Error': NOT_SUPPORTED + 'PUT'}, 405

    elif request.method == 'PATCH':
        return {'Error': NOT_SUPPORTED + 'PATCH'}, 405

    elif request.method == 'DELETE':
        return {'Error': NOT_SUPPORTED + 'DELETE'}, 405

    else:
        return {'Error': NOT_ACCEPTABLE}, 406
