from django.db import models


class Document(models.Model):
    title = models.CharField(max_length=255, verbose_name="Title")
    file = models.FileField(
        upload_to="documents/",
        verbose_name="DOCX file",
        blank=True,
        null=True,
    )
    full_text = models.TextField(
        blank=True,
        verbose_name="Full text",
        help_text="Automatically extracted from file",
    )
    is_indexed = models.BooleanField(default=False, verbose_name="Indexed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks",
        verbose_name="Document",
    )
    chunk_index = models.PositiveIntegerField(verbose_name="Chunk number")
    content = models.TextField(verbose_name="Chunk text")
    # point_id stored in Qdrant (for delete/update)
    vector_id = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Document chunk"
        verbose_name_plural = "Document chunks"
        ordering = ["document", "chunk_index"]
        unique_together = ("document", "chunk_index")

    def __str__(self):
        return f"{self.document.title} - chunk {self.chunk_index}"