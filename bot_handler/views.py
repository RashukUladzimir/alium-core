from django.utils import timezone
from decimal import Decimal

from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser, FileUploadParser, DataAndFiles
from rest_framework.response import Response
from rest_framework import status

from bot_handler.serializers import ClientGetSerializer, TaskSerializer, WithdrawalOrderSerializer, \
    ProofSerializer, ClientPutSerializer
from bot_handler.models import Task, Client, SiteSettings


class ClientGetOrCreateView(RetrieveAPIView):
    serializer_class = ClientGetSerializer
    queryset = Client.objects.all()
    lookup_field = 'user_id'

    def retrieve(self, request, *args, **kwargs):
        existing_obj = self.queryset.filter(user_id=kwargs.get(self.lookup_field)).exists()

        if not existing_obj:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            if serializer.validated_data.get('affiliate'):
                serializer.validated_data.get('affiliate').increment_ref_count()
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED, )

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save()


class TaskListView(ListAPIView):
    serializer_class = TaskSerializer
    queryset = Task.objects.all()

    def list(self, request, *args, **kwargs):
        client = Client.objects.get(user_id=request.data.get('user_id'))
        client_completed_tasks = list(client.usertask_set.filter(completed=True).values_list('task', flat=True))
        unfollowed_tasks = Task.objects.exclude(id__in=client_completed_tasks)
        repeatable_tasks = Task.objects.filter(repeatable=True)

        result_qs = unfollowed_tasks.union(repeatable_tasks)

        page = self.paginate_queryset(result_qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(result_qs, many=True)
        return Response(serializer.data)


class TaskRetrieveView(RetrieveAPIView):
    serializer_class = TaskSerializer
    queryset = Task.objects.all()
    lookup_field = 'task_id'

    def retrieve(self, request, *args, **kwargs):
        client = Client.objects.get(user_id=request.data.get('user_id'))
        instance = client.usertask_set.filter(task_id=kwargs.get('task_id'), completed=False).first()
        if not instance:
            instance = client.usertask_set.create(task_id=kwargs.get('task_id'))

        serializer = self.get_serializer(instance.task)
        return Response(serializer.data)


class WithdrawalOrderCreateView(CreateAPIView):
    serializer_class = WithdrawalOrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client = serializer.validated_data.get('client')
        withdrawal_sum = serializer.validated_data.get('withdrawal_sum')
        withdrawal_min_amount = SiteSettings.load().withdrawal_min_amount

        if withdrawal_sum > client.balance:
            return Response('Not enough balance', status=status.HTTP_406_NOT_ACCEPTABLE)
        if withdrawal_sum < withdrawal_min_amount:
            return Response('Too small sum', status=status.HTTP_406_NOT_ACCEPTABLE)

        client.balance = client.balance - withdrawal_sum
        client.save()

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ProofCreateView(CreateAPIView):
    serializer_class = ProofSerializer
    parser_classes = (MultiPartParser, FileUploadParser)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        proof = self.perform_create(serializer)

        client_id = serializer.validated_data.get('client_id')
        client = Client.objects.get(user_id=client_id)
        user_task = client.usertask_set.filter(task_id=serializer.validated_data.get('task_id'), completed=False).first()
        user_task.delete_proof()
        user_task.proof = proof
        client.last_proof_send = timezone.now()
        client.save()

        if user_task.task.need_validation and user_task.task.validator is not None:
            if not user_task.validate_proof():
                user_task.save()
                return Response(serializer.data, status=status.HTTP_403_FORBIDDEN)

            user_task.completed = True
            user_task.proof_exists = True
            client.add_task_amount(user_task.task)
            if client.affiliate and not client.is_verified_referral:
                client.is_verified_referral = True
                client.save()
                client.affiliate.add_ref_amount_to_balance()

        if user_task.task.need_trx_proof and user_task.task.trx_proof_chain:
            if not user_task.validate_transaction():
                user_task.save()
                return Response(serializer.data, status=status.HTTP_403_FORBIDDEN)

            user_task.completed = True
            user_task.proof_exists = True
            client.add_task_amount(user_task.task)
            if client.affiliate and not client.is_verified_referral:
                client.is_verified_referral = True
                client.save()
                client.affiliate.add_ref_amount_to_balance()

        if not user_task.proof_exists:
            user_task.proof_exists = True
            client.increment_unverified_balance(user_task.task)

        user_task.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save()


class ClientUpdateView(UpdateAPIView):
    serializer_class = ClientPutSerializer
    queryset = Client.objects.all()
    lookup_field = 'user_id'

