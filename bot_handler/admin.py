from django.contrib import admin

from bot_handler.models import Client, Task, UserTask, WithdrawalOrder, SiteSettings


class UserTaskInline(admin.TabularInline):
    model = UserTask

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


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'tg_username', 'phone', 'discord_username', 'task_sum', 'balance')
    inlines = (UserTaskInline,)




@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'published')


@admin.register(WithdrawalOrder)
class WithdrawalOrderAdmin(admin.ModelAdmin):
    pass


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'withdrawal_min_amount', 'referral_cost')


@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ('client', 'task', 'completed')
