import re
from constants import *
from google.cloud import datastore


name_pattern = re.compile("^[a-zA-Z0-9.' ]*$")
type_pattern = re.compile("^[a-zA-Z ]*$")
email_pattern = re.compile("[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{3})")


def get_entity(client, type, id):
    key = client.key(type, int(id))
    return client.get(key)


def new_truck(datastore, client, content):
    truck = datastore.entity.Entity(key=client.key(TRUCK))
    truck.update({
        'company': content['company'],
        'location': content['location']
    })
    client.put(truck)
    truck['id'] = truck.key.id
    truck['self'] = URL + '/trucks/' + str(truck.key.id)
    client.put(truck)
    return truck


def new_package(datastore, client, content):
    package = datastore.entity.Entity(key=client.key(PACKAGE))
    package.update({
        'source': content['source'],
        'destination': content['destination'],
        'content': content['content'],
        'owner': content['owner']
    })
    client.put(package)
    package['id'] = package.key.id
    package['self'] = URL + '/packages/' + str(package.key.id)
    client.put(package)
    return package


def new_user(datastore, client, content):
    package = datastore.entity.Entity(key=client.key(USER))
    package.update({
        'username': content['username'],
        'email': content['email']
    })
    client.put(package)
    package['id'] = package.key.id
    package['self'] = URL + '/users/' + str(package.key.id)
    client.put(package)
    return package


def all_exists(values, content):
    for value in values:
        if value not in content:
            return False
    return True


def some_exists(values, content):
    count = 0
    for value in values:
        if value in content:
            count += 1
    return count != 0


def is_nonexistent(entity):
    return entity is None


def valid(prop, input, client):
    if prop == 'company':
        return valid_company(str(input))
    elif prop == 'location':
        return valid_location(str(input))
    elif prop == 'source':
        return valid_source(input)
    elif prop == 'destination':
        return valid_destination(input)
    elif prop == 'content':
        return valid_content(input)
    elif prop == 'owner':
        return valid_owner(input, client)
    elif prop == 'username':
        return valid_username(input)
    elif prop == 'email':
        return valid_email(input)
    elif prop == 'address':
        return valid_email(input)
    else:
        return False


def valid_company(company):
    if len(company) > 50:
        return False
    return True


def valid_location(location):
    return True


def valid_source(source):
    return True


def valid_destination(destination):
    return True


def valid_content(content):
    return True


def valid_owner(owner, client):
    query = client.query(kind=USER)
    res = list(query.fetch())
    for e in res:
        e['id'] = e.key.id
    for e in res:
        if int(e['id']) == int(owner):
            return True
    return False


def valid_username(username):
    return username.isalnum()


def valid_email(email):
    if email_pattern.match(email) is None:
        return False
    return True


def valid_address(address):
    return True


def response_object(res, type, code, location=None):
    if location is not None:
        res.location = location
    res.mimetype = type
    res.status_code = code
    return res
