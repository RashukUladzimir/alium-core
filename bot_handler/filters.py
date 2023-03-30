from django.contrib import admin


class InputFilter(admin.SimpleListFilter):
    template = 'admin/input_filter.html'

    def lookups(self, request, model_admin):
        # Dummy, required to show the filter.
        return ((),)

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice


class UserFilter(InputFilter):
    parameter_name = 'affiliate'
    title = "affiliate"

    def queryset(self, request, queryset):
        if self.value() is not None:
            username = self.value()
            return queryset.filter(
                affiliate__tg_username=username
            )


class RefGreaterFilter(InputFilter):
    parameter_name = 'ref_gte'
    title = 'Referrals greater'

    def queryset(self, request, queryset):
        if self.value() is not None:
            value = self.value()
            return queryset.filter(
                referrals__gte=int(value)
            )


class RefLessFilter(InputFilter):
    parameter_name = 'ref_lte'
    title = 'Referrals greater'

    def queryset(self, request, queryset):
        if self.value() is not None:
            value = self.value()
            return queryset.filter(
                referrals__lte=int(value)
            )
