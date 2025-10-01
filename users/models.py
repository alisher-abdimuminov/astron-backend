import requests
from decouple import config
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser

from .manager import UserManager
from .worker import Worker


BOT_URL = config("BOT_URL")

ROLE = (
    ("admin", "Admin"),
    ("teacher", "O'qituvchi"),
    ("student", "Talaba"),
)
TRANSACTION_TYPE = (("income", "Kirim"), ("expense", "Chiqim"))
TRANSACTION_STATE = (
    (1, "To'lov yaratildi. Tasdiqlanishi kutilmoqda"),
    (2, "To'lov muvafaqqiyatli amalga oshirildi"),
    (-1, "To'lov bekor qilindi"),
    (-2, "To'lov tugallangandan keyin qaytarildi."),
    (3, "Yechib olindi"),
)
ADS_STATUS = (
    ("sending", "Yuborilmoqda..."),
    ("sended", "Yuborilgan"),
)


class User(AbstractUser):
    id = models.CharField(max_length=100, primary_key=True, verbose_name="ID")
    role = models.CharField(max_length=20, choices=ROLE, default="student", verbose_name="ROLE")
    balance = models.DecimalField(max_digits=100, decimal_places=2, verbose_name="Balans", default=0)
    first_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Ism")
    last_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Familiya")

    objects = UserManager()

    def __str__(self):
        return self.username


class Transaction(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=100, choices=TRANSACTION_TYPE, default="income")
    service = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    state = models.IntegerField(choices=TRANSACTION_STATE)
    amount = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.id
    

class Announcement(models.Model):
    content = models.TextField(verbose_name="Matn")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content
    

class Channel(models.Model):
    id = models.CharField(max_length=100, primary_key=True, verbose_name="ID")
    title = models.CharField(max_length=100, verbose_name="Nomi")
    is_verified = models.BooleanField(default=False, verbose_name="Tasdiqlangan")

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        try:
            response = requests.get(BOT_URL + "/verify-channel?channel=" + self.id)

            if response.json().get("data") == "administrator":
                self.is_verified = True
        except Exception as e:
            print(e)
        super().save(*args, **kwargs)
    

class Advertisement(models.Model):
    content = models.TextField(verbose_name="Matn")
    status = models.CharField(max_length=100, choices=ADS_STATUS, default="sending", verbose_name="Holati")
    receivers = models.IntegerField(default=0, verbose_name="Qabul qilganlar")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content
    

def send_ads(ads: Advertisement):
    users = User.objects.filter(role="student")
    for user in users:
        requests.get(BOT_URL + f"/send-message/?chat_id={user.id}&content={ads.content}&ads={ads.pk}")
    print(ads.receivers)
    ads.status = "sended"
    ads.save(update_fields=["status"])
    
@receiver(post_save, sender=Advertisement)
def send_ads_receiver(sender, instance: Advertisement, created, **kwargs):
    if created:
        worker = Worker(send_ads, ads=instance)
        worker.start()
