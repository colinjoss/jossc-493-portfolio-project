import re
from constants import *
from google.cloud import datastore


client = datastore.Client()


name_pattern = re.compile("^[a-zA-Z0-9.' ]*$")
type_pattern = re.compile("^[a-zA-Z ]*$")
location_pattern = re.compile("[A-Za-z]+, [A-Z]{2}")
email_pattern = re.compile("[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{3})")


# def get_collection(req, kind):
#     query = client.query(kind=kind)
#     q_limit = int(req.args.get('limit', '5'))
#     q_offset = int(req.args.get('offset', '0'))
#     l_iterator = query.fetch(limit=q_limit, offset=q_offset)
#     pages = l_iterator.pages
#     results = list(next(pages))
#     if l_iterator.next_page_token:
#         next_offset = q_offset + q_limit
#         next_url = req.base_url + '?limit=' + str(
#             q_limit) + '&offset=' + str(next_offset)
#     else:
#         next_url = None
#     for e in results:
#         e['id'] = e.key.id
#     output = {kind + 's': results}
#     if next_url:
#         output['next'] = next_url
#     return output


def get_entity(type, id):
    """
    Using the entity type and id, returns the entity from datastore.
    """
    key = client.key(type, int(id))
    return client.get(key)


def response_object(res, type, code, location=None):
    """
    Returns the output formatted with a status code and mimetype.
    """
    if location is not None:
        res.location = location
    res.mimetype = type
    res.status_code = code
    return res


def new_truck(content):
    """
    Creates a new truck entity.
    """
    truck = datastore.entity.Entity(key=client.key(TRUCK))
    truck.update({
        'company': content['company'],
        'location': content['location'],
        'arrival': content['arrival']
    })
    client.put(truck)
    truck['id'] = truck.key.id
    truck['self'] = URL + '/trucks/' + str(truck.key.id)
    client.put(truck)
    return truck


def new_package(content):
    """
    Creates a new package entity.
    """
    package = datastore.entity.Entity(key=client.key(PACKAGE))
    package.update({
        'description': content['description'],
        'source': content['source'],
        'destination': content['destination'],
        'owner': content['owner'],
        'truck': content['truck']
    })
    client.put(package)
    package['id'] = package.key.id
    package['self'] = URL + '/packages/' + str(package.key.id)
    client.put(package)
    return package


def new_user(content):
    """
    Creates a new user entity.
    """
    package = datastore.entity.Entity(key=client.key(USER))
    package.update({
        'username': content['username'],
        'email': content['email'],
        'address': content['address']
    })
    client.put(package)
    package['id'] = package.key.id
    package['self'] = URL + '/users/' + str(package.key.id)
    client.put(package)
    return package


def all_exists(values, content):
    """
    Returns true if all values exist in content, otherwise false.
    """
    for value in values:
        if value not in content:
            return False
    return True


def some_exists(values, content):
    """
    Returns true if at least one value exists in content, otherwise false.
    """
    for value in values:
        if value in content:
            return True
    return False


def is_nonexistent(entity):
    """
    Returns true if entity exists, otherwise false.
    """
    return entity is None


def valid(prop, input):
    """
    Return true if the given input property is valid otherwise false.
    """
    if prop in validate:
        return validate[prop](input)
    return False


def valid_company(company):
    """
    Returns true if the company property is valid, otherwise false.
    """
    if len(company) > 50:
        return False
    return True


def valid_location(location):
    """
    Returns true if the location property is valid, otherwise false.
    """
    if location_pattern.match(location) is None:
        return False
    return True


def valid_arrival(arrival):
    """
    Returns true if the arrival property is valid, otherwise false.
    """
    return isinstance(arrival, int)


def valid_description(description):
    """
    Returns true if the description property is valid, otherwise false.
    """
    return description.isalpha() and len(description) < 50


def valid_source(source):
    """
    Returns true if the source property is valid, otherwise false.
    """
    if location_pattern.match(source) is None:
        return False
    return True


def valid_destination(destination):
    """
    Returns true if the destination property is valid, otherwise false.
    """
    if location_pattern.match(destination) is None:
        return False
    return True


def valid_username(username):
    """
    Returns true if the username property is valid, otherwise false.
    """
    return username.isalnum() and len(username) < 16


def valid_email(email):
    """
    Returns true if the email property is valid, otherwise false.
    """
    if email_pattern.match(email) is None:
        return False
    return len(email) < 50


def valid_address(address):
    """
    Returns true if the address property is valid, otherwise false.
    """
    if location_pattern.match(address) is None:
        return False
    return True


def valid_packages(packages):
    """
    Returns true if the all package id's are valid, otherwise false.
    """
    query = client.query(kind=PACKAGE)
    res = list(query.fetch())
    for e in res:
        e['id'] = e.key.id
    count = 0
    for package in packages:
        for e in res:
            if e['id'] == package:
                count += 1
    return count == len(packages)


def valid_owner(owner):
    """
    Returns true if the owner property is valid, otherwise false.
    """
    return True


def valid_truck(truck):
    """
    Returns true if the truck property is valid, otherwise false.
    """
    query = client.query(kind=TRUCK)
    res = list(query.fetch())
    for e in res:
        e['id'] = e.key.id
    for e in res:
        if int(e['id']) == int(truck):
            return True
    return False


validate = {
    'company': valid_company,
    'location': valid_location,
    'arrival': valid_arrival,
    'description': valid_description,
    'source': valid_source,
    'destination': valid_destination,
    'owner': valid_owner,
    'truck': valid_truck,
    'username': valid_username,
    'email': valid_email,
    'address': valid_address,
    'packages': valid_packages
}
