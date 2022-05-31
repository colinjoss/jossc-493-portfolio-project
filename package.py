from flask import Blueprint, request, make_response
from google.cloud import datastore
import json
from json2html import json2html
from constants import *
from common_functions import get_entity, is_nonexistent, valid, \
    response_object, all_exists_in, one_exists_in, new_package

client = datastore.Client()
bp = Blueprint('package', __name__, url_prefix='/packages')


@bp.route('', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def get_post_package():
    if request.method == 'GET':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        query = client.query(kind=PACKAGE)
        res = list(query.fetch())
        for e in res:
            e['id'] = e.key.id
        return json.dumps(res), 200

    elif request.method == 'POST':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415

        content = request.get_json()
        if all_exists_in(['source', 'destination', 'content', 'owner'], content):
            for prop in content:
                if not valid(prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400

            if AJSON in request.accept_mimetypes:
                package = new_package(datastore, client, content)
                return response_object(make_response(json.dumps(package)), AJSON, 201)
            elif HTML in request.accept_mimetypes:
                package = new_package(datastore, client, content)
                return response_object(make_response(json2html.convert(json=json.dumps(package))), HTML, 201)
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
        package = get_entity(client, PACKAGE, pid)
        if is_nonexistent(package):
            return {'Error': NO_PACKAGE}, 404
        package['id'] = package.key.id

        if AJSON in request.accept_mimetypes:
            return response_object(make_response(json.dumps(package)), AJSON, 200)
        elif HTML in request.accept_mimetypes:
            return response_object(make_response(json2html.convert(json=json.dumps(package))), HTML, 200)
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

        if one_exists_in(['source', 'destination', 'content', 'owner'], content):
            package = get_entity(client, PACKAGE, pid)
            if is_nonexistent(package):
                return NO_PACKAGE, 404
            for prop in content:
                if not valid(prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400
                package[prop] = content[prop]
            if AJSON in request.accept_mimetypes:
                res = response_object(make_response(json.dumps(package)), AJSON, 200)
            elif HTML in request.accept_mimetypes:
                res = response_object(make_response(json2html.convert(json=json.dumps(package))), HTML, 200)
            else:
                return {'Error': BAD_RES}, 406
            client.put(package)
            return res

    elif request.method == 'PUT':
        if request.content_type != AJSON:
            return {'Error': BAD_REQ}, 415
        content = request.get_json()
        if 'id' in content or 'self' in content:
            return {'Error': NO_EDIT}, 403

        if one_exists_in(['source', 'destination', 'content', 'owner'], content):
            package = get_entity(client, PACKAGE, pid)
            if package is None:
                return NO_PACKAGE, 404
            for prop in content:
                if not valid(prop, content[prop]):
                    return {'Error': BAD_VALUE}, 400
                package[prop] = content[prop]
            msg = {'Message': 'Boat successfully edited: see location header.'}
            if AJSON in request.accept_mimetypes:
                res = response_object(make_response(json.dumps(msg)), AJSON, 303)
            elif HTML in request.accept_mimetypes:
                res = response_object(make_response(json2html.convert(json=json.dumps(msg))), HTML, 303)
            else:
                return {'Error': BAD_RES}, 406
            client.put(package)
            return res
        else:
            return {'Error': MISSING_ATTR}, 400

    elif request.method == 'DELETE':
        package = get_entity(client, PACKAGE, pid)
        if is_nonexistent(package):
            return {'Error': NO_PACKAGE}, 404
        client.delete(client.key(PACKAGE, int(pid)))
        return '', 204

    else:
        return {'Error': NOT_ACCEPTABLE}, 406
