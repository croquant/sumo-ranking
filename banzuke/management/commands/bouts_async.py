import asyncio
import datetime
import time

import aiohttp
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from banzuke.models import Basho, Torikumi
from rikishi.models import Rank, Rikishi
from rikishi.utils import convert_long_to_short_rank

BATCH_SIZE = 200

all_rikishi = Rikishi.objects.all().only("id", "api_id", "name")
rikishi_lookup = {rikishi.api_id: rikishi.id for rikishi in all_rikishi}
basho_lookup = {basho.slug: basho for basho in Basho.objects.all()}
rank_lookup = {rank.slug: rank for rank in Rank.objects.all()}


async def fetch_bouts_for_rikishi(session, api_id):
    async with session.get(
        f"https://sumo-api.com/api/rikishi/{api_id}/matches"
    ) as response:
        response_obj = await response.json()
        if (
            response_obj
            and "records" in response_obj
            and response_obj["total"] > 0
        ):
            return response_obj["records"]
        else:
            return None


async def get_basho_by_id(session, basho_id):
    async with session.get(
        f"https://sumo-api.com/api/basho/{basho_id}"
    ) as response:
        response_obj = await response.json()
        if "date" in response_obj and response_obj["date"] != "":
            return response_obj
        else:
            return None


async def process_rikishi_batch(rikishi_batch, i, n_batches):
    t_batch_0 = time.perf_counter()
    print(f"==== Processing batch {i+1}/{n_batches}")

    async with aiohttp.ClientSession(raise_for_status=True) as session:
        rikishi_tasks = [
            asyncio.create_task(process_rikishi(session, rikishi))
            for rikishi in rikishi_batch
        ]
        await asyncio.gather(*rikishi_tasks)

    t_batch_1 = time.perf_counter()
    t_batch = t_batch_1 - t_batch_0
    print(f"==== Batch {i+1}/{n_batches} Time: {t_batch}s")
    return t_batch


async def process_rikishi(session, rikishi):
    bouts = await fetch_bouts_for_rikishi(session, rikishi.api_id)
    len_bouts = len(bouts) if bouts is not None else 0

    if bouts is None:
        print(f"No bouts found for {rikishi.name}")
        return

    bout_tasks = [
        asyncio.create_task(process_bout(session, bout)) for bout in bouts
    ]
    await asyncio.gather(*bout_tasks)
    print(f"Saved {len_bouts} bouts for {rikishi.name}")


async def process_bout(session, bout):
    if bout["bashoId"] is None or bout["bashoId"] == "":
        return

    basho = await get_or_create_basho(session, bout["bashoId"])
    if basho is None:
        return

    try:
        division = slugify(bout["division"])
        east_id = rikishi_lookup.get(bout["eastId"])
        east_rank = await get_or_create_rank(bout["eastRank"])
        west_id = rikishi_lookup.get(bout["westId"])
        west_rank = await get_or_create_rank(bout["westRank"])
        winner_id = rikishi_lookup.get(bout["winnerId"])

        if (
            division is None
            or east_id is None
            or west_id is None
            or winner_id is None
        ):
            raise Exception
    except Exception as e:
        print("! === Failed to process bout", bout)
        print(e)
        print("! ================================")
        return

    await Torikumi.objects.aupdate_or_create(
        basho=basho,
        division_id=division,
        day=bout["day"],
        east_id=east_id,
        west_id=west_id,
        defaults={
            "winner_id": winner_id,
            "east_rank": east_rank,
            "west_rank": west_rank,
        },
    )


async def get_or_create_basho(session, basho_id):
    try:
        basho = basho_lookup.get(basho_id)
        if basho is not None:
            return basho
        else:
            raise Exception

    except Exception:
        basho_response = await get_basho_by_id(session, basho_id)
        if basho_response is None:
            return None

        start_date = datetime.datetime.strptime(
            basho_response["startDate"], "%Y-%m-%dT%H:%M:%SZ"
        )
        end_date = datetime.datetime.strptime(
            basho_response["endDate"], "%Y-%m-%dT%H:%M:%SZ"
        )
        basho = await Basho.objects.acreate(
            slug=basho_response["date"],
            year=int(basho_response["date"][0:4]),
            month=int(basho_response["date"][-2:]),
            start_date=start_date,
            end_date=end_date,
        )
        basho_lookup[basho_id] = basho
        return basho


async def get_or_create_rank(rank_name):
    try:
        if rank_name == "":
            return None
        rank_id = convert_long_to_short_rank(rank_name)
        rank = rank_lookup.get(rank_id)
        if rank is not None:
            return rank
        else:
            raise Exception
    except Exception:
        rank_parts = rank_name.split(" ")
        title = rank_parts[0]
        order = rank_parts[1] if len(rank_parts) > 1 else None
        direction = rank_parts[2] if len(rank_parts) > 2 else None

        print(f"Creating rank: {rank_name}")
        rank, _ = await Rank.objects.aget_or_create(
            slug=rank_id,
            defaults={
                "title": title,
                "order": order,
                "direction": direction,
            },
        )

        rank_lookup[rank_id] = rank
        return rank


class Command(BaseCommand):
    args = "<start end>"
    help = "Fetch and update Torikumi results for all Rikishi from the Sumo API and store them in the database"  # noqa

    def handle(
        self,
        *args,
        **options,
    ):
        loop = asyncio.get_event_loop()
        t0 = time.perf_counter()

        rikishi_batches = [
            list(all_rikishi[i : i + BATCH_SIZE])
            for i in range(0, len(all_rikishi), BATCH_SIZE)
        ]
        n_batches = len(rikishi_batches)

        t_batch_total = 0
        for i, rikishi_batch in enumerate(rikishi_batches):
            t_batch = loop.run_until_complete(
                process_rikishi_batch(rikishi_batch, i, n_batches)
            )
            t_batch_total += t_batch
            avg_t_batch = t_batch_total / (i + 1)
            remaining_time_estimate = avg_t_batch * (n_batches - i - 1)
            estimated_completion_time = (
                (
                    datetime.datetime.now()
                    + datetime.timedelta(seconds=remaining_time_estimate)
                )
                .time()
                .strftime("%H:%M:%S")
            )
            print(
                (
                    f"==== Average Batch Time: {avg_t_batch}s, "
                    f"Estimated Completion Time: {estimated_completion_time}"
                )
            )

        t1 = time.perf_counter()
        print(f"Total Time: {t1 - t0}s")
        print(f'Ended at {datetime.datetime.now().strftime("%H:%M:%S")}')
