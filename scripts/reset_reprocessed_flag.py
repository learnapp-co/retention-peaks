import asyncio
from src.models.heatmap import heatmap_peaks
from src.services.init_services import init_services


class ReprocessedFlagResetter:
    def __init__(self):
        pass

    async def reset_reprocessed_flag(self):
        await init_services()
        # Find all entries where 'reprocessed' key exists
        entries = await heatmap_peaks.find({"reprocessed": {"$exists": True}}).to_list()
        print(f"Found {len(entries)} entries with 'reprocessed' key.")
        updated = 0
        for entry in entries:
            if entry.reprocessed != False:
                entry.reprocessed = False
                await entry.save()
                updated += 1
                print(f"Updated {updated} entry (set reprocessed=False).")
        print(f"Updated {updated} entries (set reprocessed=False).")

    async def run(self):
        try:
            await self.reset_reprocessed_flag()
        except Exception as e:
            print(f"Main process failed: {str(e)}")
            raise


if __name__ == "__main__":
    resetter = ReprocessedFlagResetter()
    asyncio.run(resetter.run())
