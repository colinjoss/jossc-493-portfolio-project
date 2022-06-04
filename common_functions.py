import re
import json
from constants import *
from jose import jwt
from six.moves.urllib.request import urlopen


location_pattern = re.compile("[A-Za-z]+, [A-Z]{2}")
email_pattern = re.compile("[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{3})")


def verify_jwt(request):
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization'].split()
        token = auth_header[1]
    else:
        return {"code": "no auth header",
                "description": "Authorization header is missing"}, 401

    jsonurl = urlopen("https://" + DOMAIN + "/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        return 'BAD'
    if unverified_header["alg"] == "HS256":
        return {"code": "invalid_header",
                "description":
                    "Invalid header. "
                    "Use an RS256 signed JWT Access Token"}, 401
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=CLIENT_ID,
                issuer="https://" + DOMAIN + "/"
            )
        except jwt.ExpiredSignatureError:
            return {"code": "token_expired",
                    "description": "token is expired"}, 401
        except jwt.JWTClaimsError:
            return {"code": "invalid_claims",
                    "description":
                        "incorrect claims,"
                        " please check the audience and issuer"}, 401
        except Exception:
            return 'BAD'

        return payload
    else:
        return 'BAD'


def get_entity(client, kind, id):
    """
    Using the entity kind and id, returns the entity from datastore.
    """
    key = client.key(kind, int(id))
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


def new_truck(client, ds, content):
    """
    Creates a new truck entity.
    """
    truck = ds.entity.Entity(key=client.key(TRUCK))
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


def new_package(client, ds, content):
    """
    Creates a new package entity.
    """
    package = ds.entity.Entity(key=client.key(PACKAGE))
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


def new_user(client, ds, content):
    """
    Creates a new user entity.
    """
    package = ds.entity.Entity(key=client.key(USER))
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


def valid(client, prop, input):
    """
    Return true if the given input property is valid otherwise false.
    """
    if prop in validate:
        if prop == 'truck' or prop == 'packages':
            validate[prop](client, input)
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


def valid_packages(client, packages):
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


def valid_truck(client, truck):
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
