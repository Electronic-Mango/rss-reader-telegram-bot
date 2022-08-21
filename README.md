# RSS reader Telegram bot

[![CodeQL](https://github.com/Electronic-Mango/rss-reader-telegram-bot/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/Electronic-Mango/rss-reader-telegram-bot/actions/workflows/codeql-analysis.yml)
[![flake8 and pytest](https://github.com/Electronic-Mango/rss-reader-telegram-bot/actions/workflows/flake8-pytest-verification.yml/badge.svg)](https://github.com/Electronic-Mango/rss-reader-telegram-bot/actions/workflows/flake8-pytest-verification.yml)
[![black](https://github.com/Electronic-Mango/rss-reader-telegram-bot/actions/workflows/black-formatting-verification.yml/badge.svg)](https://github.com/Electronic-Mango/rss-reader-telegram-bot/actions/workflows/black-formatting-verification.yml)

A simple Telegram bot sending updates for RSS feeds, build with [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot)!


## Table of contents
 - [Requirements](#requirements)
 - [Configuration](#configuration)
   - [Bot parameters](#bot-parameters)
   - [Restricting access to bot commands](#restricting-access-to-bot-commands)
   - [Supplying RSS feed links](#supplying-rss-feed-links)
   - [Storing chat data](#storing-chat-data)
   - [Quiet hours](#quiet-hours)
   - [Randomness when checking for updates](#randomness-when-checking-for-updates)
   - [Docker](#docker)
 - [Running the bot](#running-the-bot)
 - [Commands](#commands)
 - [Other details](#other-details)
   - [Deciding which feeds are valid](#deciding-which-feeds-are-valid)
   - [Checking for updates](#checking-for-updates)
   - [Randomness in delays and checking for updates](#randomness-in-delays-and-checking-for-updates)
   - [Sending updates and message formatting](#sending-updates-and-message-formatting)
   - [Detecting when user blocks the bot and clearing chat data](#detecting-when-user-blocks-the-bot-and-clearing-chat-data)


## Requirements

This bot was built with `Python 3.10` and [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot).
Full list of Python requirements is in the `requirements.txt` file, you can use it to install all of them.


## Configuration

### Bot parameters
Configuration for the bot is stored in the `settings.toml` file.
Detailed description of each parameter is described there.

Almost all fields are filled with sensible defaults, except the Telegram bot token.
By default the `settings.toml` in the project root will be used, however this can be overriden by `SETTINGS_TOML_PATH` environment variable.

Each field in the `settings.toml` can be also overriden using environment variables, where their names are `<TABLE NAME>_<FIELD NAME>`, e.g. `TELEGRAM_TOKEN`, `UPDATES_LOOKUP_INTERVAL`, or `LOGGING_LOG_PATH`.
Environment variables will be treated with higher priority, than values in `settings.toml`.

This way you can provide your own Telegram bot token without modifying project files.
This can be especially useful when running the bot in a Docker container.


### Restricting access to bot commands
Bot can be restricted to allow only specific users to execute bot commands via `TELEGRAM` - `ALLOWED_USERNAMES` value in `settings.toml` or `TELEGRAM_ALLOWED_USERNAMES` environment variable.
When left empty everyone will be able to access the bot.

You can specify multiple users delimiting them via value in `ALLOWED_USERNAMES_DELIMITER` in `settings.toml`.
By default a single `,` is used. Any whitespaces in resulting usernames are automatically stripped.


### Supplying RSS feed links

Bot doesn't allow users to directly specify a RSS link to follow, instead it stores all available links in a YAML configuration file and allows users to pick one of types defined there.

This might not be the best approach, however it was most suitable for my use case, as it simplified the process of subscribing to RSS feeds.

There's a template `feed_links.yml` file which contains examples of how to define RSS links for the bot.
You can either modify this file directly, or supply your own file by either modifying the `RSS` - `FEEDS_YAML_FILENAME` parameter in `settings.toml`, or by overriding it via `RSS_FEEDS_YAML_FILENAME` environment variable.

Only feed names (or types) will be displayed to users, link themselves are not.

Additionally, since RSS links are not stored together with subscription data, you can change the RSS links without the need of re-adding all your subscriptions.
Just make sure, that feed type stays the same.


### Storing chat data
Bot uses a separate MongoDB to store chat data.
DB host and port can be configured via `DB_HOST` and `DB_PORT` parameters in `settings.toml`, or environment variables `DATABASE_DB_HOST` and `DATABSE_DB_PORT`.
Parameters `DB_NAME` and `DB_COLLECTION_NAME` specify names of DB and collection where all the data will be stored.

All data is stored within a single collection, for simplicity, so the latter parameters don't matter much.

Each document contains information about a single subscription and stores:
 - **chat ID** - ID of a chat where subscription was made
 - **feed type** - as specified by YAML with feed links
 - **feed name** - specific source from the link, like followed Reddit user
 - **latest read feed entry ID** - used to determine which feed entries were already send to the user

RSS links are not stored, when the bot is checking for updates it uses the link from YAML file and stored feed type.
This means, that you can change feed links without the need of re-adding all your subscriptions.
Just make sure, that feed type stays the same.


### Quiet hours
You can configure hours where bot won't check for RSS updates via `QUIET_HOURS` parameter in `settings.toml` or `UPDATES_QUIET_HOURS` environment variable. Add whatever hours you don't want updates in 24h format separated by spaces. For example these values will stop the bot from checking for updates from midnight to 7AM:
```toml
QUIET_HOURS = "0 1 2 3 4 5 6"
```
You can pad the hours with `0`, however it's not necessary.


### Randomness when checking for updates
You can configure additional delay when checking for updates on two levels - main job checking for all updates and between individual feeds.

Delay in the main loop checking for all updates can be added via `LOOKUP_INTERVAL_RANDOMNESS` parameter in `settings.toml` or `UPDATES_LOOKUP_INTERVAL_RANDOMNESS` environment variable.
Main job still triggers every `LOOKUP_INTERVAL`, however it will only trigger a new delayed job which will check for all updates.
This job is scheduled after `0` to `LOOKUP_INTERVAL_RANDOMNESS` seconds.

Additional random delay when checking for individual feeds can be configured via `LOOKUP_FEED_DELAY_RANDOMNESS` in `settings.toml` or `UPDATES_LOOKUP_FEED_DELAY_RANDOMNESS` environment variable.
It is an additional delay to `LOOKUP_FEED_DELAY` between `0` and configured value.

Setting parameters to `0` will disable their respective randomness.


### Docker

There's a Dockerfile in the repo, which will build a Docker image with for the bot using `python:3.10-slim` as base.
You can set all configuration parameters using environment variables for Docker container, rather than modifying project files before building.

Keep in mind, that running the bot in a Docker container might require changing DB IP address (as the default one is `localhost`) and possibly RSS feed links if you're using a self-hosted RSS feed, like [`RSS-Bridge`](https://github.com/RSS-Bridge/rss-bridge) or [`RSSHub`](https://github.com/DIYgod/RSSHub).

All of this can be done without modifying project files by using environment variables.

You can also supply RSS feed links without modifying the project by overriding `RSS_FEEDS_YAML_FILENAME` environment variable to point to a file in a mounted volume.

You can also check out my repository
[RSS reader Telegram bot Docker deployment](https://github.com/Electronic-Mango/rss-reader-telegram-bot-docker-deployment)
for an example of how you can deploy this bot via Docker Compose.


## Running the bot

Running the bot is quite simple:

1. Create a Telegram bot via [BotFather](https://core.telegram.org/bots#6-botfather)
1. Set up `MongoDB`, I use a [MongoDB Docker container](https://hub.docker.com/_/mongo)
1. Configure DB-related parameters in the bot, default ones assume the DB is running locally
1. Configure Telegram bot token parameters
1. Supply RSS feed links
1. Run the `main.py` file, or use a Docker container


## Commands

 * `/help` - print help information with all commands
 * `/start` - the same as `/help`
 * `/hello` - say hello to the bot
 * `/list` - list all subscriptions
 * `/add` - adds subscription for a given feed
 * `/remove` - remove subscription for a given feed
 * `/removeall` - remove all subscriptions
 * `/cancel` - cancel the current operation, currently used only when adding new subscriptions


## Other details

### Deciding which feeds are valid

Bot will assume that a given feed link (for a specific source, not a general one) is valid if it passes two conditions:

1. HTTP response code is either 200 or 301
1. feed has any entries already

The second one means, that you can't subscribe to feeds which do exist, but don't have any entries yet.
It does, however, allow for a much better validation of links, since some RSS feeds will always respond with code 200, even if the feed is not valid.
It's not a perfect solution, but it works for my use case.


### Checking for updates

Bot check for updates for all subscriptions in a regular intervals, configured by the `settings.toml` parameter `UPDATES` - `LOOKUP_INTERVAL`, or the `UPDATES_LOOKUP_INTERVAL` environment variable.

By default it will check for updates every hour.

A different parameter `LOOKUP_FEED_DELAY` configures the delay between checking each feed.
This should prevent the bot from stopping responding to commands when it's checking for updates, since it might take a while.

You should check how long checking for each update takes in your case and modify the `LOOKUP_FEED_DELAY` accordingly, so the bot has the time to respond to commands in the mean time.
At the same time it shouldn't be so big, that last checks are done when next iteration of checking for updates starts.


### Randomness in delays and checking for updates

Randomness can be added to checking for updates on two levels:
1. Main job triggering check for each feed via `LOOKUP_INTERVAL_RANDOMNESS`
1. Between individual feeds via `LOOKUP_FEED_DELAY_RANDOMNESS`

Main job still triggers every exactly `LOOKUP_INTERVAL` seconds.
However only responsibility of this job is triggering delayed checks.
These delayed checks will happen after between `0` and `LOOKUP_INTERVAL_RANDOMNESS` seconds.

Delay between checking each feed is `LOOKUP_FEED_DELAY` plus a random value between `0` and `LOOKUP_FEED_DELAY_RANDOMNESS`.
So minimum amount of seconds between checking for each feed is `LOOKUP_FEED_DELAY` and maximum is `LOOKUP_FEED_DELAY + LOOKUP_FEED_DELAY_RANDOMNESS`.

However, the main job isn't taking into account any of the additional delays and randomness, it still triggers every `LOOKUP_INTERVAL`, triggering delayed job every `0` to `LOOKUP_INTERVAL_RANDOMNESS` seconds, etc.

So minimum amout of secods between triggering checking for updates is `LOOKUP_INTERVAL - LOOKUP_INTERVAL_RANDOMNESS` and maximum is `LOOKUP_INTERVAL + LOOKUP_INTERVAL_RANDOMNESS`.
This, however, doesn't take into account neither `LOOKUP_FEED_DELAY` nor `LOOKUP_FEED_DELAY_RANDOMNESS`.


### Sending updates and message formatting

Each RSS feed entry will be sent in a separate message.
If an entry contains more than 10 images/videos the update will be split into more messages, since Telegram only allows up to 10 images/videos per message. Only the final message will contain the caption.

Each message will contain the RSS feed source and type, text of an RSS entry summary and link.
It won't contain the title, since in my use case it was just duplicating the summary anyways.

To add a title to the messages two files need to be changed:
- `parser.py` - title will need to be extracted from the RSS entry
- `sender.py` - title from the last entry needs to be added to the message

Both files are quite simple, so it shouldn't be a problem.


### Detecting when user blocks the bot and clearing chat data

Bot doesn't have any active way of checking that a user deleted their conversation with the bot and stopped it.
After this happens the bot will still check for updates.
When an update is meant to be sent, it will cause a `Forbidden` exception.
Bot will recognize this exception as a situation where this user stopped the conversation and will delete all their data from DB.
