import logging
import pprint
import json

from datetime import datetime
from rest_framework.decorators import api_view, authentication_classes, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied

# from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from ddosdb.database import Database

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


# ---------------------------------------------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def fingerprints(request, format=None):
    """
    Returns the list of fingerprint keys if no key is specified or a specific fingerprint
    if fingerprint/<key> is invoked

    Use the header 'Authorization: Token <token>' to authorize API calls.

    """
    logger.info("fingerprints ({})".format(request.method))

    # user_perms = request.user.get_user_permissions()
    # group_perms = request.user.get_group_permissions()
    #
    # # make a combined set (a set cannot contain duplicates)
    permissions = request.user.get_all_permissions()

    if request.method == "GET":
        if "ddosdb.view_fingerprint" not in permissions:
            raise PermissionDenied()
        try:
            # logger.debug(fps)
            results = {'shareable': [],
                       'non-shareable': []}

            # Only return shareable and 'own' fingerprints by default
            fps = _search({'shareable': True}, {'_id': 0})
            for fp in fps:
                results['shareable'].append(fp['key'])

            if "ddosdb.view_nonsync_fingerprint" in permissions:
                fps = _search({'shareable': False}, {'_id': 0})
            else:
                fps = _search({'shareable': False, 'submitter': request.user.username}, {'_id': 0})
            for fp in fps:
                results['non-shareable'].append(fp['key'])

            return Response(results)

        except ServerSelectionTimeoutError as e:
            logger.error("MongoDB unreachable")
            return Response({"detail": "Error with MongoDB"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == "POST":

        if "ddosdb.add_fingerprint" not in permissions:
            raise PermissionDenied()

        if request.META['CONTENT_TYPE'] != "application/json":
            return Response({"detail": "Wrong content type"}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

        logger.info("Inserting fingerprint(s)")

        fps = json.loads(request.data)
        if type(fps) is not list:
            fps = [fps]

        for fp in fps:
            logger.info("Inserting fingerprint {}".format(fp["key"]))
            # Replace name in fingerprint with the name of the user submitting it
            # so as not to transfer usernames over different DBs
            fp["submitter"] = request.user.username
            # Set shareable to false by default
            if 'shareable' not in fp:
                logger.info('Shareable not in FP, setting to false')
                fp["shareable"] = False
            # Set submit timestamp
            fp["submit_timestamp"] = datetime.utcnow().isoformat()
            if 'comment' not in fp:
                fp['comment'] = ""

            try:
                # Register record
                _delete({'key': fp['key']})
                _insert(fp)
                # file_upload = FileUpload()
                # file_upload.user = request.user
                # file_upload.filename = fp["key"]
                # file_upload.save()
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": "OK"}, status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fingerprint(request, key, format=None):
    logger.debug("fingerprint/{} ({})".format(key, request.method))

    permissions = request.user.get_all_permissions()

    if request.method == "GET":
        if "ddosdb.view_fingerprint" not in permissions:
            raise PermissionDenied()

    try:
        fps = _search({'key': key}, {'_id': 0})
        logger.debug(fps)
        if len(fps) > 0:
            # Check if this user is allowed to view this fingerprint...

            return Response(fps)
        else:
            return Response(f"Fingerprint {key} not found", status=status.HTTP_404_NOT_FOUND)

    except ServerSelectionTimeoutError as e:
        return Response({"detail": "Error with MongoDB"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def permissions(request, format=None):
    """
    Returns the permissions of the user linked to the token used to authorize this
    and other API calls.
    Use the header 'Authorization: Token <token>' to authorize API calls.

    """
    logger.debug("permissions ")

    user_permissions = list(request.user.get_all_permissions())
    permissions = []

    for perm in user_permissions:
        permissions.append(perm)

    permissions.sort()

    return Response({str(request.user): permissions})


# ---------------------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unknown_fingerprints(request, format=None):
    logger.debug("unknown_fingerprints ({})".format(request.method))
    """Takes a list of fingerprint keys and returns the fingerprint keys not present in the database"""
    """Allowing caller to then only upload fingerprints not yet known by this DDoS-DB"""
    """This is a REST method accepting only POST calls with JSON body content (application/json)"""

    all_permissions = request.user.get_all_permissions()

    # There is only a need to be able to use this call if you want
    # to upload new fingerprints and need to check which are unknown
    if "ddosdb.add_fingerprint" not in all_permissions:
        raise PermissionDenied()

    if request.META['CONTENT_TYPE'] != "application/json":
        logger.warning("unknown_fingerprints called with wrong content type")
        logger.warning("Should be 'application/json', is '{}'".format(request.META['CONTENT_TYPE']))
        return Response({"detail": "Wrong content type"}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    data = json.loads(request.body)
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

        return Response(unk_fps)

    except ServerSelectionTimeoutError as e:
        return Response({"detail": "Error with MongoDB"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

