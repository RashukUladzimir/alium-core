from decimal import Decimal

from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status

from bot_handler.serializers import ClientGetSerializer, TaskSerializer, WithdrawalOrderSerializer, ProofSerializer
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

        page = self.paginate_queryset(unfollowed_tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(unfollowed_tasks, many=True)
        return Response(serializer.data)


class TaskRetrieveView(RetrieveAPIView):
    serializer_class = TaskSerializer
    queryset = Task.objects.all()
    lookup_field = 'task_id'

    def retrieve(self, request, *args, **kwargs):
        client = Client.objects.get(user_id=request.data.get('user_id'))
        instance, created = client.usertask_set.get_or_create(task_id=kwargs.get('task_id'))
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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client_id = serializer.validated_data.get('client_id')
        client = Client.objects.get(user_id=client_id)
        user_task = client.usertask_set.get(task_id=serializer.validated_data.get('task_id'))

        proof = self.perform_create(serializer)
        user_task.proof = proof
        user_task.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save()