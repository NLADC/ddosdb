import math
import os
import time
from smtplib import SMTPException
import demjson
import requests
import base64
from datetime import datetime
import collections
import pprint
import pandas as pd
from distutils.util import strtobool
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from pymongo import ReturnDocument
import logging

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import HttpResponse
from django.shortcuts import render, redirect, reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from django.core.exceptions import PermissionDenied
#from ddosdb.enrichment.team_cymru import TeamCymru
from ddosdb.models import Query, AccessRequest, Blame, FileUpload, RemoteDdosDb

from ddosdb.database import Database
#__mdb__ = MongoClient("mongodb://"+settings.MONGODB, serverSelectionTimeoutMS=100).ddosdb.fingerprints

Database.initialize()

logger = logging.getLogger(__name__)

def _mdb():
    return Database.getDB()


def _insert(data):
    _mdb().insert(data)


def _search(query=None, fields=None):
    result = list(_mdb().find(query, fields))
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

def index(request):
    logger.debug("index ({})".format(request.method))

    context = {"time": 0}
    return HttpResponse(render(request, "ddosdb/index.html", context))


def about(request):
    logger.debug("about ({})".format(request.method))
    context = {}
    return HttpResponse(render(request, "ddosdb/about.html", context))


def help_page(request):
    logger.debug("help_page ({})".format(request.method))
    context = {}
    return HttpResponse(render(request, "ddosdb/help.html", context))


def signin(request):
    logger.debug("signin ({})".format(request.method))

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if "next" in request.GET:
                return redirect(request.GET["next"])
            else:
                return redirect("index")
        else:
            context = {"failed": True}
    else:
        context = {}

    return HttpResponse(render(request, "ddosdb/login.html", context))


def request_access(request):
    logger.debug("request_access ({})".format(request.method))

    context = {
        "error": False,
        "success": False
    }

    if request.method == "POST":
        captcha_verify = requests.post("https://www.google.com/recaptcha/api/siteverify",
                                       data={"secret": settings.RECAPTCHA_PRIVATE_KEY,
                                             "response": request.POST["g-recaptcha-response"]})
        captcha_okay = demjson.decode(captcha_verify.text)["success"]

        if captcha_okay:
            access_request = AccessRequest(first_name=request.POST["first-name"],
                                           last_name=request.POST["last-name"],
                                           email=request.POST["email"],
                                           institution=request.POST["institution"],
                                           purpose=request.POST["purpose"])

            try:
                send_mail("DDoSDB Access Request",
                          """
                First name: {first_name}
                Last name: {last_name}
                Email: {email}
                Institution: {institution}
                Purpose: {purpose}
                """.format(first_name=access_request.first_name,
                           last_name=access_request.last_name,
                           email=access_request.email,
                           institution=access_request.institution,
                           purpose=access_request.purpose),
                          "noreply@ddosdb.org",
                          [settings.ACCESS_REQUEST_EMAIL])

                access_request.save()

                context["success"] = True
            except (SMTPException, ConnectionRefusedError) as e:
                context["error"] = e
        else:
            context["error"] = "Invalid captcha"

    return HttpResponse(render(request, "ddosdb/request-access.html", context))


@login_required()
def account(request):
    logger.debug("account ({})".format(request.method))

    user: User = request.user
    context = {
        "user": user,
        "permissions": user.get_all_permissions(),
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
                    context["error"] = "The current password is incorrect"
            else:
                context["error"] = "The passwords are not the same"

    return HttpResponse(render(request, "ddosdb/account.html", context))


@login_required()
def signout(request):
    logger.debug("signout ({})".format(request.method))

    logout(request)
    return redirect("index")


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

        try:
            results = _search({'key': key}, {'_id': 0})
            context["results"] = results
        except Exception as e:
            context["error"] = "Invalid query: " + str(e)

        return HttpResponse(render(request, "ddosdb/details.html", context))
    else:
        return redirect("/overview")


@login_required()
def query(request):
    logger.debug("query ({})".format(request.method))

    pp = pprint.PrettyPrinter(indent=4)

    start = time.time()
    context = {
        "results": [],
        "comments": {},
        "q": "",
        "p": 1,
        "o": "_score",
        "pages": range(1, 1),
        "amount": 0,
        "error": "",
        "time": 0
    }

    if "q" in request.GET:
        if "p" in request.GET:
            context["p"] = int(request.GET["p"])
        if "o" in request.GET:
            context["o"] = request.GET["o"]

        q = context["q"] = request.GET["q"]

        try:
            # results = _search({'key': q}, {'_id': 0})
#            results = _search( query=None, fields={'_id': 0})
            logger.info("Query: {}".format(q))
            results = _search({"$text": {"$search": q}})
            logger.info("Results: {}".format(results))
            context["results"] = results
            context["amount"] = len(results)
        #     es = Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)
        #     response = es.search(index="ddosdb", q=q, from_=offset, size=10, sort=context["o"])
        #     context["time"] = time.time() - start
        #
        #     results = [x["_source"] for x in response["hits"]["hits"]]
        #     context["amount"] = response["hits"]["total"]["value"]
        #     context["pages"] = range(1, int(math.ceil(context["amount"] / 10)) + 1)
        #
        #     #            for x in results:
        #     #                if "comments" in x:
        #     #                    context["comments"][x["key"]] = x.pop("comments", None)
        #
        #     def clean_result(x):
        #         # Remove the start_timestamp attribute (if it exists)
        #         x.pop("start_timestamp", None)
        #
        #         #                for y in x["src_ips"]:
        #         #                    y.pop("as", None)
        #         #                    y.pop("cc", None)
        #
        #         return x
        #
        #     results = map(clean_result, results)
        #     results = list(results)
        #
        #     if request.user.has_perm("ddosdb.view_blame"):
        #         for result in results:
        #             try:
        #                 result["blame"] = Blame.objects.get(key=result["key"]).to_dict()
        #             except ObjectDoesNotExist:
        #                 pass
        #
        #     context["results"] = results
        except Exception as e:
            context["error"] = "Invalid query: " + str(e)

    return HttpResponse(render(request, "ddosdb/query.html", context))

@login_required()
def query_old(request):
    start = time.time()
    context = {
        "results": [],
        "comments": {},
        "q": "",
        "p": 1,
        "o": "_score",
        "pages": range(1, 1),
        "amount": 0,
        "error": "",
        "time": 0
    }

    if "q" in request.GET:
        if "p" in request.GET:
            context["p"] = int(request.GET["p"])
        if "o" in request.GET:
            context["o"] = request.GET["o"]

        q = context["q"] = request.GET["q"]

        if context["p"] == 1:
            data_query = Query(query=q, user_id=request.user.id)
            data_query.save()

        try:
            offset = 10 * (context["p"] - 1)

            es = Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)
            response = es.search(index="ddosdb", q=q, from_=offset, size=10, sort=context["o"])
            context["time"] = time.time() - start

            results = [x["_source"] for x in response["hits"]["hits"]]
            context["amount"] = response["hits"]["total"]["value"]
            context["pages"] = range(1, int(math.ceil(context["amount"] / 10)) + 1)

            #            for x in results:
            #                if "comments" in x:
            #                    context["comments"][x["key"]] = x.pop("comments", None)

            def clean_result(x):
                # Remove the start_timestamp attribute (if it exists)
                x.pop("start_timestamp", None)

                #                for y in x["src_ips"]:
                #                    y.pop("as", None)
                #                    y.pop("cc", None)

                return x

            results = map(clean_result, results)
            results = list(results)

            if request.user.has_perm("ddosdb.view_blame"):
                for result in results:
                    try:
                        result["blame"] = Blame.objects.get(key=result["key"]).to_dict()
                    except ObjectDoesNotExist:
                        pass

            context["results"] = results
        except (SyntaxError, RequestError) as e:
            context["error"] = "Invalid query: " + str(e)

    return HttpResponse(render(request, "ddosdb/query.html", context))


# @login_required()
# def compare(request):
#     items = {}
#     similarities = {}
#     es = Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)
#
#     for key in request.GET.getlist("key"):
#         items[key] = es.get(index="ddosdb", doc_type="_doc", id=key)["_source"]
#
#     # for x in es.search(index="ddosdb", q="pcap", size=50)["hits"]["hits"]:
#     #     items[x["_id"]] = x["_source"]
#
#     for key in items:
#         similarities[key] = {}
#         my_set = set([x["ip"] for x in items[key]["src_ips"]])
#         for other_key in items:
#             other_set = set([x["ip"] for x in items[other_key]["src_ips"]])
#             similarities[key][other_key] = {
#                 "percentage": len(my_set.intersection(other_set)) / len(other_set),
#                 "fraction": str(len(my_set.intersection(other_set))) + "/" + str(len(other_set))
#             }
#
#     context = {
#         "similarities": similarities,
#         "items": items
#     }
#     return HttpResponse(render(request, "ddosdb/compare.html", context))


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
            # JSON enrichment
            json_content = request.FILES["json"].read()
            data = demjson.decode(json_content)
            # print(data)
            # Add key if not exists
            #        if "key" not in data:
            #            data["key"] = filename

            if "dst_ports" in data:
                data["dst_ports"] = [x for x in data["dst_ports"] if not math.isnan(x)]
            if "src_ports" in data:
                data["src_ports"] = [x for x in data["src_ports"] if not math.isnan(x)]

            # Enrich it all a bit
            data["amplifiers_size"] = 0
            data["attackers_size"] = 0

            if "src_ips" in data:
                data["src_ips_size"] = len(data["src_ips"])

            if "amplifiers" in data:
                data["amplifiers_size"] = len(data["amplifiers"])

            if "attackers" in data:
                data["attackers_size"] = len(data["attackers"])

            if "tags" in data:
                data["tags"] = sorted(data["tags"])

            data["ips_involved"] = data["amplifiers_size"] + data["attackers_size"]

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

    logger.info("context: {}".format(context))
    _search()

    try:
        # offset = 10 * (context["p"] - 1)

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
            "total_ips": "IP's involved",
            "avg_bps": "bits/second",
            #            "avg_pps"           : "packets/second",
#            "total_dst_ports": "# ports",
            "submit_timestamp": "submitted at",
            "submitter": "submitted by",
            "comment": "comment",
        }

        # Only retrieve the fields that we display
        fields = dict.fromkeys(list(context["headers"].keys()), 1)

        q = "*"
        if (context["q"]):
            q = context["q"]

        mdb_resp = _search(fields=fields)
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

    return HttpResponse(render(request, "ddosdb/overview.html", context))


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


@login_required()
def remote_sync(request):
    logger.debug("remote_sync ({})".format(request.method))

    pp = pprint.PrettyPrinter(indent=4)
    user: User = request.user

    if not user.is_superuser:
        raise PermissionDenied()

    context = {
        "user": user,
    }

    # Get all the shareable fingerprints
    try:
        response = _search({'shareable': True}, {'_id': 0})
        fp_keys = [fp['key'] for fp in response]
        logger.info("Fingerprints to sync: {}".format(fp_keys))

    except ServerSelectionTimeoutError as e:
        logger.error("Could not setup a connection to MongoDB")
        response = HttpResponse()
        response.status_code = 503
        response.reason_phrase = "Database unavailable"
        return response

    results = []
    remotedbs = RemoteDdosDb.objects.filter(active=True)
    logger.info(remotedbs)
    rdbs = []
    for rdb in remotedbs:
        logger.info(rdb)
        unk_fps = []
        try:
            r = requests.post("{}/unknown-fingerprints".format(rdb.url),
                              auth=(rdb.username, rdb.password),
                              json=fp_keys,
                              timeout=10)
            if r.status_code == 200:
                logger.debug(r.json())
                unk_fps = r.json()
                if len(unk_fps) > 0:
                    fps_to_sync = list(filter(lambda fp: fp['key'] in unk_fps, fingerprints))
                    plogger.info("Fingerprints to sync: {}".format(fps_to_sync))

                    r = requests.post("{}/fingerprints".format(rdb.url),
                                      auth=(rdb.username, rdb.password),
                                      json=fps_to_sync)
            rdbs.append({"name": rdb.name,
                         "status": r.status_code,
                         "status_reason": r.reason,
                         "unk_fps": unk_fps,
                         "unk_fps_nr": len(unk_fps),
                         })
        except Exception as e:
            logger.error(e)
            rdbs.append({"name": rdb.name,
                         "status": 555,
                         "status_reason": "Connection failed",
                         "unk_fps": [],
                         "unk_fps_nr": 0,
                         })
            continue


    context["result"] = rdbs
    return HttpResponse(render(request, "ddosdb/remotesync.html", context))


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
        fp = _search_one({"key": key}, {"shareable" : 1, "key" : 1, "submitter" : 1})
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

        fp = mdb.find_one({"key": key}, {"comment" : 1, "key" : 1, "submitter" : 1})
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


@csrf_exempt
def fingerprints(request):
    logger.debug("fingerprints ({})".format(request.method))

    """REST API Call"""
    """GET method will return list of keys for all fingerprints present in the database"""
    """can add query parameters to it if needed, e.g.:"""
    """curl -u username:password http://localhost:8000/fingerprints\?q=shareable:true"""
    """Uses Basic authentication and checks for \"ddosdb.view_fingerprint\" permissions"""
    """POST method will store all fingerprints present in the body"""
    """It will remove the shareable property (i.e. set it to False), to by default prevent it from transfering further """
    """Uses Basic authentication and checks for \"ddosdb.add_fingerprint\" permissions"""

    # curl -X POST -H "Content-Type: application/json" -u user:password -d @test.json http://localhost:8000/fingerprints
    if request.method == "GET":

        q = "*"
        if "q" in request.GET:
            q = request.GET["q"]

        user_perms = _auth_user_get_perms(request)

        if user_perms["user"] is None or "ddosdb.view_fingerprint" not in user_perms["permissions"]:
            raise PermissionDenied()
        try:
            # offset = 10 * (context["p"] - 1)
            # es = Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)
            # response = es.search(index="ddosdb", q=q, size=10000, _source="key")
            # results = [x["_source"]["key"] for x in response["hits"]["hits"]]
            fps = _search(fields={'key': 1})
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

        def insert(fp):
            # es.index(index="ddosdb", doc_type="_doc", id=fp["key"], body=fp, request_timeout=500)
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


@csrf_exempt
def csp_report(request):
    logger.debug("csp_report ({})".format(request.method))

    pp = pprint.PrettyPrinter(indent=4)

    if request.method == "POST":
        report = demjson.decode(request.body)
        logger.info(request.body)
        logger.info(report)
        response = HttpResponse()
        response.status_code = 200
        return response

    else:
        logger.warning("GET request on csp_report. Fishy...")
        response = HttpResponse()
        response.status_code = 405
        return response
