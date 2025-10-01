import json
import time
from django.http import HttpRequest
from rest_framework import decorators
from rest_framework.response import Response

from .models import User, Transaction, Announcement, Advertisement


@decorators.api_view(http_method_names=["POST"])
def payme_callback(request: HttpRequest):
    user: User = None
    body = json.loads(request.body.decode())

    if body.get("method") == "CheckPerformTransaction":
        username = body.get("params", {}).get("account", {}).get("appid", "")

        user = User.objects.filter(username=username)

        if not user:
            return Response(
                {
                    "error": {
                        "code": -31050,
                        "message": {
                            "en": "User not found",
                            "ru": "User not found",
                            "uz": "Foydalanuvchi topilmadi",
                        },
                        "data": "id",
                    }
                }
            )

        user = user.first()

        return Response(
            {
                "jsonrpc": "2.0",
                "id": username,
                "result": {
                    "allow": True,
                    "additional": {
                        "id": username,
                        "name": f"{user.first_name} {user.last_name}"
                        if (user.first_name and user.last_name)
                        else "Astron foydalanuvchisi",
                        "balance": user.balance,
                    },
                },
            }
        )

    if body.get("method") == "CreateTransaction":
        username = body.get("params", {}).get("account", {}).get("appid", "")
        transaction_id = body.get("params", {}).get("id")
        amount = body.get("params", {}).get("amount", 1) / 100

        user = User.objects.filter(username=username).first()

        transaction = Transaction.objects.create(
            id=transaction_id, author=user, amount=amount, state=1
        )

        return Response(
            {
                "result": {
                    "create_time": body.get("params").get("time"),
                    "transaction": transaction.id,
                    "state": transaction.state,
                }
            }
        )
    
    if body.get("method") == "PerformTransaction":
        transaction_id = body.get("params", {}).get("id")

        transaction = Transaction.objects.filter(id=transaction_id)

        if not transaction:
            return Response({
                "error": {
                    "code": -31003
                }
            })
        
        transaction = transaction.first()
        transaction.author.balance = transaction.author.balance + transaction.amount
        transaction.author.save()
        transaction.state = 2
        transaction.save()

        return Response(
            {
                "result": {
                    "transaction": transaction_id,
                    "perform_time": int(time.time()),
                    "state": 2,
                }
            }
        )
    
    return Response({})


@decorators.api_view(http_method_names=["GET"])
def get_announcement(request: HttpRequest):
    announcement = Announcement.objects.last()
    if announcement:
        return Response({
            "content": announcement.content,
            "created": announcement.created
        })
    return Response({
        "content": None,
        "created": None
    })


@decorators.api_view(http_method_names=["POST"])
def telemetry(request: HttpRequest):
    data = request.data
    
    id = data.get("id", None)
    username = data.get("username", id)
    first_name = data.get("first_name")
    last_name = data.get("last_name")

    if not id:
        return Response({
            "status": "!ok"
        })

    user = User.objects.filter(id=id)

    if not user.exists():
        user = User.objects.create(
            id=id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            balance=0
        )
    
    else:
        user = user.first()

        user.first_name = first_name
        user.last_name = last_name
        user.save()

    return Response({
        "status": "ok"
    })


@decorators.api_view(http_method_names=["GET"])
def increment_receivers(request: HttpRequest):
    ads = request.GET.get("ads")

    if not ads:
        return Response({
            "status": "!ok"
        })
    
    ads = Advertisement.objects.filter(pk=ads)

    if not ads:
        return Response({
            "status": "!ok"
        })
    
    ads = ads.first()

    ads.receivers += 1
    ads.save()

    return Response({
        "status": "ok"
    })

