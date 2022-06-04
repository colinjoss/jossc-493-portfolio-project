from flask import Blueprint, request, make_response
from google.cloud import datastore
import json
from constants import *
from common_functions import get_entity, is_nonexistent, valid, \
    response_object, all_exists, some_exists, new_package
from auth import verify_jwt


client = datastore.Client()
bp = Blueprint('package', __name__, url_prefix='/packages')


@bp.route('', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def get_post_package():
    if request.method == 'GET':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        payload = verify_jwt(request)
        query = client.query(kind=PACKAGE)
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
        by_owner = []
        for e in results:
            e['id'] = e.key.id
            if str(e['owner']) == str(payload['sub']):
                by_owner.append(e)
        output = {'packages': by_owner}
        if next_url:
            output['next'] = next_url
        return json.dumps(output), 200

    elif request.method == 'POST':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        payload = verify_jwt(request)
        content = request.get_json()
        content['owner'] = payload['sub']
        if all_exists(['description', 'source', 'destination', 'owner', 'truck'], content):
            for prop in content:
                if not valid(prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400
            if AJSON in request.accept_mimetypes:
                package = new_package(content)
                return response_object(make_response(json.dumps(package)), AJSON, 201)
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
def get_put_patch_delete_package(pid):
    if request.method == 'GET':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        payload = verify_jwt(request)
        package = get_entity(PACKAGE, pid)
        if is_nonexistent(package):
            return {'Error': NO_PACKAGE}, 404
        if str(package['owner']) == str(payload['sub']):
            package['id'] = package.key.id
            if AJSON in request.accept_mimetypes:
                return response_object(make_response(json.dumps(package)), AJSON, 200)
            return {'Error': BAD_RES}, 406
        else:
            return {'Error': 'JWT DOES NOT MATCH'}, 406         ##########

    elif request.method == 'POST':
        return {'Error': NOT_SUPPORTED + 'POST'}, 405

    elif request.method == 'PATCH':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        payload = verify_jwt(request)
        content = request.get_json()
        if 'id' in content or 'self' in content:
            return {'Error': NO_EDIT}, 403
        if some_exists(['description', 'source', 'destination', 'truck'], content):
            package = get_entity(PACKAGE, pid)
            if str(package['owner']) == str(payload['sub']):
                if is_nonexistent(package):
                    return NO_PACKAGE, 404
                for prop in content:
                    if not valid(prop, content[prop]):
                        return {'Error': BAD_VALUE}, 400
                    package[prop] = content[prop]
                if AJSON in request.accept_mimetypes:
                    res = response_object(make_response(json.dumps(package)), AJSON, 200)
                else:
                    return {'Error': BAD_RES}, 406
                client.put(package)
                return res
            else:
                return {'Error': 'JWT DOES NOT MATCH'}, 406     ##########

    elif request.method == 'PUT':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        payload = verify_jwt(request)
        content = request.get_json()
        if 'id' in content or 'self' in content:
            return {'Error': NO_EDIT}, 403
        if some_exists(['description', 'source', 'destination', 'owner', 'truck'], content):
            package = get_entity(PACKAGE, pid)
            if str(package['owner']) == str(payload['sub']):
                if package is None:
                    return NO_PACKAGE, 404
                for prop in content:
                    if not valid(prop, content[prop]):
                        return {'Error': BAD_VALUE}, 400
                    package[prop] = content[prop]
                msg = {'Message': 'Boat successfully edited: see location header.'}
                if AJSON in request.accept_mimetypes:
                    res = response_object(make_response(json.dumps(msg)), AJSON, 303)
                else:
                    return {'Error': BAD_RES}, 406
                client.put(package)
                return res
            else:
                return {'Error': 'JWT DOES NOT MATCH'}, 406     ##########
        else:
            return {'Error': MISSING_ATTR}, 400

    elif request.method == 'DELETE':
        payload = verify_jwt(request)
        package = get_entity(PACKAGE, pid)
        if str(package['owner']) != str(payload['sub']):
            return {'Error': 'JWT DOES NOT MATCH'}, 406         ##########
        if is_nonexistent(package):
            return {'Error': NO_PACKAGE}, 404
        user = get_entity(USER, package['owner'])       # Delete package from all user packages
        user['packages'].remove(pid)
        client.put(user)
        truck = get_entity(TRUCK, package['truck'])     # Delete package from all truck packages
        truck['packages'].remove(pid)
        client.put(truck)
        client.delete(client.key(PACKAGE, int(pid)))
        return '', 204

    else:
        return {'Error': NOT_ACCEPTABLE}, 406
