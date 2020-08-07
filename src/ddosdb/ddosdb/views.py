import math
import os
import time
from smtplib import SMTPException
import demjson
import requests

import pprint
import pandas as pd
import numpy as np

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError, NotFoundError

from ddosdb.enrichment.team_cymru import TeamCymru
from ddosdb.models import Query, AccessRequest, Blame, FileUpload


def index(request):
    print(request)
    context = {}
    return HttpResponse(render(request, "ddosdb/index.html", context))


def about(request):
    context = {}
    return HttpResponse(render(request, "ddosdb/about.html", context))


def help_page(request):
    context = {}
    return HttpResponse(render(request, "ddosdb/help.html", context))


def signin(request):
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
    logout(request)
    return redirect("index")


@login_required()
def query(request):
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
            context["amount"] = response["hits"]["total"]
            context["pages"] = range(1, int(math.ceil(context["amount"] / 10)) + 1)

#            for x in results:
#                if "comments" in x:
#                    context["comments"][x["key"]] = x.pop("comments", None)

            def clean_result(x):
                # Remove the start_timestamp attribute (if it exists)
                x.pop("start_timestamp", None)

                for y in x["src_ips"]:
                    y.pop("as", None)
                    y.pop("cc", None)


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


@login_required()
def compare(request):
    items = {}
    similarities = {}
    es = Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)

    for key in request.GET.getlist("key"):
        items[key] = es.get(index="ddosdb", doc_type="_doc", id=key)["_source"]

    # for x in es.search(index="ddosdb", q="pcap", size=50)["hits"]["hits"]:
    #     items[x["_id"]] = x["_source"]

    for key in items:
        similarities[key] = {}
        my_set = set([x["ip"] for x in items[key]["src_ips"]])
        for other_key in items:
            other_set = set([x["ip"] for x in items[other_key]["src_ips"]])
            similarities[key][other_key] = {
                "percentage": len(my_set.intersection(other_set)) / len(other_set),
                "fraction": str(len(my_set.intersection(other_set))) + "/" + str(len(other_set))
            }

    context = {
        "similarities": similarities,
        "items": items
    }
    return HttpResponse(render(request, "ddosdb/compare.html", context))


@login_required()
def fingerprint(request, key):
    file = settings.RAW_PATH + key + ".json"
    if os.path.isfile(file):
        response = HttpResponse(content_type="application/json")
        response["X-Sendfile"] = file
        response["Content-Disposition"] = "attachment; filename=" + key + ".json"
        return response
    else:
        return HttpResponse("File not found")


@login_required()
def attack_trace(request, key):
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
def upload_file(request):
    if request.method == "POST":
        username = request.META["HTTP_X_USERNAME"]
        password = request.META["HTTP_X_PASSWORD"]
        filename = request.META["HTTP_X_FILENAME"]
        user = authenticate(request, username=username, password=password)

        print("user:{} - filename:{}".format(username, filename))

        if user is None or not user.has_perm("ddosdb.upload_fingerprint"):
            response = HttpResponse()
            response.status_code = 403
            response.reason_phrase = "Invalid credentials or no permission to upload fingerprints"
            return response

        try:
            os.remove(settings.RAW_PATH + filename + ".json")
            os.remove(settings.RAW_PATH + filename + ".pcap")
        except IOError:
            pass

        # JSON enrichment
        json_content = request.FILES["json"].read()

        data = demjson.decode(json_content)

        # Add key if not exists
        if "key" not in data:
            data["key"] = filename

        data["dst_ports"] = [x for x in data["dst_ports"] if not math.isnan(x)]
        data["src_ports"] = [x for x in data["src_ports"] if not math.isnan(x)]

        data["src_ips_size"] = len(data["src_ips"])

        # Bear in mind that the data format may change. Hence the order of these steps is important.
        # Enrich with ASN
        data = (TeamCymru(data)).parse()
        # Enrich with something
        # data = (Something(data)).parse()

        # JSON upload
        demjson.encode_to_file(settings.RAW_PATH + filename + ".json", data)

        # JSON database insert
        es = Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)

        try:
            es.delete(index="ddosdb", doc_type="_doc", id=filename, request_timeout=500)
        except NotFoundError:
            pass
        except:
            print("Could not setup a connection to Elasticsearch")
            response = HttpResponse()
            response.status_code = 503
            response.reason_phrase = "Database unavailable"
            return response

        es.index(index="ddosdb", doc_type="_doc", id=filename, body=data, request_timeout=500)

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

    pp = pprint.PrettyPrinter(indent=4)

    start = time.time()
    context = {
        "results": [],
        "q": "",
        "p": 1,
        "o": "multivector_key",
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

    try:
        #offset = 10 * (context["p"] - 1)
        es = Elasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)
        context["headers"] = {
            "multivector_key"   : "multivector",
            "key"               : "key",
            "duration_sec"      : "duration (seconds)",
            "total_packets"     : "# packets",
            "avg_bps"           : "bits/second",
            "avg_pps"           : "packets/second",
            "total_dst_ports"   : "# ports",
            "submitter"         : "submitted by",
        }
        source = ','.join(list(context["headers"].keys()))

        q = "*"
        if (context["q"]
        ):
            q = context["q"]

        response = es.search(index="ddosdb", q=q, size=10000,  _source=source)

        context["time"] = time.time() - start

        results = [x["_source"] for x in response["hits"]["hits"]]

#        print(results)
        # Only do this if there are actual results...
        # and more than one, since one result does not need sorting
        if len(results) > 1 :
            df = pd.DataFrame.from_dict(results)
            o = [context["o"]][0]

            # Do a special sort if the column to sort by is 'submitter'
            # Since people can put e-mail addresses in starting with upper/lower case
            # Change if statement to the following if you want to sort case insensitive
            # on any column with string values: if df.dtypes[o] == np.object:
            if o == "submitter":
                onew = o+"_tmp"
                df[onew] = df[o].str.lower()
                df.sort_values(by=onew, ascending=(context["so"]=="asc"), inplace=True)
                del df[onew]
            else:
                df.sort_values(by=o, ascending=(context["so"]=="asc"), inplace=True)

            context["results"] = df.to_dict(orient='records')
        else:
            context["results"] = results

    except (SyntaxError, RequestError) as e:
        context["error"] = "Invalid query: " + str(e)

    return HttpResponse(render(request, "ddosdb/overview.html", context))
