import logging
import demjson
from datetime import datetime
# from rest_framework.views import APIView
from rest_framework.decorators import api_view, authentication_classes, permission_classes, renderer_classes
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import PermissionDenied

# from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from ddosdb.database import Database
from ddosdb.models import FileUpload

Database.initialize()

logger = logging.getLogger(__name__)


def _mdb():
    return Database.getDB()


def _insert(data):
    _mdb().insert(data, check_keys=False)


def _search(query=None, fields=None, order=None):
    q = query
    if order:
        q = {}
        q["$query"] = query
        q["$orderby"] = order

    logger.info("filter={}, fields={}".format(q, fields))
    result = list(_mdb().find(q, fields))
    return result


def _search_one(query=None, fields=None):
    result = _mdb().find_one(query, fields)
    return result


def _update(query=None, fields=None):
    result = _mdb().find_one_and_update(query, fields)
    return result


def _delete(query=None):
    result = _mdb().delete_many(query)
    return result


# Create your views here.
@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def index(request):
    logger.debug("Index")
    content = {'message': 'Hello {} ({})'.format(request.user, request.method)}
    return JsonResponse(content)


# ---------------------------------------------------------------------------------
@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def fingerprints(request):
    logger.info("fingerprints ({})".format(request.method))

    user_perms = request.user.get_user_permissions()
    group_perms = request.user.get_group_permissions()

    # make a combined set (a set cannot contain duplicates)
    permissions = user_perms | group_perms

    if request.method == "GET":
        if "ddosdb.view_fingerprint" not in permissions:
            raise PermissionDenied()
        try:
            # Only return shareable fingerprints
            fps = _search({'shareable': True}, {'_id': 0})

            # logger.debug(fps)
            results = []
            for fp in fps:
                results.append(fp['key'])
            return JsonResponse(results, safe=False)

        except ServerSelectionTimeoutError as e:
            logger.error("MongoDB unreachable")
            response = HttpResponse()
            response.status_code = 500
            response.reason_phrase = "Error with MongoDB"
            return response

    elif request.method == "POST":

        if "ddosdb.add_fingerprint" not in permissions:
            raise PermissionDenied()
            # response = HttpResponse()
            # response.status_code = 401
            # response.reason_phrase = "Invalid credentials or no permission"
            # return response

        if request.META['CONTENT_TYPE'] != "application/json":
            response = HttpResponse()
            response.status_code = 400
            response.reason_phrase = "Wrong content type"
            return response

        logger.info("Inserting fingerprint(s)")

        def insert(fp):
            logger.info("Inserting fingerprint {}".format(fp["key"]))
            # Register record
            _delete({'key': fp['key']})
            _insert(fp)
            file_upload = FileUpload()
            file_upload.user = request.user
            file_upload.filename = fp["key"]
            file_upload.save()

        fps = demjson.decode(request.body)
        if type(fps) is list:
            for fp in fps:
                # Replace name in fingerprint with the name of the user submitting it
                # so as not to transfer usernames over different DBs
                fp["submitter"] = request.user.username
                # Set shareable to false to prevent it being shared further on by default
                fp["shareable"] = False
                # Set submit timestamp
                fp["submit_timestamp"] = datetime.utcnow().isoformat()
                if not 'comment' in fp:
                    fp['comment'] = ""

                try:
                    insert(fp)
                except Exception as e:
                    response = HttpResponse()
                    response.status_code = 400
                    response.reason_phrase = str(e)
                    return response
        else:
            # Replace name in fingerprint with the name of the user submitting it
            # so as not to transfer usernames over different DBs
            fps["submitter"] = request.user.username
            # Set shareable to false to prevent it being shared further on by default
            fps["shareable"] = False
            # Set submit timestamp
            fps["submit_timestamp"] = datetime.utcnow().isoformat()
            if not 'comment' in fps:
                fps['comment'] = ""
            try:
                insert(fps)
            except Exception as e:
                response = HttpResponse()
                response.status_code = 400
                response.reason_phrase = str(e)
                return response

        response = HttpResponse()
        response.status_code = 201
        response.reason_phrase = "Fingerprints added successfully"
        return response


# ---------------------------------------------------------------------------------
@api_view(['GET'])
@authentication_classes([TokenAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def fingerprint(request, key):
    logger.debug("fingerprint/{} ({})".format(key, request.method))

    user_perms = request.user.get_user_permissions()
    group_perms = request.user.get_group_permissions()

    # make a combined set (a set cannot contain duplicates)
    permissions = user_perms | group_perms

    if request.method == "GET":
        if "ddosdb.view_fingerprint" not in permissions:
            raise PermissionDenied()

    try:
        fps = _search({'key': key}, {'_id': 0})
        logger.debug(fps)
        if len(fps) > 0:
            return JsonResponse(fps, safe=False)
        else:
            response = HttpResponse()
            response.status_code = 404
            response.reason_phrase = "Fingerprint {} not found".format(key)
            return response

    except ServerSelectionTimeoutError as e:
        logger.error("MongoDB unreachable")
        response = HttpResponse()
        response.status_code = 500
        response.reason_phrase = "Error with MongoDB"
        return response


# ---------------------------------------------------------------------------------
@api_view(['GET'])
@authentication_classes([TokenAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def permissions(request):
    logger.debug("permissions ")

    user_perms = request.user.get_user_permissions()
    group_perms = request.user.get_group_permissions()

    # make a combined set (a set cannot contain duplicates)
    user_permissions = user_perms | group_perms

    if user_permissions is None:
        raise PermissionDenied()

    return JsonResponse({str(request.user): list(user_permissions)}, safe=False)


# ---------------------------------------------------------------------------------
@api_view(['POST'])
@authentication_classes([TokenAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def unknown_fingerprints(request):
    logger.debug("unknown_fingerprints ({})".format(request.method))
    """Takes a list of fingerprint keys and returns the fingerprint keys not present in the database"""
    """Allowing caller to then only upload fingerprints not yet known by this DDoS-DB"""
    """This is a REST method accepting only POST calls with JSON body content (application/json)"""

    user_perms = request.user.get_user_permissions()
    group_perms = request.user.get_group_permissions()

    # make a combined set (a set cannot contain duplicates)
    all_permissions = user_perms | group_perms

    if "ddosdb.view_fingerprint" not in all_permissions:
        raise PermissionDenied()

    if request.META['CONTENT_TYPE'] != "application/json":
        logger.warning("unknown_fingerprints called with wrong content type")
        logger.warning("Should be 'application/json', is '{}'".format(request.META['CONTENT_TYPE']))
        response = HttpResponse()
        response.status_code = 400
        response.reason_phrase = "Wrong content type"
        return response

    data = demjson.decode(request.body)
    unk_fps = []

    try:
        fps = _search(fields={'key': 1, '_id': 0})
        known_fps = []
        for fp in fps:
            known_fps.append(fp['key'])
        logger.info("Known fingerprints: ".format(known_fps))
        logger.info(data)
        for fp in data:
            logger.info("Fingerprint {} is {}".format(fp, fp in known_fps))
            if not fp in known_fps:
                unk_fps.append(fp)

        return JsonResponse(unk_fps, safe=False)

    except ServerSelectionTimeoutError as e:
        logger.error("MongoDB unreachable")
        response = HttpResponse()
        response.status_code = 500
        response.reason_phrase = "Error reaching MongoDB"
        return response

