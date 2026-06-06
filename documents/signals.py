# documents/signals.py

import logging
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete


from .models import Document, DocumentChunk
from .services.docx_parser import extract_text_from_docx
from .services.chunker import chunk_text

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Document)
def process_document_on_save(sender, instance: Document, created, **kwargs):
    """
    After saving a document:
    1. If it has a file and text is empty → extract text
    2. Create chunks
    (Qdrant indexing will be added in day 3)
    """
    # prevent infinite recursion using a flag
    if getattr(instance, "_processing", False):
        return

    if not instance.file:
        return

    # skip reprocessing if already done (unless file changed)
    if instance.full_text and instance.chunks.exists():
        return

    try:
        # 1) extract text
        file_path = instance.file.path
        text = extract_text_from_docx(file_path)

        # 2) create chunks
        chunks = chunk_text(text)

        # 3) save
        instance._processing = True
        instance.full_text = text
        instance.is_indexed = False  # not indexed in Qdrant yet
        instance.save(update_fields=["full_text", "is_indexed"])

        # delete old chunks and recreate
        instance.chunks.all().delete()
        DocumentChunk.objects.bulk_create([
            DocumentChunk(
                document=instance,
                chunk_index=idx,
                content=chunk,
            )
            for idx, chunk in enumerate(chunks)
        ])

        logger.info(f"Document '{instance.title}' processed: {len(chunks)} chunks.")

    except Exception as e:
        logger.error(f"Error processing document '{instance.title}': {e}")
    finally:
        instance._processing = False


@receiver(pre_delete, sender=Document)
def remove_document_from_qdrant(sender, instance: Document, **kwargs):
    """Before deleting a document, remove it from Qdrant as well."""
    try:
        from .services.indexer import delete_document_from_index
        delete_document_from_index(instance)
    except Exception as e:
        logger.error(f"Error removing '{instance.title}' from Qdrant: {e}")