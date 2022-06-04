from flask import Blueprint, request, make_response
from google.cloud import datastore
import json
from constants import *
from common_functions import get_entity, is_nonexistent, valid, \
    response_object, some_exists
from auth import verify_jwt


client = datastore.Client()
bp = Blueprint('user', __name__, url_prefix='/users')


@bp.route('', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def get_post_user():
    if request.method == 'GET':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        query = client.query(kind=USER)
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit=q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + '?limit=' + str(
                q_limit) + '&offset=' + str(next_offset)
        else:
            next_url = None
        for e in results:
            e['id'] = e.key.id
        output = {'users': results}
        if next_url:
            output['next'] = next_url
        return json.dumps(output), 200

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


@bp.route('/<uid>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def get_put_patch_delete_user(pid):
    if request.method == 'GET':
        user = get_entity(USER, pid)
        if is_nonexistent(user):
            return {'Error': NO_USER}, 404
        user['id'] = user.key.id
        if AJSON in request.accept_mimetypes:
            return response_object(make_response(json.dumps(user)), AJSON, 200)
        else:
            return {'Error': BAD_RES}, 406

    elif request.method == 'POST':
        return {'Error': NOT_SUPPORTED + 'POST'}, 405

    elif request.method == 'PATCH':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        payload = verify_jwt(request)
        content = request.get_json()
        if 'id' in content or 'self' in content or 'packages' in content:
            return {'Error': NO_EDIT}, 403
        if some_exists(['username', 'email', 'address'], content):
            user = get_entity(USER, pid)
            if is_nonexistent(user):
                return NO_USER, 404
            if str(user['sub']) != str(payload['sub']):
                return {'Error': 'JWT DOES NOT MATCH'}, 406     ##########
            for prop in content:
                if not valid(prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400
                user[prop] = content[prop]
            if AJSON in request.accept_mimetypes:
                res = response_object(make_response(json.dumps(user)), AJSON, 200)
            else:
                return {'Error': BAD_RES}, 406
            client.put(user)
            return res

    elif request.method == 'PUT':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        payload = verify_jwt(request)
        content = request.get_json()
        if 'id' in content or 'self' in content or 'packages' in content:
            return {'Error': NO_EDIT}, 403
        if some_exists(['username', 'email', 'address'], content):
            user = get_entity(USER, pid)
            if user is None:
                return NO_USER, 404
            if str(user['sub']) != str(payload['sub']):
                return {'Error': 'JWT DOES NOT MATCH'}, 406     ##########
            for prop in content:
                if not valid(prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400
                user[prop] = content[prop]
            msg = {'Message': 'Boat successfully edited: see location header.'}
            if AJSON in request.accept_mimetypes:
                res = response_object(make_response(json.dumps(msg)), AJSON, 303)
            else:
                return {'Error': BAD_RES}, 406
            client.put(user)
            return res
        else:
            return {'Error': MISSING_ATTR}, 400

    elif request.method == 'DELETE':
        user = get_entity(USER, pid)
        payload = verify_jwt(request)
        if is_nonexistent(user):
            return {'Error': NO_USER}, 404
        if str(user['sub']) != str(payload['sub']):
            return {'Error': 'JWT DOES NOT MATCH'}, 406     ##########
        query = client.query(kind=PACKAGE)      # Delete all packages
        res = list(query.fetch())
        for e in res:
            e['id'] = e.key.id
        for e in res:
            if e['id'] in user['packages']:
                client.delete(client.key(PACKAGE, int(e['id'])))
        client.delete(client.key(USER, int(pid)))
        return '', 204

    else:
        return {'Error': NOT_ACCEPTABLE}, 406


@bp.route('/<uid>/packages/<pid>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])        # Add/remove package user
def put_delete_user(uid, pid):
    user = get_entity(USER, uid)
    package = get_entity(PACKAGE, pid)
    if is_nonexistent(user):
        return {'Error': NO_USER}, 404
    if is_nonexistent(package):
        return {'Error': NO_PACKAGE}, 404

    if request.method == 'GET':
        return {'Error': NOT_SUPPORTED + 'GET'}, 405

    elif request.method == 'POST':
        return {'Error': NOT_SUPPORTED + 'POST'}, 405

    if request.method == 'PUT':
        if package['truck'] is not None:
            return {'Error': 'PACKAGE_IN_USE'}, 403
        user['packages'].append({'id': int(package.key.id), 'self': package['self']})
        package['truck'] = {'id': int(user.key.id), 'self': user['self']}
        client.put(user)
        client.put(package)
        return '', 204

    elif request.method == 'PATCH':
        return {'Error': NOT_SUPPORTED + 'PATCH'}, 405

    elif request.method == 'DELETE':
        for curr_package in user['packages']:
            if str(curr_package['id']) == str(pid):
                package['truck'] = None
                user['packages'].remove(curr_package)
                client.put(user)
                client.put(package)
                return '', 204
        return {'Error': 'PACKAGE NOT ON USER'}, 404

    else:
        return {'Error': NOT_ACCEPTABLE}, 406


@bp.route('/<uid>/packages', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def get_packages_user(uid):
    if request.method == 'GET':
        user = get_entity(USER, uid)
        if is_nonexistent(user):
            return {'Error': NO_USER}, 404
        package_list = {'packages': []}
        for curr_package in user['packages']:
            package = get_entity(PACKAGE, curr_package['id'])
            package_list['packages'].append(package)
        return json.dumps(package_list), 200

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

