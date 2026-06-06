from django.urls import path
from .views import AskView, HistoryListView

urlpatterns = [
    path("ask/", AskView.as_view(), name="ask"),
    path("history/", HistoryListView.as_view(), name="history"),
]