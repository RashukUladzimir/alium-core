import uuid
from django.utils import timezone
from django.db import models
from django.utils.html import format_html
from tinymce.models import HTMLField


class Client(models.Model):
    affiliate = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    user_id = models.BigIntegerField(
        primary_key=True,
    )
    tg_username = models.CharField(
        max_length=32,
        null=True,
        blank=True,
    )
    phone = models.CharField(
        max_length=16,
        null=True,
        blank=True,
    )
    discord_username = models.CharField(
        max_length=32,
        null=True,
        blank=True,
    )
    referrals = models.IntegerField(
        default=0,
    )
    task_sum = models.IntegerField(
        default=0,
    )
    balance = models.DecimalField(
        max_digits=30,
        decimal_places=2,
        default=0,
    )
    wallet = models.CharField(
        max_length=250,
        null=True,
        blank=True,
    )
    referral_link = models.UUIDField(
        default=uuid.uuid4,
    )

    tasks = models.ManyToManyField(
        'Task',
        through='UserTask',
    )

    welcome_passed = models.BooleanField(
        default=False
    )

    def increment_ref_count(self):
        self.referrals += 1
        self.balance += SiteSettings.load().referral_cost
        self.save(update_fields=['referrals', 'balance'])

    def add_task_amount(self, task):
        self.balance = self.balance + task.price
        self.task_sum += 1
        self.save(update_fields=['balance', 'task_sum'])

    def remove_task_amount(self, task):
        self.balance = self.balance - task.price
        self.task_sum -= 1
        self.save(update_fields=['balance', 'task_sum'])

    def __str__(self):
        return '{} {}'.format(self.tg_username, self.user_id)


class Task(models.Model):
    published = models.DateTimeField(
        default=timezone.now,
    )
    name = models.CharField(
        max_length=30,
        default='Task name'
    )
    description = HTMLField()
    price = models.DecimalField(
        max_digits=30,
        decimal_places=2,
        default=0,
    )
    success_text = models.TextField()
    fail_text = models.TextField()
    proof_type = models.CharField(max_length=20)

    def __str__(self):
        return self.name


def image_folder(instance, filename):
    return 'photos/{}.jpg'.format(uuid.uuid4().hex)


class Proof(models.Model):
    text_answer = models.CharField(
        null=True,
        blank=True,
        max_length=100,
    )
    image_answer = models.ImageField(
        null=True,
        blank=True,
        upload_to=image_folder,
    )

    def img_preview(self):  # new
        return format_html('<img src="{}" style="max-width:200px; max-height:200px"/>'.format(self.image_answer.url))


class UserTask(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
    )
    completed = models.BooleanField(
        default=False,
    )
    proof = models.OneToOneField(
        Proof,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )


class WithdrawalOrder(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
    )
    withdrawal_sum = models.DecimalField(
        max_digits=20,
        decimal_places=2,
    )

    created = models.DateTimeField(
        default=timezone.now,
    )

    payed = models.BooleanField(
        default=False,
    )


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class SiteSettings(SingletonModel):
    withdrawal_min_amount = models.DecimalField(
        max_digits=30,
        decimal_places=2,
        default=5,
    )
    referral_cost = models.DecimalField(
        max_digits=30,
        decimal_places=2,
        default=0.15,
    )

    def __str__(self):
        return 'Site Setting'
