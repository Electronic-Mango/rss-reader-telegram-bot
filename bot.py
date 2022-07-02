from basic_json_feed_reader import get_json_feed_items, get_unhandled_feed_items
from discord.ext import tasks
from discord.ext.commands import Bot, when_mentioned_or
from dotenv import load_dotenv
from logging import basicConfig, info, INFO
from os import getenv
from rss_db import add_rss_to_db, get_all_rss_from_db

load_dotenv()
bot = Bot(command_prefix=when_mentioned_or("!"))


def configure_logging():
    basicConfig(format="%(asctime)s %(message)s", datefmt="%d-%m-%Y %H:%M:%S", level=INFO)


@bot.event
async def on_ready():
    info(f"Logged in as [{bot.user}]...")
    info(f"Connected servers: {bot.guilds}...")
    info("Bot started!")


@bot.command()
async def hello(context):
    await context.send("Hello there!")


@bot.command(aliases=["add"])
async def add_feed(context, rss_feed=None, rss_name=None):
    if not rss_feed or not rss_name:
        await context.send_help(add_feed)
        return
    channel_id = context.channel.id
    feed_items = get_json_feed_items(rss_feed)
    latest_item_id = feed_items[0]["id"]
    info(f"Adding RSS feed, channel_id=[{channel_id}] name=[{rss_name}] feed=[{rss_feed}] latest=[{latest_item_id}].")
    add_rss_to_db(channel_id, rss_feed, rss_name, latest_item_id)


@tasks.loop(seconds=int(getenv("LOOKUP_INTERVAL_SECONDS")))
async def check_rss():
    info(f"Checking all RSS...")
    all_rss = get_all_rss_from_db()
    unhandled_rss = {
        channel_id: get_unhandled_rss_data_for_channel(rss_data)
        for channel_id, rss_data in all_rss.items()
    }
    if not unhandled_rss:
        info("No updates.")
        return
    info("Found not handled feed items:")
    info(unhandled_rss)


def get_unhandled_rss_data_for_channel(all_rss_data):
    unhandled_items = dict()
    for rss_data in all_rss_data:
        rss_name = rss_data["rss_name"]
        rss_feed = rss_data["rss_feed"]
        latest_handled_item_id = rss_data["latest_item_id"]
        unhandled_items[rss_name] = get_unhandled_feed_items(rss_feed, latest_handled_item_id)
    return unhandled_items


configure_logging()
info(f"Bot starting...")
check_rss.start()
bot.run(getenv("TOKEN"))
