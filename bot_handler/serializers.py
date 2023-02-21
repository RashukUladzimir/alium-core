from rest_framework import serializers
from bot_handler.models import Client, Task, WithdrawalOrder, Proof


class ClientGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['user_id', 'tg_username', 'affiliate', 'welcome_passed', 'balance', 'referrals']


class ClientPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['discord_username', 'wallet', 'welcome_passed']


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'description', 'price', 'proof_type', 'name', 'success_text', 'fail_text', 'need_validation']


class WithdrawalOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalOrder
        fields = ['client', 'withdrawal_sum']


class ProofSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(write_only=True)

    task_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Proof
        fields = ['text_answer', 'image_answer', 'client_id', 'task_id']

    def create(self, validated_data):
        for key in ('client_id', 'task_id'):
            validated_data.pop(key, None)
        return super(ProofSerializer, self).create(validated_data)

