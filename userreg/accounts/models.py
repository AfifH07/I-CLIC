from django.db import models

# Create your models here.
from django.conf import settings

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    GENDER_CHOICES = (
        (0, 'Laki-laki'),
        (1, 'Perempuan'),
    )

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    umur = models.IntegerField()
    gender = models.IntegerField(choices=GENDER_CHOICES)
    password = models.CharField(max_length=128)  # Password akan di-hash

    def __str__(self):
        return self.username
class Prediction(models.Model):
    prediction_id = models.AutoField(primary_key=True)  # <-- ini primary key, bukan 'id'
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    prediction_name = models.CharField(max_length=255)
    confidence_score = models.FloatField()
    predicted_at = models.DateTimeField()

    def __str__(self):
        return self.prediction_name

    class Meta:
        db_table = 'predictions'  # pakai tabel yang sudah ada di DB
        managed = False  # opsional, jika kamu tidak ingin Django mengatur tabel ini (tidak bikin/migrate)

    
class Article(models.Model):
    article_id = models.AutoField(primary_key=True)  # <- Tambahkan ini!
    title = models.CharField(max_length=255)
    content = models.TextField()
    prediction_id = models.IntegerField()
    date_scraping = models.DateTimeField(default=timezone.localtime)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'articles'