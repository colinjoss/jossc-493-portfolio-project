from flask import Blueprint, request, make_response
from common_functions import *
from google.cloud import datastore


client = datastore.Client()
bp = Blueprint('truck', __name__, url_prefix='/trucks')


@bp.route('', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def get_post_truck():
    if request.method == 'GET':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        query = client.query(kind=TRUCK)
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
        output = {'trucks': results}
        if next_url:
            output['next'] = next_url
        return json.dumps(output), 200

    elif request.method == 'POST':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        content = request.get_json()
        if all_exists(['company', 'location', 'arrival', 'packages'], content):
            for prop in content:
                if not valid(client, prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400
            if AJSON in request.accept_mimetypes:
                truck = new_truck(client, datastore, content)
                return response_object(make_response(json.dumps(truck)), AJSON, 201)
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


@bp.route('/<tid>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def get_put_patch_delete_truck(tid):
    if request.method == 'GET':
        truck = get_entity(client, TRUCK, tid)
        if is_nonexistent(truck):
            return {'Error': NO_TRUCK}, 404
        truck['id'] = truck.key.id
        if AJSON in request.accept_mimetypes:
            return response_object(make_response(json.dumps(truck)), AJSON, 200)
        return {'Error': BAD_RES}, 406

    elif request.method == 'POST':
        return {'Error': NOT_SUPPORTED + 'POST'}, 405

    elif request.method == 'PATCH':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        content = request.get_json()
        if 'id' in content or 'self' in content:
            return {'Error': NO_EDIT}, 403
        if some_exists(['company', 'location', 'arrival', 'packages'], content):
            truck = get_entity(client, TRUCK, tid)
            if is_nonexistent(truck):
                return {'Error': NO_TRUCK}, 404
            for prop in content:
                if not valid(client, prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400
                truck[prop] = content[prop]
            if AJSON in request.accept_mimetypes:
                res = response_object(make_response(json.dumps(truck)), AJSON, 200)
            else:
                return {'Error': BAD_RES}, 406
            client.put(truck)
            return res

    elif request.method == 'PUT':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        content = request.get_json()
        if 'id' in content or 'self' in content:
            return {'Error': NO_EDIT}, 403
        if some_exists(['company', 'location', 'arrival', 'packages'], content):
            truck = get_entity(client, TRUCK, tid)
            if truck is None:
                return NO_TRUCK, 404
            for prop in content:
                if not valid(client, prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400
                truck[prop] = content[prop]
            msg = {'Message': 'Truck successfully edited: see location header.'}
            if AJSON in request.accept_mimetypes:
                res = response_object(make_response(json.dumps(msg)), AJSON, 303)
            else:
                return {'Error': BAD_RES}, 406
            client.put(truck)
            return res
        else:
            return {'Error': MISSING_ATTR}, 400

    elif request.method == 'DELETE':
        truck = get_entity(client, TRUCK, tid)
        if is_nonexistent(truck):
            return {'Error': NO_TRUCK}, 404

        # Delete truck from all packages
        query = client.query(kind=PACKAGE)
        res = list(query.fetch())
        for e in res:
            if e['truck'] == tid:
                e['truck'] = None
                client.put(e)

        client.delete(client.key(TRUCK, int(tid)))
        return '', 204

    else:
        return {'Error': NOT_ACCEPTABLE}, 406


@bp.route('/<tid>/packages/<pid>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def put_delete_truck(tid, pid):
    truck = get_entity(client, TRUCK, tid)
    package = get_entity(client, PACKAGE, pid)
    if is_nonexistent(truck):
        return {'Error': NO_TRUCK}, 404
    if is_nonexistent(package):
        return {'Error': NO_PACKAGE}, 404

    if request.method == 'GET':
        return {'Error': NOT_SUPPORTED + 'GET'}, 405

    elif request.method == 'POST':
        return {'Error': NOT_SUPPORTED + 'POST'}, 405

    if request.method == 'PUT':
        if package['truck'] is not None:
            return {'Error': 'PACKAGE_IN_USE'}, 403
        truck['packages'].append({'id': int(package.key.id), 'self': package['self']})
        package['truck'] = {'id': int(truck.key.id), 'self': truck['self']}
        client.put(truck)
        client.put(package)
        return '', 204

    elif request.method == 'PATCH':
        return {'Error': NOT_SUPPORTED + 'PATCH'}, 405

    elif request.method == 'DELETE':
        for curr_package in truck['packages']:
            if str(curr_package['id']) == str(pid):
                package['truck'] = None
                truck['packages'].remove(curr_package)
                client.put(truck)
                client.put(package)
                return '', 204
        return {'Error': 'PACKAGE NOT ON TRUCK'}, 404

    else:
        return {'Error': NOT_ACCEPTABLE}, 406


@bp.route('/<tid>/packages', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def get_packages_truck(tid):
    if request.method == 'GET':
        truck = get_entity(client, TRUCK, tid)
        if is_nonexistent(tid):
            return {'Error': NO_TRUCK}, 404
        package_list = {'packages': []}
        for curr_package in truck['packages']:
            package = get_entity(client, PACKAGE, curr_package['id'])
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
