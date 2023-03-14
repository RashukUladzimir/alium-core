from django import forms

from bot_handler.models import UserTask, Task


class UserTaskForm(forms.ModelForm):
    class Meta:
        model = UserTask
        fields = '__all__'

    def clean(self):
        if 'completed' in self.changed_data:
            client = self.cleaned_data.get('client')
            task = self.cleaned_data.get('id').task
            if self.cleaned_data.get('completed'):
                client.transfer_from_unverified(task)
                if client.affiliate and client.is_verified_referral is False:
                    client.is_verified_referral = True
                    client.affiliate.add_ref_amount_to_balance()
            else:
                client.transfer_to_unverified(task)


class MessageForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    message = forms.CharField(widget=forms.Textarea, required=False)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = '__all__'

    def clean(self):
        if self.cleaned_data.get('need_validation', False) and not self.cleaned_data.get('validator'):
            self.add_error('validator', error='Validator must be initialized')

        if self.cleaned_data.get('need_validation', False) and self.cleaned_data.get('need_trx_proof'):
            self.add_error('need_validation', error='Need Validation or Need Trx Proof')
            self.add_error('need_trx_proof', error='Need Validation or Need Trx Proof')

        if not self.cleaned_data.get('trx_proof_chain') and self.cleaned_data.get('need_trx_proof'):
            self.add_error('trx_proof_chain', 'Trx proof chain and Need trx proof must be defined')
            self.add_error('need_trx_proof', 'Trx proof chain and Need trx proof must be defined')

        if self.cleaned_data.get('trx_proof_chain') and self.cleaned_data.get('need_trx_proof', False) is False:
            self.add_error('need_trx_proof', 'Trx proof chain and Need trx proof must be defined')
            self.add_error('trx_proof_chain', 'Trx proof chain and Need trx proof must be defined')
