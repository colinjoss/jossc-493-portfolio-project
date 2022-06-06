import re
import json
from constants import *
from jose import jwt
from six.moves.urllib.request import urlopen


location_pattern = re.compile("[A-Za-z ]+, [A-Z]{2}")


def verify_jwt(request):
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization'].split()
        token = auth_header[1]
    else:
        return False

    jsonurl = urlopen("https://" + DOMAIN + "/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        return False
    if unverified_header["alg"] == "HS256":
        return False
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
            return False
        except jwt.JWTClaimsError:
            return False
        except Exception:
            return 401

        return payload
    else:
        return False


def get_entity(client, kind, eid):
    """
    Using the entity kind and id, returns the entity from datastore.
    """
    key = client.key(kind, int(eid))
    return client.get(key)


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
    truck['packages'] = []
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
        'truck': None
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
    user = ds.entity.Entity(key=client.key(USER))
    user.update({
        'nickname': content['nickname'],
        'email': content['email'],
        'sub': content['sub']
    })
    client.put(user)
    user['packages'] = []
    user['id'] = user.key.id
    user['self'] = URL + '/users/' + str(user.key.id)
    client.put(user)
    return user


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


def is_authorized(sub1, sub2):
    """
    Returns true if sub value matches entity sub, false otherwise.
    """
    return str(sub1) == str(sub2)


def valid(prop, user_input):
    """
    Return true if the given input property is valid otherwise false.
    """
    if prop in validate:
        return validate[prop](user_input)
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
    return all(c.isalpha() or c.isspace() for c in description) and len(description) < 50


validate = {
    'company': valid_company,
    'location': valid_location,
    'arrival': valid_arrival,
    'description': valid_description,
    'source': valid_location,
    'destination': valid_location
}
