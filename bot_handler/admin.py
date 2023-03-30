from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from import_export import resources
from import_export.admin import ExportMixin
from import_export.fields import Field
from django.conf import settings

from rangefilter.filters import DateTimeRangeFilter
from django_celery_beat.models import (
    IntervalSchedule,
    CrontabSchedule,
    SolarSchedule,
    ClockedSchedule,
    PeriodicTask,
)

from bot_handler.models import Client, Task, UserTask, WithdrawalOrder, SiteSettings, \
    Proof, Validator, TokenPrice, Contract, StoredTransaction
from bot_handler.forms import UserTaskForm, MessageForm, TaskForm
from bot_handler.utils import broadcast_message, send_message_to_user
from bot_handler.filters import UserFilter, RefGreaterFilter, RefLessFilter

admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)
admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)


class UserTaskInline(admin.TabularInline):
    model = UserTask
    form = UserTaskForm
    extra = 0
    fields = ('task', 'completed', 'proof_text', 'proof_image')
    readonly_fields = ('task', 'proof_text', 'proof_image')
    can_delete = False

    def has_add_permission(self, request, obj):
        return False

    def proof_text(self, obj=None):
        if not obj:
            return None
        return obj.proof.text_answer

    def proof_image(self, obj=None):
        if not obj:
            return None
        return obj.proof.img_preview()


class ClientResource(resources.ModelResource):
    completed_tasks = Field()

    class Meta:
        model = Client
        fields = ['affiliate', 'user_id', 'tg_username', 'phone', 'discord_username', 'referrals',
                  'task_sum', 'balance', 'wallet', 'completed_tasks']
        export_order = fields

    def dehydrate_completed_tasks(self, client):
        completed_tasks = client.usertask_set.filter(completed=True).values_list('task_id', flat=True)
        return ', '.join(list(map(str, completed_tasks)))


@admin.register(Client)
class ClientAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('user_id', 'tg_username', 'phone', 'discord_username', 'task_sum', 'balance', 'unverified_balance', 'referrals')
    inlines = (UserTaskInline,)
    resource_class = ClientResource
    search_fields = ['tg_username']
    list_filter = (
        UserFilter,
        RefGreaterFilter,
        RefLessFilter,
    )

    actions = ['send_message', 'send_deny_message']

    def send_message(self, request, queryset):
        if 'apply' in request.POST:
            broadcast_message_text = request.POST["message"]
            bot_token = settings.BOT_TOKEN
            user_ids = [u.user_id for u in queryset]
            broadcast_message(bot_token, user_ids, broadcast_message_text)
            return HttpResponseRedirect(request.get_full_path())

        form = MessageForm(initial={'_selected_action': queryset.values_list('user_id', flat=True)})
        context = {
            'form': form,
            'items': queryset,
        }
        return render(request, "admin/broadcast_message.html", context)

    def send_deny_message(self, request, queryset):
        for client in queryset:
            bot_token = settings.BOT_TOKEN
            user_uncompleted_tasks = list(client.usertask_set.filter(completed=False).values_list('task__name', flat=True))
            message = "Could you please repeat your tasks: " + ", ".join(user_uncompleted_tasks)
            send_message_to_user(client.user_id, bot_token, message)

    def changelist_view(self, request, extra_context=None):
        return super(ClientAdmin, self).changelist_view(request, extra_context)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'published')
    form = TaskForm


class WithdrawalOrderResource(resources.ModelResource):

    class Meta:
        model = WithdrawalOrder
        fields = ['client__tg_username', 'withdrawal_sum', 'created', 'payed']
        export_order = fields


@admin.register(WithdrawalOrder)
class WithdrawalOrderAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ['client', '_wallet', 'withdrawal_sum', 'created', 'payed',]
    list_filter = (
        'payed',
        ('created', DateTimeRangeFilter),
    )
    resource_class = WithdrawalOrderResource

    actions = ['mark_as_payed', ]

    def _wallet(self, obj=None):
        if not obj:
            return None
        return obj.client.wallet

    def mark_as_payed(self, request, queryset):
        queryset.update(payed=True)
    mark_as_payed.description = 'Mark selected withdrawals as payed'


@admin.register(Proof)
class ProofAdmin(admin.ModelAdmin):

    list_display = ['__str__', '_task_name', '_user']
    readonly_fields = ('img_preview',)

    def _task_name(self, obj=None):
        if not hasattr(obj, 'usertask'):
            return None
        return obj.usertask.task.name

    def _user(self, obj=None):
        if not hasattr(obj, 'usertask'):
            return None
        return obj.usertask.client.tg_username


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'withdrawal_min_amount', 'referral_cost')


@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ('client', 'task', 'completed')
    list_filter = (
        'task',
    )
    search_fields = ('client__tg_username', )


@admin.register(Validator)
class ValidatorAdmin(admin.ModelAdmin):
    pass


@admin.register(TokenPrice)
class TokenPriceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'price')


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('chain', 'hash')


@admin.register(StoredTransaction)
class StoredTransactionAdmin(admin.ModelAdmin):
    list_display = ('trx_hash',)
