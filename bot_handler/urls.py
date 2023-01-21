from django.urls import path

from bot_handler.views import ClientGetOrCreateView, TaskListView, TaskRetrieveView, WithdrawalOrderCreateView, ProofCreateView

urlpatterns = [
    path('get-user/<int:user_id>/', ClientGetOrCreateView.as_view(), name=''),
    path('tasks/', TaskListView.as_view(), name=''),
    path('tasks/<int:task_id>/', TaskRetrieveView.as_view()),

    path('proof/create/', ProofCreateView.as_view(),),

    path('clients/withdrawal/', WithdrawalOrderCreateView.as_view())
]