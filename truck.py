from flask import Blueprint, request, make_response
from google.cloud import datastore
import json
from json2html import json2html
from constants import *
from common_functions import get_entity, is_nonexistent, valid, \
    response_object, new_truck, all_exists, some_exists


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
        if all_exists(['company', 'location'], content):
            for prop in content:
                if not valid(prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400

            if AJSON in request.accept_mimetypes:
                truck = new_truck(content)
                return response_object(make_response(json.dumps(truck)), AJSON, 201)
            elif HTML in request.accept_mimetypes:
                truck = new_truck(datastore)
                return response_object(make_response(json2html.convert(json=json.dumps(truck))), HTML, 201)
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


@bp.route('/<tid>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def get_put_patch_delete_truck(tid):
    if request.method == 'GET':
        truck = get_entity(TRUCK, tid)
        if is_nonexistent(truck):
            return {'Error': NO_TRUCK}, 404
        truck['id'] = truck.key.id

        if AJSON in request.accept_mimetypes:
            return response_object(make_response(json.dumps(truck)), AJSON, 200)
        elif HTML in request.accept_mimetypes:
            return response_object(make_response(json2html.convert(json=json.dumps(truck))), HTML, 200)
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

        if some_exists(['company', 'location'], content):
            truck = get_entity(TRUCK, tid)
            if is_nonexistent(truck):
                return NO_TRUCK, 404
            for prop in content:
                if not valid(prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400
                truck[prop] = content[prop]

            if AJSON in request.accept_mimetypes:
                res = response_object(make_response(json.dumps(truck)), AJSON, 200)
            elif HTML in request.accept_mimetypes:
                res = response_object(make_response(json2html.convert(json=json.dumps(truck))), HTML, 200)
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

        if some_exists(['company', 'location'], content):
            truck = get_entity(TRUCK, tid)
            if truck is None:
                return NO_TRUCK, 404
            for prop in content:
                if not valid(prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400
                truck[prop] = content[prop]
            msg = {'Message': 'Truck successfully edited: see location header.'}
            if AJSON in request.accept_mimetypes:
                res = response_object(make_response(json.dumps(msg)), AJSON, 303)
            elif HTML in request.accept_mimetypes:
                res = response_object(make_response(json2html.convert(json=json.dumps(msg))), HTML, 303)
            else:
                return {'Error': BAD_RES}, 406
            client.put(truck)
            return res
        else:
            return {'Error': MISSING_ATTR}, 400

    elif request.method == 'DELETE':
        truck = get_entity(TRUCK, tid)
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
