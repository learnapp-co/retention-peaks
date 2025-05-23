import asyncio
from src.models.heatmap import heatmap_peaks
from src.services.init_services import init_services


async def reset_reprocessed_flag():
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
    print(f"Updated {updated} entries (set reprocessed=False).")


if __name__ == "__main__":
    asyncio.run(reset_reprocessed_flag())
