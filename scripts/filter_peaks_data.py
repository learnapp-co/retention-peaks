import asyncio
from collections import defaultdict
from bson import json_util
from datetime import datetime
from typing import Optional
from src.models.heatmap import heatmap_peaks
from src.services.init_services import init_services


class HeatmapDeduplicationService:
    def __init__(self):
        self.collection = heatmap_peaks

    async def fetch_all_documents(self):
        return await self.collection.find_all().to_list()

    def group_by_video_id(self, documents):
        grouped = defaultdict(list)
        for doc in documents:
            video_id = getattr(doc, "video_id", None)
            if video_id:
                grouped[video_id].append(doc)
        return grouped

    def determine_ids_to_keep_and_delete(self, grouped_docs):
        ids_to_keep = set()
        all_ids = set()

        for docs in grouped_docs.values():
            all_ids.update([doc.id for doc in docs])
            with_peaks = [doc for doc in docs if getattr(doc, "peaks", None)]

            if with_peaks:
                ids_to_keep.add(with_peaks[0].id)
            else:
                ids_to_keep.add(docs[0].id)

        ids_to_delete = list(all_ids - ids_to_keep)
        return ids_to_keep, ids_to_delete

    async def backup_documents(
        self, ids_to_delete: list, backup_path: Optional[str] = None
    ):
        if not backup_path:
            backup_path = f"heatmap_peaks_backup_{datetime.now().isoformat()}.json"

        docs_to_backup = await self.collection.find_many(
            {"_id": {"$in": ids_to_delete}}
        ).to_list()
        with open(backup_path, "w") as f:
            f.write(json_util.dumps(docs_to_backup, indent=2))

        print(f"📦 Backup created at {backup_path} ({len(docs_to_backup)} documents)")

    async def delete_duplicates(self, ids_to_delete):
        result = await self.collection.find_many(
            {"_id": {"$in": ids_to_delete}}
        ).delete()
        print(f"✅ Deleted {result} duplicate entries")

    async def run_deduplication(self):
        print("🔍 Starting deduplication process...")
        documents = await self.fetch_all_documents()
        grouped = self.group_by_video_id(documents)
        ids_to_keep, ids_to_delete = self.determine_ids_to_keep_and_delete(grouped)

        if not ids_to_delete:
            print("ℹ️ No duplicates found.")
            return

        await self.backup_documents(ids_to_delete)
        await self.delete_duplicates(ids_to_delete)
        print("✅ Deduplication complete.")


async def main():
    await init_services()
    service = HeatmapDeduplicationService()
    await service.run_deduplication()


if __name__ == "__main__":
    asyncio.run(main())
