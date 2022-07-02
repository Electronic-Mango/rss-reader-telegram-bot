from os import getenv
from dotenv import load_dotenv
from discord.ext.commands import Bot, when_mentioned_or


bot = Bot(command_prefix=when_mentioned_or("!"))


@bot.event
async def on_ready():
    print(f"Logged in as [{bot.user}]")
    print(f"Connected servers: {bot.guilds}")


@bot.command()
async def hello(context):
    await context.send("Hello there!")


load_dotenv()
bot.run(getenv("TOKEN"))
