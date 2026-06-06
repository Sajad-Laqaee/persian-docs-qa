from django.contrib import admin, messages
from .models import Document, DocumentChunk
from .services.indexer import index_document, delete_document_from_index


class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    readonly_fields = ("chunk_index", "content", "vector_id")
    can_delete = False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "is_indexed", "chunk_count", "created_at")
    list_filter = ("is_indexed",)
    search_fields = ("title", "full_text")
    readonly_fields = ("full_text", "is_indexed", "created_at", "updated_at")
    inlines = [DocumentChunkInline]
    actions = ["action_index", "action_reindex", "action_remove_index", "action_full_index"]

    @admin.display(description="Chunk count")
    def chunk_count(self, obj):
        return obj.chunks.count()

    @admin.action(description="🔵 Index in Qdrant")
    def action_index(self, request, queryset):
        total = 0
        for doc in queryset:
            try:
                total += index_document(doc)
            except Exception as e:
                self.message_user(
                    request, f"Error indexing '{doc.title}': {e}", messages.ERROR
                )
        self.message_user(
            request, f"✅ {total} chunks indexed.", messages.SUCCESS
        )

    @admin.action(description="🔄 Reindex (delete and index again)")
    def action_reindex(self, request, queryset):
        total = 0
        for doc in queryset:
            try:
                delete_document_from_index(doc)
                total += index_document(doc)
            except Exception as e:
                self.message_user(
                    request, f"Error reindexing '{doc.title}': {e}", messages.ERROR
                )
        self.message_user(
            request, f"🔄 {total} chunks reindexed.", messages.SUCCESS
        )

    @admin.action(description="🗑️ Remove from Qdrant index")
    def action_remove_index(self, request, queryset):
        for doc in queryset:
            try:
                delete_document_from_index(doc)
                doc.is_indexed = False
                doc.save(update_fields=["is_indexed"])
            except Exception as e:
                self.message_user(
                    request, f"Error removing '{doc.title}': {e}", messages.ERROR
                )
        self.message_user(request, "🗑️ Removed from index.", messages.SUCCESS)




    @admin.action(description="🚀 Full indexing (rebuild vocab + index all)")
    def action_full_index(self, request, queryset):
        from core.vectorstore import rebuild_bm25_vocab

        # 1) rebuild BM25 vocabulary once
        rebuild_bm25_vocab()

        # 2) index all documents (without repeated rebuild)
        total = 0
        for doc in queryset:
            try:
                total += index_document(doc, rebuild_vocab=False)
            except Exception as e:
                self.message_user(request, f"Error '{doc.title}': {e}", messages.ERROR)

        self.message_user(request, f"🚀 {total} chunks indexed.", messages.SUCCESS)


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("document", "chunk_index", "vector_id")
    search_fields = ("content",)


