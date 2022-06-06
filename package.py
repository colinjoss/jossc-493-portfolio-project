from flask import Blueprint, request
from common_functions import *
from google.cloud import datastore


client = datastore.Client()
bp = Blueprint('package', __name__, url_prefix='/packages')


@bp.route('', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def get_post_package():
    if request.method == 'GET':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        payload = verify_jwt(request)
        if not payload:
            return {'Error': BAD_AUTH}, 401
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
        if not payload:
            return {'Error': BAD_AUTH}, 401
        content = request.get_json()
        if not all_exists(['description', 'source', 'destination'], content):
            return {'Error': MISSING_ATTR}, 400
        for prop in content:
            if not valid(prop, content[prop]):
                return {'Error': BAD_VALUE}, 400
        if AJSON in request.accept_mimetypes:
            content['owner'] = payload['sub']
            package = new_package(client, datastore, content)
            query = client.query(kind=USER)  # Add package to user packages
            users = query.fetch()
            for user in users:
                if str(user['sub']) == str(package['owner']):
                    user['packages'].append({'id': package['id'], 'self': package['self']})
                    client.put(user)
            return json.dumps(package), 201
        else:
            return {'Error': BAD_RES}, 406



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
        if not payload:
            return {'Error': BAD_AUTH}, 401
        package = get_entity(client, PACKAGE, pid)
        if is_nonexistent(package):
            return {'Error': NO_PACKAGE}, 404
        if not is_authorized(package['owner'], payload['sub']):
            return {'Error': BAD_AUTH}, 401
        package['id'] = package.key.id
        if AJSON in request.accept_mimetypes:
            return json.dumps(package), 200
        return {'Error': BAD_RES}, 406

    elif request.method == 'POST':
        return {'Error': NOT_SUPPORTED + 'POST'}, 405

    elif request.method == 'PATCH':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        payload = verify_jwt(request)
        if not payload:
            return {'Error': BAD_AUTH}, 401
        content = request.get_json()
        if some_exists(['id', 'self'], content):
            return {'Error': NO_EDIT}, 403
        if not some_exists(['description', 'source', 'destination'], content):
            return {'Error': MISSING_ATTR}, 400
        package = get_entity(client, PACKAGE, pid)
        if not is_authorized(package['owner'], payload['sub']):
            return {'Error': BAD_AUTH}, 401
        if is_nonexistent(package):
            return {'Error': NO_PACKAGE}, 404
        for prop in content:
            if not valid(prop, content[prop]):
                return {'Error': BAD_VALUE}, 400
            package[prop] = content[prop]
        if AJSON in request.accept_mimetypes:
            client.put(package)
            return json.dumps(package), 200
        return {'Error': BAD_RES}, 406

    elif request.method == 'PUT':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        payload = verify_jwt(request)
        if not payload:
            return {'Error': BAD_AUTH}, 401
        content = request.get_json()
        if some_exists(['id', 'self'], content):
            return {'Error': NO_EDIT}, 403
        if not some_exists(['description', 'source', 'destination'], content):
            return {'Error': MISSING_ATTR}, 400
        package = get_entity(client, PACKAGE, pid)
        if not is_authorized(package['owner'], payload['sub']):
            return {'Error': BAD_AUTH}, 401
        if package is None:
            return {'Error': NO_PACKAGE}, 404
        for prop in content:
            if not valid(prop, content[prop]):
                return {'Error': BAD_VALUE}, 400
            package[prop] = content[prop]
        if AJSON in request.accept_mimetypes:
            client.put(package)
            return json.dumps(package), 200
        return {'Error': BAD_RES}, 406

    elif request.method == 'DELETE':
        payload = verify_jwt(request)
        if not payload:
            return {'Error': BAD_AUTH}, 401
        package = get_entity(client, PACKAGE, int(pid))
        if not is_authorized(payload['sub'], package['owner']):
            return {'Error': BAD_AUTH}, 401
        if is_nonexistent(package):
            return {'Error': NO_PACKAGE}, 404
        query = client.query(kind=USER)                         # Delete package from all user packages
        users = query.fetch()
        for user in users:
            if is_authorized(user['sub'], package['owner']):
                user['packages'] = [d for d in user['packages'] if int(d['id']) != int(pid)]
                client.put(user)
        if package['truck'] is not None:
            truck = get_entity(client, TRUCK, package['truck']['id'])     # Delete package from all truck packages
            truck['packages'] = [d for d in truck['packages'] if int(d['id']) != int(pid)]
            client.put(truck)
        client.delete(client.key(PACKAGE, int(pid)))
        return '', 204

    else:
        return {'Error': NOT_ACCEPTABLE}, 406
