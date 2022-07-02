from logging import DEBUG, ERROR, INFO, WARN, basicConfig, debug, error, info, warn
from os import getenv

from discord.ext import tasks
from discord.ext.commands import Bot, when_mentioned_or
from dotenv import load_dotenv

from basic_json_feed_reader import get_json_feed_items, get_not_handled_feed_items
from feed_item_sender_basic import send_message
from feed_item_sender_instagram import send_message_instagram
from rss_db import add_rss_to_db, get_all_rss_from_db, remove_rss_feed_id_db, update_rss_feed_in_db

load_dotenv()
bot = Bot(command_prefix=when_mentioned_or("!"))


def configure_logging():
    basicConfig(format="%(asctime)s %(message)s", datefmt="%d-%m-%Y %H:%M:%S", level=INFO)


@bot.event
async def on_ready():
    info(f"Logged in as [{bot.user}]...")
    info(f"Connected servers: {bot.guilds}...")
    info(f"Connected channels: {list(bot.get_all_channels())}")
    info("Bot started!")
    start_rss_checking_when_necessary()


@bot.command()
async def hello(context):
    info(f"Hello from channel=[{context.channel.id}]")
    await context.send("Hello there!")


@bot.command(aliases=["add"])
async def add_feed(context, rss_feed=None, rss_name=None):
    if not rss_feed or not rss_name:
        await context.send_help(add_feed)
        return
    channel_id = context.channel.id
    feed_items = get_json_feed_items(rss_feed)
    latest_item_id = feed_items[0]["id"]
    info(f"Adding RSS feed, channel_id=[{channel_id}] name=[{rss_name}] feed=[{rss_feed}] latest=[{latest_item_id}]...")
    add_rss_to_db(channel_id, rss_feed, rss_name, latest_item_id)
    start_rss_checking_when_necessary()
    await context.send(f'Added subscription for "{rss_name}"!')


@bot.command(aliases=["remove", "stop", "stop_feed"])
async def remove_feed(context, rss_name=None):
    if not rss_name:
        await context.send_help(remove_feed)
        return
    channel_id = context.channel.id
    info(f"Removing RSS feed, channel_id=[{channel_id}] name=[{rss_name}]...")
    removed_count = remove_rss_feed_id_db(channel_id, rss_name)
    if removed_count:
        info(f"RSS channel_id=[{channel_id}] name=[{rss_name}] was removed.")
        await context.send(f'Removed subscription for "{rss_name}"!')
    else:
        info(f"Removed no entries for channel_id=[{channel_id}] name=[{rss_name}], most likely this RSS name doesn't exist.")
        await context.send(f'No subscription with name "{rss_name}" to remove!')


def start_rss_checking_when_necessary():
    if check_rss.is_running():
        return
    data_to_look_up = {collection: data for collection, data in get_all_rss_from_db().items() if data}
    if data_to_look_up:
        check_rss.start()


@tasks.loop(seconds=int(getenv("LOOKUP_INTERVAL_SECONDS")))
async def check_rss():
    if not bot.is_ready():
        return
    info(f"Checking all RSS...")
    not_handled_rss = prepare_all_not_handled_data(get_all_rss_from_db())
    if not not_handled_rss:
        info("No updates.")
        return
    info("Found new RSS items.")
    info(not_handled_rss)
    for channel_id, rss_channel_data in not_handled_rss.items():
        for rss_name, rss_feed, items in rss_channel_data:
            for item in items:
                await send_rss_update(channel_id, rss_name, item)
            latest_item = items[-1]
            update_rss_feed_in_db(channel_id, rss_feed, rss_name, latest_item["id"])


def prepare_all_not_handled_data(stored_rss_data):
    not_handled_rss_data = {
        int(channel_id): get_not_handled_rss_data_for_channel(rss_data)
        for channel_id, rss_data in stored_rss_data.items()
    }
    return {
        channel_id: not_handled_rss_data
        for channel_id, not_handled_rss_data in not_handled_rss_data.items()
        if not_handled_rss_data
    }


def get_not_handled_rss_data_for_channel(all_rss_data):
    not_handled_items = list()
    for rss_data in all_rss_data:
        rss_name = rss_data["rss_name"]
        rss_feed = rss_data["rss_feed"]
        latest_handled_item_id = rss_data["latest_item_id"]
        not_handled_feed_items = get_not_handled_feed_items(rss_feed, latest_handled_item_id)
        if not_handled_feed_items:
            not_handled_items.append((rss_name, rss_feed, not_handled_feed_items))
    return not_handled_items


async def send_rss_update(channel_id, rss_name, item):
    channel = bot.get_channel(channel_id)
    if channel is None:
        info(f"Fetching channel ID=[{channel_id}]...")
        channel = await bot.fetch_channel(channel_id)
    if channel is None:
        error(f"Channel ID=[{channel_id}] is None, cannot send message!")
        return
    info(f"Sending message to ID=[{channel_id}]")
    item_id = item["id"]
    if "www.instagram.com" in item_id:
        await send_message_instagram(channel, rss_name, item)
    else:
        await send_message(channel, rss_name, item)


configure_logging()
info(f"Bot starting...")
bot.run(getenv("TOKEN"))
