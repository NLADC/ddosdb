import math
import os
import time
import demjson
import requests
import base64
from datetime import datetime
from datetime import timedelta
import collections
import pprint
import pandas as pd
from distutils.util import strtobool
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import logging

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from django.http import HttpResponse
from django.shortcuts import render, redirect, reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django_rest_multitokenauth.models import MultiToken

# from ddosdb.enrichment.team_cymru import TeamCymru
from ddosdb.models import Query, RemoteDdosDb, FailedLogin, MISP, FileUpload
from ddosdb.database import Database
import ddosdb.misp

Database.initialize()

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------------------------------------------------
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


def _remote_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = None
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _pretty_request(request):
    logger.debug("_pretty_request ({})".format(request.method))
    headers = ''
    for header, value in request.META.items():
        if not header.startswith('HTTP'):
            continue
        header = '-'.join([h.capitalize() for h in header[5:].lower().split('_')])
        headers += '{}: {}\n'.format(header, value)

    return (
        '{method} HTTP/1.1\n'
        'Content-Length: {content_length}\n'
        'Content-Type: {content_type}\n'
        '{headers}\n\n'
        '{body}'
    ).format(
        method=request.method,
        content_length=request.META['CONTENT_LENGTH'],
        content_type=request.META['CONTENT_TYPE'],
        headers=headers,
        body=request.body,
    )


# -------------------------------------------------------------------------------------------------------------------
def index(request):
    logger.debug("index ({})".format(request.method))

    context = {"time": 0}
    return HttpResponse(render(request, "ddosdb/index.html", context))


# -------------------------------------------------------------------------------------------------------------------
def about(request):
    logger.debug("about ({})".format(request.method))
    context = {}
    return HttpResponse(render(request, "ddosdb/about.html", context))


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def help_page(request):
    logger.debug("help_page ({})".format(request.method))
    context = {}
    return HttpResponse(render(request, "ddosdb/help.html", context))


# -------------------------------------------------------------------------------------------------------------------
def signin(request):
    ip = _remote_ip(request)
    logger.info("Login request from {}".format(ip))

    if request.method == "POST":
        timeout = False
        timeout_sec = 0
        # Check failed logins in last 5 minutes

        fls = FailedLogin.objects.filter(ipaddress=ip, logindatetime__gt=timezone.now() - timedelta(seconds=300))
        logger.info("Failed login attempts from {} in the last 5 minutes: {}".format(ip, len(fls)))

        if len(fls) < 3:
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Remove old failed attempts from this ip older than 10 minutes
                # FailedLogin.objects.filter(ipaddress=ip, logindatetime__lte=timezone.now() - timedelta(minutes=10)).delete()

                login(request, user)
                if "next" in request.GET:
                    return redirect(request.GET["next"])
                else:
                    return redirect("index")
            else:
                logger.info("Login fail from {}".format(ip))
                fl = FailedLogin()
                fl.ipaddress = ip
                fl.logindatetime = timezone.now()
                fl.save()
                context = {"failed": True, "message": "Invalid username or password"}
                if len(fls) >= 2:
                    context["message"] = "Invalid username or password, wait 5 minutes"
        else:
            logger.info("Already too many failed attempts from {}, automatic fail".format(ip))
            fl = FailedLogin()
            fl.ipaddress = ip
            fl.logindatetime = timezone.now()
            fl.save()
            context = {"failed": True, "message": "Too many failed logins, wait 60 seconds"}
    else:
        context = {}

    return HttpResponse(render(request, "ddosdb/login.html", context))


# def request_access(request):
#     logger.debug("request_access ({})".format(request.method))
#
#     context = {
#         "error": False,
#         "success": False
#     }
#
#     if request.method == "POST":
#         captcha_verify = requests.post("https://www.google.com/recaptcha/api/siteverify",
#                                        data={"secret": settings.RECAPTCHA_PRIVATE_KEY,
#                                              "response": request.POST["g-recaptcha-response"]})
#         captcha_okay = demjson.decode(captcha_verify.text)["success"]
#
#         if captcha_okay:
#             access_request = AccessRequest(first_name=request.POST["first-name"],
#                                            last_name=request.POST["last-name"],
#                                            email=request.POST["email"],
#                                            institution=request.POST["institution"],
#                                            purpose=request.POST["purpose"])
#
#             try:
#                 send_mail("DDoSDB Access Request",
#                           """
#                 First name: {first_name}
#                 Last name: {last_name}
#                 Email: {email}
#                 Institution: {institution}
#                 Purpose: {purpose}
#                 """.format(first_name=access_request.first_name,
#                            last_name=access_request.last_name,
#                            email=access_request.email,
#                            institution=access_request.institution,
#                            purpose=access_request.purpose),
#                           "noreply@ddosdb.org",
#                           [settings.ACCESS_REQUEST_EMAIL])
#
#                 access_request.save()
#
#                 context["success"] = True
#             except (SMTPException, ConnectionRefusedError) as e:
#                 context["error"] = e
#         else:
#             context["error"] = "Invalid captcha"
#
#     return HttpResponse(render(request, "ddosdb/request-access.html", context))
#


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def account(request):
    logger.debug("account ({})".format(request.method))

    user: User = request.user
    # token, created = Token.objects.get_or_create (user=request.user)
    # logger.debug(token)

    context = {
        "user": user,
        "permissions": user.get_all_permissions(),
        # "token": token.key,
        "success": "",
        "error": ""
    }

    if request.method == "POST":
        if "email" in request.POST:
            email = request.POST["email"].strip()

            if email != user.email:
                if User.objects.filter(email=email).exists():
                    context["error"] = "There already is a user with this email address"
                else:
                    try:
                        validate_email(email)
                        user.email = email
                        user.username = email
                        user.save()

                        user = authenticate(request, username=email)
                        context["success"] = "Successfully changed your email address"
                    except ValidationError:
                        context["error"] = "This is not a valid email address"

        elif "new-password" in request.POST:
            if request.POST["new-password"] == request.POST["new-password2"]:
                if user.check_password(request.POST["current-password"]):
                    user.set_password(request.POST["new-password"])
                    user.save()

                    user = authenticate(request, username=user.username, password=request.POST["new-password"])
                    context["success"] = "Successfully changed your password"
                else:
                    context["error"] = "The provided current password is incorrect"
            else:
                context["error"] = "The new passwords are not the same"

    return HttpResponse(render(request, "ddosdb/account.html", context))


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def tokens(request):
    logger.debug("tokens ({})".format(request.method))

    user_perms = request.user.get_user_permissions()
    group_perms = request.user.get_group_permissions()

    # make a combined set (a set cannot contain duplicates)
    permissions = user_perms | group_perms

    if request.method == "GET":
        user: User = request.user

        def token_date(token: MultiToken):
            return token.created

        tokens = list(MultiToken.objects.filter(user=request.user))
        tokens.sort(key=token_date, reverse=True)
        logger.debug(tokens)
        # token, created = Token.objects.get_or_create (user=request.user)
        # logger.debug(token)

        context = {
            "user": user,
            "permissions": user.get_all_permissions(),
            "tokens": tokens,
            "success": "",
            "error": ""
        }
        return HttpResponse(render(request, "ddosdb/tokens.html", context))

    if request.method == "POST":
        if "django_rest_multitokenauth.add_multitoken" not in permissions:
            raise PermissionDenied()

        description='New Token'
        if "description" in request.POST:
            descr = request.POST["description"].strip()
            if len(descr) > 0:
                description = descr

        token = MultiToken.objects.create(
            user=request.user,
            user_agent=description,
            last_known_ip=request.META.get('REMOTE_ADDR'),
        )

    return redirect("/tokens")


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def delete_token(request):
    key = ""
    if "key" in request.GET:
        key = request.GET['key']
    logger.debug("Delete token ({})".format(key))

    user_perms = request.user.get_user_permissions()
    group_perms = request.user.get_group_permissions()

    # make a combined set (a set cannot contain duplicates)
    permissions = user_perms | group_perms

    if "django_rest_multitokenauth.delete_multitoken" not in permissions:
        raise PermissionDenied()

    # User is allowed to delete tokens. But do check first wether the specified token belongs to this user.
    token: MultiToken = MultiToken.objects.filter(user=request.user, key=key)
    logger.debug(token)

    if len(token) == 1:
        token[0].delete()

    return redirect("/tokens")


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def signout(request):
    logger.debug("signout ({})".format(request.method))

    logout(request)
    return redirect("index")


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def details(request):
    logger.debug("details ({})".format(request.method))

    pp = pprint.PrettyPrinter(indent=4)

    start = time.time()
    context = {
        "results": [],
        "time": 0,
        "error": ""
    }

    if "key" in request.GET:
        key = request.GET["key"]
        context["key"] = key

        start = time.time()

        try:
            results = _search({'key': key}, {'_id': 0})
            context["results"] = results
        except Exception as e:
            context["error"] = "Invalid query: " + str(e)

        context["time"] = time.time() - start

        return HttpResponse(render(request, "ddosdb/details.html", context))
    else:
        return redirect("/overview")


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def download(request):
    logger.debug("details ({})".format(request.method))

    pp = pprint.PrettyPrinter(indent=4)

    start = time.time()
    context = {
        "results": [],
        "time": 0,
        "error": ""
    }

    if "key" in request.GET:
        key = request.GET["key"]
        context["key"] = key

        start = time.time()

        try:
            results = _search({'key': key}, {'_id': 0})
            # context["results"] = results
            return HttpResponse(results, headers={
                'Content-Type': 'application/json',
                'Content-Disposition': 'attachment; filename="{}.json"'.format(key)})

        except Exception as e:
            context["error"] = "Invalid query: " + str(e)
    else:
        return redirect("/overview")


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def query(request):
    logger.debug("query ({})".format(request.method))

    # { key: {$regex: /^0.*/ } }
    pp = pprint.PrettyPrinter(indent=4)

    start = time.time()
    context = {
        "results": [],
        "comments": {},
        "q": "{}",
        "f": "{_id:0}",
        "o": "",
        "amount": 0,
        "error": "",
        "time": 0
    }

    if "q" in request.GET:
        f = context["f"]
        o = context["o"]

        if "f" in request.GET:
            f = context["f"] = request.GET["f"]
        if f == "":
            f = context["f"] = '{"_id":0}'

        if "o" in request.GET:
            o = context["o"] = request.GET["o"]

        q = context["q"] = request.GET["q"]
        if q == "":
            q = context["q"] = "{}"

        try:
            logger.info("Query: {}".format(q))
            qjson = demjson.decode(q)
        except Exception as e:
            logger.info("Error in query command: {}".format(q))
            context["error"] = "Error interpreting query: {}".format(str(e))
            context["time"] = time.time() - start
            context["results"] = []
            context["amount"] = 0
            return HttpResponse(render(request, "ddosdb/query.html", context))

        ojson = None
        try:
            logger.info("Order: {}".format(o))
            if len(o) > 0:
                ojson = demjson.decode(o)

        except Exception as e:
            logger.info("Error in Order specification: {}".format(o))
            context["error"] = "Error in Order specification: {}".format(str(e))
            context["time"] = time.time() - start
            context["results"] = []
            context["amount"] = 0
            return HttpResponse(render(request, "ddosdb/query.html", context))

        try:
            logger.info("Fields: {}".format(f))
            fjson = demjson.decode(f)
        except Exception as e:
            logger.info("Error in Fields specification: {}".format(f))
            context["error"] = "Error in Fields specification: {}".format(str(e))
            context["time"] = time.time() - start
            context["results"] = []
            context["amount"] = 0
            return HttpResponse(render(request, "ddosdb/query.html", context))

        try:
            # { 'attack_vector.dns_qry_name': {$regex: '\.'}  }
            # results = _search(qjson, fields={"_id":0})
            logger.info("q={}, o={}, f={}".format(qjson, ojson, fjson))
            results = _search(qjson, fields=fjson, order=ojson)
            # pp.pprint(results)
            context["time"] = time.time() - start
            logger.info("Results: {}".format(len(results)))
            context["results"] = results
            context["amount"] = len(results)
        except Exception as e:
            logger.info("Error in query command: {} ({})".format(q, str(e)))
            context["error"] = "Invalid query"
            context["time"] = time.time() - start
            context["results"] = []
            context["amount"] = 0

    return HttpResponse(render(request, "ddosdb/query.html", context))


# -------------------------------------------------------------------------------------------------------------------
def _cleanup_fp(fp_in):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(fp_in)

    return fp_in


# -------------------------------------------------------------------------------------------------------------------
@csrf_exempt
def upload_file(request):
    logger.debug("upload_file ({})".format(request.method))

    if request.method == "POST":
        #        print(pretty_request(request))
        #        if not all (k in request.META for k in ("HTTP_X_USERNAME","HTTP_X_PASSWORD","HTTP_X_FILENAME")):
        if not all(k in request.META for k in ("HTTP_X_USERNAME", "HTTP_X_PASSWORD")):
            response = HttpResponse()
            response.status_code = 401
            response.reason_phrase = "Invalid credentials or no permission"
            return response

        username = request.META["HTTP_X_USERNAME"]
        password = request.META["HTTP_X_PASSWORD"]
        filename = None
        if "HTTP_X_FILENAME" in request.META:
            filename = request.META["HTTP_X_FILENAME"]
        user = authenticate(request, username=username, password=password)

        #        print("user:{} - filename:{}".format(username, filename))

        if user is None or not user.has_perm("ddosdb.upload_fingerprint"):
            response = HttpResponse()
            response.status_code = 403
            response.reason_phrase = "Invalid credentials or no permission to upload fingerprints"
            logger.warning("upload_file with invalid credentials or no permission by user {}".format(username))
            return response

        if "json" in request.FILES:
            json_content = request.FILES["json"].read()
            data = None
            try:
                data = demjson.decode(json_content)
            except demjson.JSONDecodeError as e:
                logger.error("Fingerprint JSON decode error ({})".format(e))
                response = HttpResponse()
                response.status_code = 400
                response.reason_phrase = "JSON Decode Error ({})".format(e)

            # print(data)
            # Add key if not exists
            #        if "key" not in data:
            #            data["key"] = filename

            if "dst_ports" in data:
                data["dst_ports"] = [x for x in data["dst_ports"] if not math.isnan(x)]
            if "src_ports" in data:
                data["src_ports"] = [x for x in data["src_ports"] if not math.isnan(x)]

            # Enrich it all a bit
            # data["amplifiers_size"] = 0
            # data["attackers_size"] = 0

            # if "src_ips" in data:
            #     data["src_ips_size"] = len(data["src_ips"])
            #
            # if "amplifiers" in data:
            #     data["amplifiers_size"] = len(data["amplifiers"])
            #
            # if "attackers" in data:
            #     data["attackers_size"] = len(data["attackers"])

            if "tags" in data:
                data["tags"] = sorted(data["tags"])

            # data["ips_involved"] = data["amplifiers_size"] + data["attackers_size"]

            data["comment"] = ""

            # add username of submitter as well.
            # Probably best to have an optional separate field for contact information
            data["submitter"] = username

            # Add the timestamp it was submitted as well.
            # Useful for ordering in overview page.
            # Different databases (elasticsearch, MongoDB) treat this differently
            # Elasticsearch happily swallows this:
            # data["submit_timestamp"] = datetime.utcnow()
            # Whereas with MongoDB this leads toan IsoFormat object of some kind,
            # which doesn't display properly (leads to 'epoch = 0' 1970 displau)
            # So for MongoDB this works:
            # data["submit_timestamp"] = datetime.utcnow().isoformat()
            data["submit_timestamp"] = datetime.utcnow().isoformat()
            # 2021-04-11T01:38:32.950389

            # Assume normally all fingerprints can be shared.
            # Add some edit function for this later...
            data["shareable"] = False

            #        else:
            #            if "amplifiers" in data:
            #                data["src_ips"]      = data["amplifiers"]
            #                data["src_ips_size"] = len(data["src_ips"])
            #            else:
            #                data["src_ips"]      = []
            #                data["src_ips_size"] = 0

            # Bear in mind that the data format may change. Hence the order of these steps is important.
            # Enrich with ASN
            # data = (TeamCymru(data)).parse()
            print("Enrichment with AS # disabled")
            # Enrich with something
            # data = (Something(data)).parse()

            if filename is None:
                filename = data["key"]

            try:
                os.remove(settings.RAW_PATH + filename + ".json")
            except IOError:
                pass
            # Save JSON upload to file (not really needed to be honest)
            demjson.encode_to_file(settings.RAW_PATH + filename + ".json", data)

            logger.info("Fingerprint {}: {}".format(data["key"], data))

            _cleanup_fp(data)
            # JSON database insert
            try:
                _delete({'key': data['key']})
                _insert(data)
            except ServerSelectionTimeoutError:
                logger.error("ServerSelectionTimeoutError: could not reach MongoDB")
                response = HttpResponse()
                response.status_code = 500
                response.reason_phrase = "Error reaching MongoDB"
                return response

        if "pcap" in request.FILES:
            logger.info("pcap in request as well")
            try:
                os.remove(settings.RAW_PATH + filename + ".pcap")
            except IOError:
                pass

            # PCAP upload
            pcap_fp = open(settings.RAW_PATH + filename + ".pcap", "wb+")
            pcap_file = request.FILES["pcap"]
            for chunk in pcap_file.chunks():
                pcap_fp.write(chunk)

            pcap_fp.close()

            # Register record
            file_upload = FileUpload()
            file_upload.user = user
            file_upload.filename = filename
            file_upload.save()

        response = HttpResponse()
        response.status_code = 201
        return response

    else:
        response = HttpResponse()
        response.status_code = 405
        return response


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def overview(request):
    logger.debug("overview ({})".format(request.method))

    pp = pprint.PrettyPrinter(indent=4)

    user: User = request.user

    start = time.time()
    context = {
        "user": user,
        "permissions": user.get_all_permissions(),
        "results": [],
        "q": "",
        "p": 1,
        "o": "key",
        "so": "asc",
        "son": "desc",
        "error": "",
        "time": 0
    }

    if "q" in request.GET:
        context["q"] = request.GET["q"]
    if "o" in request.GET:
        context["o"] = request.GET["o"]
    if "so" in request.GET:
        context["so"] = request.GET["so"]
    if "son" in request.GET:
        context["son"] = request.GET["son"]

    logger.debug("context: {}".format(context))
    #    _search()

    try:
        context["headers"] = {
            #            "multivector_key"   : "multivector",
            "key": "key",
            "shareable": "Sync",
            "start_time": "start time",
            # "tags": "tags",
            "file_type": "capture",
            #            "duration_sec": "duration (seconds)",
            "total_packets": "# packets",
            #            "amplifiers_size"    : "IP's involved",
            #            "ips_involved": "IP's involved",
            "total_ips": "# IPs",
            "avg_bps": "bits/second",
            #            "avg_pps"           : "packets/second",
            #            "total_dst_ports": "# ports",
            "submit_timestamp": "submitted",
            "submitter": "by",
            "comment": "comment",
        }

        # Only retrieve the fields that we display
        fields = dict.fromkeys(list(context["headers"].keys()), 1)

        q = "*"
        query = {}
        if (context["q"]):
            q = context["q"]
        q_dis = q.split(':')
        if q_dis[0] == 'submitter':
            query = {"submitter": q_dis[1]}
        mdb_resp = _search(query=query, fields=fields)
        #        pp.pprint(mdb_resp)

        context["time"] = time.time() - start
        logger.debug("Search took {} seconds".format(context["time"]))
        #        results = [x["_source"] for x in response["hits"]["hits"]]
        results = mdb_resp
        logger.info("Got {} results".format(len(results)))

        #        pp.pprint(results)
        # Only do this if there are actual results...
        # and more than one, since one result does not need sorting
        if len(results) > 1:
            df = pd.DataFrame.from_dict(results)
            # pp.pprint(df)

            # Remove the headers that are not present in the results (e.g. due to changing formats)
            avail_cols = list(df.columns)
            for field in fields:
                if not field in avail_cols:
                    context["headers"].pop(field)
            o = [context["o"]][0]

            # Do a special sort if the column to sort by is 'submitter'
            # Since people can put e-mail addresses in starting with upper/lower case
            # Change the if statement to the following if you want to sort case insensitive
            # on any column with string values: if df.dtypes[o] == np.object:
            if o == "submitter":
                onew = o + "_tmp"
                df[onew] = df[o].str.lower()
                df.sort_values(by=onew, ascending=(context["so"] == "asc"), inplace=True)
                del df[onew]
            else:
                df.sort_values(by=o, ascending=(context["so"] == "asc"), inplace=True)

            # Make sure some columns are shown as int
            if "total_ips" in df.columns:
                df = df.astype({"total_ips": int})
            if "ips_involved" in df.columns:
                df = df.astype({"ips_involved": int})

            context["results"] = df.to_dict(orient='records')
        else:
            context["results"] = results

        # Count the number of shareable fingerprints
        context["syncfps"] = collections.Counter([d['shareable'] for d in results])[True]
        logger.debug("{} fingerprints allowed to be shared with other DDoSDBs".format(context["syncfps"]))

    except ServerSelectionTimeoutError as e:
        context["error"] = " ServerSelectionTimeoutError "
        logger.error(e)

    # Do something special in overview page if user is a super user
    if user.is_superuser:
        remotedbs = RemoteDdosDb.objects.filter(active=True)
        rdbs = []
        for remotedb in remotedbs:
            rdbs.append({"name": remotedb.name})
        context["remotedbs"] = rdbs

        misps = MISP.objects.filter(active=True)
        rdbs = []
        for misp in misps:
            rdbs.append({"name": misp.name})
        context["misps"] = rdbs

    return HttpResponse(render(request, "ddosdb/overview.html", context))


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def delete(request):
    logger.debug("delete ({})".format(request.method))

    pp = pprint.PrettyPrinter(indent=4)

    user: User = request.user

    start = time.time()
    context = {
        "user": user,
        "permissions": user.get_all_permissions(),
        "results": [],
        "q": "",
        "p": 1,
        "o": "key",
        "so": "asc",
        "son": "desc",
        "error": "",
        "time": 0
    }

    if "q" in request.GET:
        context["q"] = request.GET["q"]
    if "o" in request.GET:
        context["o"] = request.GET["o"]
    if "so" in request.GET:
        context["so"] = request.GET["so"]
    if "son" in request.GET:
        context["son"] = request.GET["son"]

    if "key" in request.GET:
        if "ddosdb.delete_fingerprint" in user.get_all_permissions():
            _delete({"key": request.GET["key"]})
            logger.info("User {} delete fingerprint {}".format(user.username, request.GET["key"]))
        else:
            logger.error("********************************************************")
            logger.error("********  delete request without permission ************")
            logger.error("********      THIS SHOULD NOT HAPPEN        ************")
            logger.error("********************************************************")

    extra = []
    if "q" in request.GET:
        extra.append("q=" + request.GET["q"])
    else:
        extra.append("q=")
    if "o" in request.GET:
        extra.append("o=" + request.GET["o"])
    if "so" in request.GET:
        extra.append("so=" + request.GET["so"])
    if "son" in request.GET:
        extra.append("son=" + request.GET["son"])

    extrastr = ""
    if len(extra) > 0:
        extrastr = "?" + "&".join(extra)
    return redirect("/overview{}".format(extrastr))


# -------------------------------------------------------------------------------------------------------------------
def remote_push_sync():
    # Do a Push sync
    # Get all the shareable fingerprints
    try:
        fingerprints = _search({'shareable': True}, {'_id': 0})
        fp_keys = [fp['key'] for fp in fingerprints]
        logger.info("Fingerprints to sync: {}".format(fp_keys))

    except ServerSelectionTimeoutError as e:
        logger.error("Could not setup a connection to MongoDB")
        response = HttpResponse()
        response.status_code = 503
        response.reason_phrase = "Database unavailable"
        return response

    remotedbs = RemoteDdosDb.objects.filter(active=True, push=True)
    logger.info(remotedbs)
    rdbs = []
    for rdb in remotedbs:
        logger.info("Contacting remote DDoSDB:{} @ {}".format(rdb, rdb.url))
        unk_fps = []
        try:
            r = requests.post("{}/unknown-fingerprints".format(rdb.url),
                              auth=(rdb.username, rdb.password),
                              json=fp_keys,
                              timeout=10, verify=rdb.check_cert)
            logger.info("status:{}".format(r.status_code))
            if r.status_code == 200:
                logger.info("Fingerprint keys unknown to {}: {}".format(rdb.name, r.json()))
                unk_fps = r.json()
                if len(unk_fps) > 0:
                    # fps_to_sync = []
                    # for (unk_fp in unk_fps):
                    fps_to_sync = list(filter(lambda fp: fp['key'] in unk_fps, fingerprints))
                    logger.debug("Fingerprints to sync: {}".format(fps_to_sync))

                    r = requests.post("{}/fingerprints".format(rdb.url),
                                      auth=(rdb.username, rdb.password),
                                      json=fps_to_sync,
                                      timeout=10, verify=rdb.check_cert)
            rdbs.append({"name": rdb.name,
                         "type": "push",
                         "status": r.status_code,
                         "status_reason": r.reason,
                         "unk_fps": unk_fps,
                         "unk_fps_nr": len(unk_fps),
                         })
            logger.info("Sync response:{}".format(r.status_code))
        except Exception as e:
            logger.info("{}".format(e))
            rdbs.append({"name": rdb.name,
                         "type": "push",
                         "status": 555,
                         "status_reason": "Connection failed",
                         "unk_fps": [],
                         "unk_fps_nr": 0,
                         })
            continue

    return rdbs


# -------------------------------------------------------------------------------------------------------------------
def remote_pull_sync():
    # Now do a Pull sync
    remotedbs = RemoteDdosDb.objects.filter(active=True, pull=True)
    logger.info(remotedbs)
    rdbs = []
    for rdb in remotedbs:
        fps_srch = _search(fields={'key': 1, "_id": 0})
        fps = [fp['key'] for fp in fps_srch]
        logger.info("Fingerprints I have: {}".format(fps))

        logger.info("Contacting remote DDoSDB:{} @ {}".format(rdb, rdb.url))
        unk_fps = []
        try:
            r = requests.get("{}/fingerprints".format(rdb.url),
                             auth=(rdb.username, rdb.password),
                             timeout=10, verify=rdb.check_cert)
            logger.debug("status:{}".format(r.status_code))
            if r.status_code == 200:
                logger.info("Fingerprints at {}: {}".format(rdb.name, r.json()))
                rem_fps = r.json()
                for rem_fp in rem_fps:
                    if not rem_fp in fps:
                        unk_fps.append(rem_fp)
                logger.info("Fingerprints to pull: {}".format(unk_fps))

                if len(unk_fps) > 0:
                    for unk_fp in unk_fps:
                        r = requests.get("{}/fingerprint/{}".format(rdb.url, unk_fp),
                                         auth=(rdb.username, rdb.password),
                                         timeout=10, verify=rdb.check_cert)
                        if r.status_code == 200:
                            fp = r.json()[0]
                            # pp.pprint(fp)
                            fp["shareable"] = False
                            # Set submit timestamp
                            fp["submit_timestamp"] = datetime.utcnow().isoformat()
                            if not 'comment' in fp:
                                fp['comment'] = ""
                            _insert(fp)
                            # file_upload = FileUpload()
                            # file_upload.user = user_perms["user"]
                            # file_upload.filename = fp["key"]
                            # file_upload.save()

                            # logger.info(fp)

                rdbs.append({"name": rdb.name,
                             "type": "pull",
                             "status": r.status_code,
                             "status_reason": r.reason,
                             "unk_fps": unk_fps,
                             "unk_fps_nr": len(unk_fps),
                             })

            logger.info("Sync response:{}".format(r.status_code))
        except Exception as e:
            logger.info("{}".format(e))
            rdbs.append({"name": rdb.name,
                         "type": "pull",
                         "status": 555,
                         "status_reason": "Connection failed",
                         "unk_fps": [],
                         "unk_fps_nr": 0,
                         })
            continue

    return rdbs


# -------------------------------------------------------------------------------------------------------------------
def remote_misp_push_sync():
    rmisps = []
    misps = MISP.objects.filter(active=True, push=True)
    logger.info(misps)

    try:
        fingerprints = _search({'shareable': True}, {'_id': 0})
        fp_keys = [fp['key'] for fp in fingerprints]
        logger.info("Fingerprints to sync: {}".format(fp_keys))

    except ServerSelectionTimeoutError as e:
        logger.error("Could not setup a connection to MongoDB")
        return []

    for misp in misps:
        logger.info("Contacting remote MISP:{} @ {}".format(misp.name, misp.url))
        try:
            known_fps = ddosdb.misp.get_misp_fingerprints(misp)
            unk_fps = []
            unk_fps_keys = []
            for fp in fingerprints:
                if not fp['key'] in known_fps:
                    unk_fps.append(fp)
                    unk_fps_keys.append(fp['key'])

            logger.info("MISP {} needs sync for {} fingerprints {}".format(misp.name, len(unk_fps_keys), unk_fps_keys))
            for fp in unk_fps:
                logger.debug("Syncing fingerprint {}".format(fp['key']))
                ddosdb.misp.add_misp_fingerprint(misp, fp)

            rmisps.append({"name": misp.name,
                           "type": "push",
                           "status": 200,
                           "status_reason": 'OK',
                           "unk_fps": unk_fps_keys,
                           "unk_fps_nr": len(unk_fps_keys),
                           })
        except Exception as e:
            logger.error("{}".format(e))
            rmisps.append({"name": misp.name,
                           "type": "push",
                           "status": 555,
                           "status_reason": 'Connection failed',
                           "unk_fps": [],
                           "unk_fps_nr": 0,
                           })

    return rmisps


# -------------------------------------------------------------------------------------------------------------------
def remote_misp_pull_sync():
    logger.warning('MISP pull sync not implemented')
    return []


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def remote_sync(request):
    logger.debug("remote_sync ({})".format(request.method))

    pp = pprint.PrettyPrinter(indent=4)
    user: User = request.user

    if not user.is_superuser:
        raise PermissionDenied()

    rdbs = remote_push_sync()
    rdbs += remote_pull_sync()
    logger.info(rdbs)

    context = {
        "user": user,
        "result": rdbs,
    }
    return HttpResponse(render(request, "ddosdb/remotesync.html", context))


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def misp_sync(request):
    logger.debug("misp_sync ({})".format(request.method))

    pp = pprint.PrettyPrinter(indent=4)
    user: User = request.user

    if not user.is_superuser:
        raise PermissionDenied()

    misps = remote_misp_push_sync()
    misps += remote_misp_pull_sync()
    logger.info(misps)

    context = {
        "user": user,
        "result": misps,
    }
    return HttpResponse(render(request, "ddosdb/mispsync.html", context))


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def toggle_shareable(request):
    logger.debug("toggle_shareable ({})".format(request.method))

    pp = pprint.PrettyPrinter(indent=4)

    user: User = request.user

    # Get the key from the request.
    if "key" in request.GET:
        key = request.GET["key"]
    else:
        return redirect('overview')

    shareable = False

    if "shareable" in request.GET:
        shareable = not strtobool(request.GET["shareable"])

    try:
        fp = _search_one({"key": key}, {"shareable": 1, "key": 1, "submitter": 1})
        if fp["submitter"] == user.username or user.is_superuser:
            logger.info("Setting key {} to Shareable={}".format(key, shareable))
            _update({'key': key}, {'$set': {"shareable": shareable}})
        else:
            raise PermissionDenied()
    except Exception as e:
        logger.error(e)
        response = HttpResponse()
        response.status_code = 503
        response.reason_phrase = "Database unavailable"
        return response

    extra = []
    if "q" in request.GET:
        extra.append("q=" + request.GET["q"])
    else:
        extra.append("q=")
    if "o" in request.GET:
        extra.append("o=" + request.GET["o"])
    if "so" in request.GET:
        extra.append("so=" + request.GET["so"])
    if "son" in request.GET:
        extra.append("son=" + request.GET["son"])

    extrastr = ""
    if len(extra) > 0:
        extrastr = "?" + "&".join(extra)
    return redirect("/overview{}".format(extrastr))


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def edit_comment(request):
    logger.debug("edit_comment ({})".format(request.method))

    pp = pprint.PrettyPrinter(indent=4)

    user: User = request.user
    context = {
        "user": user,
        "permissions": user.get_all_permissions(),
        "time": 0,
    }

    key = ""

    if request.method == "GET":
        # Get the key from the request.
        if "key" in request.GET:
            key = request.GET["key"]
            context["key"] = key
        else:
            return redirect('overview')

        mdb = MongoClient(settings.MONGODB).ddosdb.fingerprints

        try:
            fp = mdb.find_one({"key": key})
            logger.debug("Found key {} to edit comment".format(fp["key"]))
        except:
            logger.error("Could not setup a connection to MongoDB")
            response = HttpResponse()
            response.status_code = 503
            response.reason_phrase = "Database unavailable"
            return response

        if fp["submitter"] == user.username or user.is_superuser:
            context["node"] = fp
            return HttpResponse(render(request, "ddosdb/edit-comment.html", context))
        else:
            raise PermissionDenied()

    elif request.method == "POST":
        key = request.POST["key"]

        mdb = MongoClient(settings.MONGODB).ddosdb.fingerprints

        fp = mdb.find_one({"key": key}, {"comment": 1, "key": 1, "submitter": 1})
        if fp["submitter"] == user.username or user.is_superuser:
            try:
                logger.info("Setting comment for fingerprint {} to '{}'".format(key, request.POST["comment"]))
                mdb.find_one_and_update({'key': key}, {'$set': {"comment": request.POST["comment"]}})
            except Exception as e:
                logger.error(e)
                logger.error("Could not setup a connection to MongoDB")
                response = HttpResponse()
                response.status_code = 503
                response.reason_phrase = "Database unavailable"
                return response
        else:
            raise PermissionDenied()
        return redirect("overview")


# -------------------------------------------------------------------------------------------------------------------
def _auth_user_get_perms(request):
    logger.debug("_auth_user_get_perms")

    user_and_perms = {
        "user": None,
        "permissions": []
    }

    if not "HTTP_AUTHORIZATION" in request.META:
        return user_and_perms

    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token_type, _, credentials = auth_header.partition(' ')
    username, password = base64.b64decode(credentials).decode('utf-8').split(':')

    user = authenticate(request, username=username, password=password)

    if user is None:
        return user_and_perms

    user_and_perms["user"] = user
    user_perms = user.get_user_permissions()
    group_perms = user.get_group_permissions()

    # make a combined set (a set cannot contain duplicates)
    permissions = user_perms | group_perms

    # Now filter out everything but the ddosdb.* permissions
    ddosdb_permissions = []
    for p in permissions:
        if p.startswith("ddosdb."):
            ddosdb_permissions.append(p)
    user_and_perms["permissions"] = ddosdb_permissions

    return user_and_perms


# -------------------------------------------------------------------------------------------------------------------
@csrf_exempt
def my_permissions(request):
    logger.debug("my_permissions ({})".format(request.method))

    if request.method == "GET":

        user_perms = _auth_user_get_perms(request)

        if user_perms["user"] is None:
            response = HttpResponse()
            response.status_code = 401
            response.reason_phrase = "Invalid credentials or no permission"
            return response

        return JsonResponse({str(user_perms["user"]): user_perms["permissions"]}, safe=False)
    else:
        logger.warning("my_permissions: POST method for GET only request")
        response = HttpResponse()
        response.status_code = 405
        response.reason_phrase = "Use GET only for this call"
        return response


# -------------------------------------------------------------------------------------------------------------------
@csrf_exempt
def fingerprints(request):
    logger.debug("fingerprints ({})".format(request.method))

    if request.method == "GET":

        user_perms = _auth_user_get_perms(request)

        if user_perms["user"] is None or "ddosdb.view_fingerprint" not in user_perms["permissions"]:
            raise PermissionDenied()
        try:
            # Only return shareable fingerprints
            fps = _search({'shareable': True}, {'_id': 0})

            logger.debug(fps)
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
        user_perms = _auth_user_get_perms(request)

        if user_perms["user"] is None or "ddosdb.add_fingerprint" not in user_perms["permissions"]:
            response = HttpResponse()
            response.status_code = 401
            response.reason_phrase = "Invalid credentials or no permission"
            return response

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
            file_upload.user = user_perms["user"]
            file_upload.filename = fp["key"]
            file_upload.save()

        fps = demjson.decode(request.body)
        if type(fps) is list:
            for fp in fps:
                # Replace name in fingerprint with the name of the user submitting it
                # so as not to transfer usernames over different DBs
                fp["submitter"] = user_perms["user"].username
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
            fps["submitter"] = user_perms["user"].username
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

    else:
        response = HttpResponse()
        response.status_code = 405
        response.reason_phrase = "Only GET or POST supported"
        return response


# -------------------------------------------------------------------------------------------------------------------
@csrf_exempt
def unknown_fingerprints(request):
    logger.debug("unknown_fingerprints ({})".format(request.method))
    """Takes a list of fingerprint keys and returns the fingerprint keys not present in the database"""
    """Allowing caller to then only upload fingerprints not yet known by this DDoS-DB"""
    """This is a REST method accepting only POST calls with JSON body content (application/json)"""
    if request.method == "POST":

        # print(pretty_request(request))
        user_perms = _auth_user_get_perms(request)

        if user_perms["user"] is None or "ddosdb.view_fingerprint" not in user_perms["permissions"]:
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
    else:
        response = HttpResponse()
        response.status_code = 405
        response.reason_phrase = "Use POST method only for this call"
        return response


# -------------------------------------------------------------------------------------------------------------------
@csrf_exempt
def fingerprint(request, key):
    logger.debug("fingerprint ({})".format(request.method))
    if request.method == "GET":

        # print(pretty_request(request))
        user_perms = _auth_user_get_perms(request)

        if user_perms["user"] is None or "ddosdb.view_fingerprint" not in user_perms["permissions"]:
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
    else:
        response = HttpResponse()
        response.status_code = 405
        response.reason_phrase = "Use GET method only for this call"
        return response


# -------------------------------------------------------------------------------------------------------------------
@login_required()
def attack_trace(request, key):
    logger.debug("attack_trace ({}), key={}".format(request.method, key))
    file = ""
    for file_path in os.listdir(settings.RAW_PATH):
        filename, file_extension = os.path.splitext(file_path)
        if filename == key and not file_extension == ".json":
            file = file_path
            break

    if file != "":
        response = HttpResponse(content_type="application/octet-stream")
        response["X-Sendfile"] = settings.RAW_PATH + file
        response["Content-Disposition"] = "attachment; filename=" + file
        return response
    else:
        return HttpResponse("File not found")


# -------------------------------------------------------------------------------------------------------------------
@csrf_exempt
def remote_dbs(request):
    logger.debug("remote_dbs ({})".format(request.method))

    if request.method == "GET":

        user_perms = _auth_user_get_perms(request)

        if user_perms["user"] is None or not user_perms["user"].is_superuser:
            raise PermissionDenied()

        remotedbs = RemoteDdosDb.objects.filter(active=True)
        rdbs = []
        for rdb in remotedbs:
            rdbs.append({"name": rdb.name,
                         "api_url": rdb.api_url,
                         "username": rdb.username,
                         "password": rdb.password})
        return JsonResponse(rdbs, safe=False)
    else:
        response = HttpResponse()
        response.status_code = 405
        response.reason_phrase = "Only GET supported"
        return response


# -------------------------------------------------------------------------------------------------------------------
@csrf_exempt
def csp_report(request):
    logger.debug("csp_report ({})".format(request.method))

    pp = pprint.PrettyPrinter(indent=4)

    if request.method == "POST":
        logger.info(request.body)
        # report = demjson.decode(request.body)
        # logger.info(report)
        response = HttpResponse()
        response.status_code = 200
        return response

    else:
        logger.error("GET request on csp_report. Fishy...")
        response = HttpResponse()
        response.status_code = 405
        return response

# -------------------------------------------------------------------------------------------------------------------
