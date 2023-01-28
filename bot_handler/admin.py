from django.contrib import admin
from import_export import resources
from import_export.admin import ExportMixin
from import_export.fields import Field

from rangefilter.filters import DateTimeRangeFilter

from bot_handler.models import Client, Task, UserTask, WithdrawalOrder, SiteSettings
from bot_handler.forms import UserTaskForm


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
        return obj.proof.image_answer


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
    list_display = ('user_id', 'tg_username', 'phone', 'discord_username', 'task_sum', 'balance')
    inlines = (UserTaskInline,)
    resource_class = ClientResource

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'published')


@admin.register(WithdrawalOrder)
class WithdrawalOrderAdmin(admin.ModelAdmin):
    list_display = ['client', 'withdrawal_sum', 'created', 'payed']
    list_filter = (
        'payed',
        ('created', DateTimeRangeFilter),
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'withdrawal_min_amount', 'referral_cost')


@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ('client', 'task', 'completed')
