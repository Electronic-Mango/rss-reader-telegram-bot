from basic_json_feed_reader import get_json_feed_items
from discord.ext.commands import Bot, when_mentioned_or
from dotenv import load_dotenv
from os import getenv
from rss_db import add_rss_to_db

bot = Bot(command_prefix=when_mentioned_or("!"))


@bot.event
async def on_ready():
    print(f"Logged in as [{bot.user}]")
    print(f"Connected servers: {bot.guilds}")


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
    print(f"Adding RSS feed, channel_id=[{channel_id}] name=[{rss_name}] feed=[{rss_feed}] latest=[{latest_item_id}]")
    add_rss_to_db(channel_id, rss_feed, rss_name, latest_item_id)


load_dotenv()
bot.run(getenv("TOKEN"))
