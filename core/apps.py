from django.apps import AppConfig
import os


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        if os.environ.get("RUN_MAIN") == "true":
            from core.embeddings import get_embeddings
            from django.conf import settings
            try:
                get_embeddings()
                if settings.USE_RERANKER:
                    from core.reranker import get_reranker
                    get_reranker()  # warm-up reranker هم
            except Exception:
                pass