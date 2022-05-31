from flask import Blueprint, request, make_response
from google.cloud import datastore
import json
from json2html import json2html
from constants import *
from common_functions import get_entity, is_nonexistent, valid, \
    response_object, all_exists_in, one_exists_in, new_user

client = datastore.Client()
bp = Blueprint('user', __name__, url_prefix='/users')


@bp.route('', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def get_post_user():
    if request.method == 'GET':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        query = client.query(kind=USER)
        res = list(query.fetch())
        for e in res:
            e['id'] = e.key.id
        return json.dumps(res), 200

    elif request.method == 'POST':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415

        content = request.get_json()
        if all_exists_in(['username', 'email'], content):
            for prop in content:
                if not valid(prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400

            if AJSON in request.accept_mimetypes:
                user = new_user(datastore, client, content)
                return response_object(make_response(json.dumps(user)), AJSON, 201)
            elif HTML in request.accept_mimetypes:
                user = new_user(datastore, client, content)
                return response_object(make_response(json2html.convert(json=json.dumps(user))), HTML, 201)
            else:
                return {'Error': BAD_RES}, 406

        else:
            return {'Error': MISSING_ATTR}, 400

    elif request.method == 'PUT':
        return {'Error': NOT_SUPPORTED + 'PUT'}, 405

    elif request.method == 'PATCH':
        return {'Error': NOT_SUPPORTED + 'PATCH'}, 405

    elif request.method == 'DELETE':
        return {'Error': NOT_SUPPORTED + 'DELETE'}, 405

    else:
        return {'Error': NOT_ACCEPTABLE}, 406


@bp.route('/<pid>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def get_put_patch_delete_user(pid):
    if request.method == 'GET':
        user = get_entity(client, USER, pid)
        if is_nonexistent(user):
            return {'Error': NO_USER}, 404
        user['id'] = user.key.id

        if AJSON in request.accept_mimetypes:
            return response_object(make_response(json.dumps(user)), AJSON, 200)
        elif HTML in request.accept_mimetypes:
            return response_object(make_response(json2html.convert(json=json.dumps(user))), HTML, 200)
        else:
            return {'Error': BAD_RES}, 406

    elif request.method == 'POST':
        return {'Error': NOT_SUPPORTED + 'POST'}, 405

    elif request.method == 'PATCH':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        content = request.get_json()
        if 'id' in content or 'self' in content:
            return {'Error': NO_EDIT}, 403

        if one_exists_in(['username', 'email'], content):
            user = get_entity(client, USER, pid)
            if is_nonexistent(user):
                return NO_USER, 404
            for prop in content:
                if not valid(prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400
                user[prop] = content[prop]
            if AJSON in request.accept_mimetypes:
                res = response_object(make_response(json.dumps(user)), AJSON, 200)
            elif HTML in request.accept_mimetypes:
                res = response_object(make_response(json2html.convert(json=json.dumps(user))), HTML, 200)
            else:
                return {'Error': BAD_RES}, 406
            client.put(user)
            return res

    elif request.method == 'PUT':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        content = request.get_json()
        if 'id' in content or 'self' in content:
            return {'Error': NO_EDIT}, 403

        if one_exists_in(['username', 'email'], content):
            user = get_entity(client, USER, pid)
            if user is None:
                return NO_USER, 404
            for prop in content:
                if not valid(prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400
                user[prop] = content[prop]
            msg = {'Message': 'Boat successfully edited: see location header.'}
            if AJSON in request.accept_mimetypes:
                res = response_object(make_response(json.dumps(msg)), AJSON, 303)
            elif HTML in request.accept_mimetypes:
                res = response_object(make_response(json2html.convert(json=json.dumps(msg))), HTML, 303)
            else:
                return {'Error': BAD_RES}, 406
            client.put(user)
            return res
        else:
            return {'Error': MISSING_ATTR}, 400

    elif request.method == 'DELETE':
        user = get_entity(client, USER, pid)
        if is_nonexistent(user):
            return {'Error': NO_USER}, 404
        client.delete(client.key(USER, int(pid)))
        return '', 204

    else:
        return {'Error': NOT_ACCEPTABLE}, 406
