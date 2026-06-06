import time
import logging
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .models import Conversation, Question
from .serializers import (
    AskRequestSerializer, AskResponseSerializer, QuestionHistorySerializer,
)
from .services.rag_chain import generate_answer

logger = logging.getLogger(__name__)


class AskView(APIView):
    """Submit a question and get an answer based on documents."""

    @extend_schema(
        request=AskRequestSerializer,
        responses=AskResponseSerializer,
        summary="Submit question and generate RAG answer",
    )
    def post(self, request):
        serializer = AskRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        start = time.perf_counter()

        # conversation
        conv_id = data.get("conversation_id")
        if conv_id:
            try:
                conversation = Conversation.objects.get(id=conv_id)
            except Conversation.DoesNotExist:
                return Response(
                    {"detail": "Conversation not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            conversation = Conversation.objects.create(
                title=data["query"][:50]
            )

        # RAG
        try:
            result = generate_answer(
                query=data["query"],
                limit=data["limit"],
                use_hybrid=data["use_hybrid"],
                document_id=data.get("document_id"),
            )
        except Exception as e:
            logger.exception(f"Error generating answer: {e}")
            return Response(
                {"detail": "Error processing question."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        duration = round(time.perf_counter() - start, 3)

        # save history
        question = Question.objects.create(
            conversation=conversation,
            text=data["query"],
            answer=result["answer"],
            search_mode=result["search_mode"],
            retrieved_chunks=result["retrieved_chunks"],
            sources=result["sources"],
            total_duration_sec=duration,
        )

        response = {
            "answer": result["answer"],
            "sources": result["sources"],
            "query": data["query"],
            "search_mode": result["search_mode"],
            "conversation_id": conversation.id,
            "question_id": question.id,
        }
        return Response(response, status=status.HTTP_200_OK)


class HistoryListView(ListAPIView):
    """Question and answer history."""
    serializer_class = QuestionHistorySerializer

    def get_queryset(self):
        qs = Question.objects.all().order_by("-created_at")
        conv_id = self.request.query_params.get("conversation_id")
        if conv_id:
            qs = qs.filter(conversation_id=conv_id)
        return qs