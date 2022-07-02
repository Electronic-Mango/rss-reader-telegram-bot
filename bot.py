from basic_json_feed_reader import get_json_feed_items, get_unhandled_feed_items
from discord.ext import tasks
from discord.ext.commands import Bot, when_mentioned_or
from dotenv import load_dotenv
from os import getenv
from rss_db import add_rss_to_db, get_all_rss_from_db

load_dotenv()
bot = Bot(command_prefix=when_mentioned_or("!"))


@bot.event
async def on_ready():
    print(f"Logged in as [{bot.user}]...")
    print(f"Connected servers: {bot.guilds}...")
    print("Bot started!")


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
    print(f"Adding RSS feed, channel_id=[{channel_id}] name=[{rss_name}] feed=[{rss_feed}] latest=[{latest_item_id}].")
    add_rss_to_db(channel_id, rss_feed, rss_name, latest_item_id)


@tasks.loop(seconds=int(getenv("LOOKUP_INTERVAL_SECONDS")))
async def check_rss():
    print(f"Checking all RSS...")
    all_rss = get_all_rss_from_db()
    unhandled_rss = {
        channel_id: get_unhandled_rss_data_for_channel(rss_data)
        for channel_id, rss_data in all_rss.items()
    }
    if not unhandled_rss:
        print("No updates.")
        return
    print("Found not handled feed items:")
    print(unhandled_rss)


def get_unhandled_rss_data_for_channel(all_rss_data):
    unhandled_items = dict()
    for rss_data in all_rss_data:
        rss_name = rss_data["rss_name"]
        rss_feed = rss_data["rss_feed"]
        latest_handled_item_id = rss_data["latest_item_id"]
        unhandled_items[rss_name] = get_unhandled_feed_items(rss_feed, latest_handled_item_id)
    return unhandled_items


print(f"Bot starting...")
check_rss.start()
bot.run(getenv("TOKEN"))
