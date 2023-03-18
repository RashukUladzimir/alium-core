import uuid
import re

from django.utils import timezone
from django.db import models
from django.utils.html import format_html
from tinymce.models import HTMLField
from decimal import Decimal

from bot_handler.hash_validator import OkLinkValidator

PROOF_TYPE_CHOICES = (
    ('text', 'text'),
    ('photo', 'photo'),
)

CHAIN_SHORTNAME_CHOICES = (
    ('BSC', 'BSC'),
    ('ETH', 'ETH'),
    ('POLYGON', 'POLYGON'),
)


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

    is_verified_referral = models.BooleanField(
        default=False,

    )

    unverified_balance = models.DecimalField(
        max_digits=30,
        decimal_places=2,
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

    tasks = models.ManyToManyField(
        'Task',
        through='UserTask',
    )

    welcome_passed = models.BooleanField(
        default=False
    )

    def transfer_from_unverified(self, task):
        self.unverified_balance -= task.price
        self.balance += task.price
        self.task_sum += 1
        self.save(update_fields=['unverified_balance', 'balance', 'task_sum'])

    def transfer_to_unverified(self, task):
        self.unverified_balance += task.price
        self.balance -= task.price
        self.task_sum -= 1
        self.save(update_fields=['unverified_balance', 'balance', 'task_sum'])

    def increment_unverified_balance(self, task):
        self.unverified_balance += task.price
        self.save(update_fields=['unverified_balance'])

    def increment_ref_count(self):
        self.referrals += 1
        self.unverified_balance += SiteSettings.load().referral_cost
        self.save(update_fields=['referrals', 'unverified_balance'])

    def add_task_amount(self, task):
        self.balance += task.price
        self.task_sum += 1
        self.save(update_fields=['balance', 'task_sum'])

    def remove_task_amount(self, task):
        self.balance -= task.price
        self.task_sum -= 1
        self.save(update_fields=['balance', 'task_sum'])

    def add_ref_amount_to_balance(self):
        ref_cost = SiteSettings.load().referral_cost
        self.unverified_balance -= ref_cost
        self.balance += ref_cost
        self.save(update_fields=['balance', 'unverified_balance'])

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

    need_validation = models.BooleanField(
        default=False,
    )

    success_text = models.TextField()
    fail_text = models.TextField()
    proof_type = models.CharField(
        max_length=20,
        choices=PROOF_TYPE_CHOICES,
        null=False,
        blank=False,
    )

    validator = models.ForeignKey(
        'Validator',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    repeatable = models.BooleanField(
        default=False,
    )

    need_trx_proof = models.BooleanField(
        default=False,
    )
    trx_proof_chain = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=CHAIN_SHORTNAME_CHOICES,
    )

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

    def delete(self, using=None, keep_parents=False):
        if self.image_answer:
            self.image_answer.delete(save=False)
        super(Proof, self).delete(using, keep_parents)


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
    proof_exists = models.BooleanField(
        default=False
    )

    def delete_proof(self):
        try:
            if self.proof:
                self.proof.delete(None, True)
        except Exception as e:
            return None

    def validate_proof(self):
        proof = self.proof.text_answer
        validator = re.compile(self.task.validator.expression)
        return re.fullmatch(validator, proof) is not None

    def validate_transaction(self):
        trx_hash = self.proof.text_answer
        chain_name = self.task.trx_proof_chain

        resp = OkLinkValidator().get_transaction(trx_hash, chain_name)
        if not resp.ok:
            return False
        resp = resp.json()
        data = resp.get('data', [{}])[0]
        output_details = data.get('outputDetails', None)
        if output_details is None:
            return False

        contract_presents = False

        for output_detail in output_details:
            contract_list = Contract.objects.all().values_list('hash', flat=True)
            contract_hash = output_detail.get('outputHash')
            if contract_hash in contract_list:
                contract_presents = True

        if not contract_presents:
            return False

        token_transfer_data = data.get('tokenTransferDetails', None)
        if token_transfer_data is None:
            return False

        for transfer_data in token_transfer_data:
            if transfer_data.get('symbol') == 'ALM':
                amount = Decimal(transfer_data.get('amount', 0))
                rate = TokenPrice.objects.get(name='ALM').price
                if amount * rate > Decimal('10'):
                    StoredTransaction.objects.create(trx_hash=trx_hash)
                    return True
        return False


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


class Validator(models.Model):
    name = models.CharField(
        null=False,
        blank=False,
        max_length=30,
    )

    expression = models.TextField(
        null=False,
        blank=False,

    )

    def __str__(self):
        return self.name


class Contract(models.Model):
    chain = models.CharField(
        max_length=30,
        default=None,
        null=False,
        blank=False,
        choices=CHAIN_SHORTNAME_CHOICES
    )
    hash = models.CharField(
        primary_key=True,
        max_length=200,
    )


class TokenPrice(models.Model):
    name = models.CharField(
        primary_key=True,
        max_length=15
    )
    price = models.DecimalField(
        max_digits=30,
        decimal_places=10,
        null=False,
        blank=False,
        default=0,
    )

    def __str__(self):
        return self.name


class StoredTransaction(models.Model):
    trx_hash = models.CharField(
        unique=True,
        max_length=200
    )
