from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from import_export import resources
from import_export.admin import ExportMixin
from import_export.fields import Field
from django.conf import settings

from rangefilter.filters import DateTimeRangeFilter

from bot_handler.models import Client, Task, UserTask, WithdrawalOrder, SiteSettings, \
    Proof, Validator
from bot_handler.forms import UserTaskForm, MessageForm
from bot_handler.utils import broadcast_message


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
    list_display = ('user_id', 'tg_username', 'phone', 'discord_username', 'task_sum', 'balance', 'unverified_balance')
    inlines = (UserTaskInline,)
    resource_class = ClientResource

    actions = ['send_message', ]

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

    def changelist_view(self, request, extra_context=None):
        return super(ClientAdmin, self).changelist_view(request, extra_context)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'published')


@admin.register(WithdrawalOrder)
class WithdrawalOrderAdmin(admin.ModelAdmin):
    list_display = ['client', '_wallet', 'withdrawal_sum', 'created', 'payed',]
    list_filter = (
        'payed',
        ('created', DateTimeRangeFilter),
    )

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


@admin.register(Validator)
class ValidatorAdmin(admin.ModelAdmin):
    pass
