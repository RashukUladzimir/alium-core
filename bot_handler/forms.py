from django import forms

from bot_handler.models import UserTask


class UserTaskForm(forms.ModelForm):
    class Meta:
        model = UserTask
        fields = '__all__'

    def clean(self):
        if 'completed' in self.changed_data:
            client = self.cleaned_data.get('client')
            task = self.cleaned_data.get('id').task
            if self.cleaned_data.get('completed'):
                client.add_task_amount(task)
            else:
                client.remove_task_amount(task)


class MessageForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    message = forms.CharField(widget=forms.Textarea, required=False)
