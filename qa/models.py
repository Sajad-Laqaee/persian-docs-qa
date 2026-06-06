from django.db import models


class Conversation(models.Model):
    title = models.CharField(max_length=255, blank=True, verbose_name="Conversation title")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"Conversation #{self.id}"


class Question(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="questions",
        null=True,
        blank=True,
        verbose_name="Conversation",
    )
    text = models.TextField(verbose_name="Question text")

    # answer
    answer = models.TextField(blank=True, verbose_name="Generated answer")

    # retrieval metadata
    search_mode = models.CharField(max_length=20, default="hybrid")
    retrieved_chunks = models.JSONField(null=True, blank=True, verbose_name="Retrieved chunks")
    sources = models.JSONField(null=True, blank=True, verbose_name="Sources")

    # metrics
    total_duration_sec = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Question and Answer"
        verbose_name_plural = "Question history"
        ordering = ["-created_at"]

    def __str__(self):
        return self.text[:50]