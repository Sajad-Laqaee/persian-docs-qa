from django.contrib import admin
from .models import Conversation, Question


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_at")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "short_text", "conversation", "created_at")
    list_filter = ("search_mode", "created_at")
    search_fields = ("text", "answer")
    readonly_fields = (
        "text", "answer", "search_mode", "retrieved_chunks",
        "sources", "total_duration_sec", "created_at",
    )

    @admin.display(description="Question")
    def short_text(self, obj):
        return obj.text[:60]