from rest_framework import serializers
from .models import Question, Conversation


class AskRequestSerializer(serializers.Serializer):
    query = serializers.CharField(min_length=1)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
    limit = serializers.IntegerField(default=5, min_value=1, max_value=20)
    use_hybrid = serializers.BooleanField(default=True)
    document_id = serializers.IntegerField(required=False, allow_null=True)


class SourceSerializer(serializers.Serializer):
    score = serializers.FloatField()
    document_id = serializers.IntegerField(allow_null=True)
    document_title = serializers.CharField(allow_null=True)
    chunk_index = serializers.IntegerField(allow_null=True)
    preview = serializers.CharField()


class AskResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()
    sources = SourceSerializer(many=True)
    query = serializers.CharField()
    search_mode = serializers.CharField()
    conversation_id = serializers.IntegerField()
    question_id = serializers.IntegerField()


class QuestionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id", "conversation", "text", "answer",
            "search_mode", "sources", "total_duration_sec", "created_at",
        ]