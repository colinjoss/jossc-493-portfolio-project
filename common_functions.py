import re
from constants import *


name_pattern = re.compile("^[a-zA-Z0-9.' ]*$")
type_pattern = re.compile("^[a-zA-Z ]*$")


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


def all_exists_in(values, content):
    for value in values:
        if value not in content:
            return False
    return True


def one_exists_in(values, content):
    count = 0
    for value in values:
        if value in content:
            count += 1
    return count == 0


def is_nonexistent(entity):
    return entity is None


def name_in_use(client, type, name):
    query = client.query(kind=type)
    results = list(query.fetch())
    for entity in results:
        if str(entity['name']) == str(name):
            return True
    return False


def valid(prop, input):
    if prop == 'name':
        return valid_name(str(input))
    elif prop == 'type':
        return valid_type(str(input))
    elif prop == 'length':
        return valid_length(input)
    else:
        return False


def valid_name(name):
    if len(name) > 33:          # Boat name cannot exceed 33 characters
        return False
    if name_pattern.match(name) is None:     # Boat name can only use letters, spaces, numbers, and periods
        return False
    return True


def valid_type(type):
    if len(type) > 255:         # Boat type cannot exceed 255 characters
        return False
    if type_pattern.match(type) is None:      # Boat type can only use letters and spaces
        return False
    return True


def valid_length(length):
    try:
        int(length)
        return True
    except:
        return False


def response_object(res, type, code, location=None):
    if location is not None:
        res.location = location
    res.mimetype = type
    res.status_code = code
    return res
