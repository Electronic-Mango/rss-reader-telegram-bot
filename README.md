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
   - [Persistence](#persistence)
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
Configuration parameters for the bot are stored in a configuration YAML file.
Default parameters are stored in `settings.yml` file in the project root.
Detailed description of each parameter is described there.

Almost all fields are filled with sensible defaults, except the Telegram bot token.
Values from the default file can be overwritten by a custom YAML file, which path can be supplied by `CUSTOM_SETTINGS_PATH` environment variable.
Only specific parameters can be configured in the custom file.
All parameters missing from custom YAML will be taken from default YAML instead.

This way you can provide your own Telegram bot token without modifying project files.
This can be especially useful when running the bot in a Docker container.

Most basic custom YAML can contains only Telegram bot token:

```yaml
telegram:
  token: your-telegram-bot-token
```


### Restricting access to bot commands
Bot can be restricted to allow only specific users to execute bot commands via `telegram` - `allowed_usernames` value in configuration YAML.
When the list is left empty everyone will be able to access the bot.

You can specify multiple users, as the value in YAML is a list.


### Persistence

Bot uses pickled file for storing persistence data between restarts.
By default `persistence` file in the project root is used.
Its path can be tweaked via configuration YAML.

All conversation-style commands are persistent.
This means, that their state should be preserved after bot has been restarted, you can just continue the conversation afterwards.

When deploying the bot via Docker I'd recommend changing the path to persistence pickled file into a mounted volume.
Otherwise it will be stored directly in the container and it will be removed with it.


### Supplying RSS feed links

Bot doesn't allow users to directly specify a RSS link to follow, instead it stores all available links in a YAML configuration file and allows users to pick one of types defined there.

This might not be the best approach, however it was most suitable for my use case, as it simplified the process of subscribing to RSS feeds.

There's a template `feed_links.yml` file which contains examples of how to define RSS links for the bot.
You can either modify this file directly, or supply your own file by either modifying the `rss` - `feeds_yaml_filename` parameter in configuration YAML.

Only feed names (or types) will be displayed to users, links themselves are not.

Additionally, since RSS links are not stored together with subscription data, you can change the RSS links without the need of re-adding all your subscriptions.
Just make sure, that feed type stays the same.

Here's a basic set of configuration parameters for a RSS feed in YAML:

```yaml
# RSS type name displayed to the user
Feed name 1:
  # RSS feed link. Notice {source_pattern} substring, it will be replaced with whatever source you input when adding a subscription.
  url: http://feedlink1.com/{source_pattern}/rss
  # Configure whether updates will contain RSS entry title.
  # Case sensitive, optional, defaults to "false".
  show_title: true
  # Configure whether updates will contain RSS entry description.
  # Case sensitive, optional, ddefaults to "false".
  show_description: true
  # List of strings which will be trimmed out of both title and description.
  # Filters are case sensitive. Whole field is optional and defaults to an empty string.
  filters:
    - some string
    - some other string
```

Out of all parameters only `url` is required, others are optional.


### Storing chat data
Bot uses a separate MongoDB to store chat data.
DB configuration is stored in `database` section of configuration YAML.
DB host and port can be configured via `host` and `port` parameters.
Parameters `name` and `collection_name` specify names of DB and collection where all the data will be stored.

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
You can configure hours where bot won't check for RSS updates via `quiet_hours` parameter in configuration YAML in `telegram` - `updates` section.
Add whatever hours you don't want updates in 24h format.
For example these values will stop the bot from checking for updates from 11PM to 8AM:

```yml
telegram:
  updates:
    quiet_hours: [23, 0, 1, 2, 3, 4, 5, 6, 7]
```

Just don't pad the values with `0`, as they will be then treated as strings, rather than ints.


### Randomness when checking for updates
You can configure additional delay when checking for updates on two levels - main job checking for all updates and between individual feeds.

Parameters related to updates, delays and randomness are in `telegram` - `updates` section of configuration YAML.

Delay in the main loop checking for all updates can be added via `lookup_interval_randomness` parameter.
Main job still triggers every `lookup_interval`, however it will only trigger a new delayed job which will check for all updates.
This job is scheduled after `0` to `lookup_interval_randomness` seconds.

Additional random delay when checking for individual feeds can be configured via `lookup_feed_delay_randomness` parameter.
It is an additional delay to `lookup_feed_delay` between `0` and configured value.

Setting parameters to `0` will disable their respective randomness.


### Docker

There's a Dockerfile in the repo, which will build a Docker image with for the bot using `python:3.10-slim` as base.
You can set all configuration parameters using environment variables for Docker container, rather than modifying project files before building.

Keep in mind, that running the bot in a Docker container might require changing DB IP address (as the default one is `localhost`) and possibly RSS feed links if you're using a self-hosted RSS feed, like [`RSS-Bridge`](https://github.com/RSS-Bridge/rss-bridge) or [`RSSHub`](https://github.com/DIYgod/RSSHub).

When supplying configuration parameters, you can add a custom configuration YAML to a mounted volume and point to it via `CUSTOM_SETTINGS_PATH` environment variable in the container.
This way configuration YAML with your bot token isn't inserted directly in the container.
Also, you can provide custom configuration without modifying project files.

You can in a similar way supply feed links.

When deploying the bot via Docker I'd also recommend changing the path to persistence pickled file into a mounted volume.
Otherwise it will be stored directly in the container and it will be removed with it.
You can do that either by modifying `telegram` - `persistence_file` value in configuration YAML.

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
 * `/add` - adds subscription for a given feed
 * `/subscriptions` - list and manage your subscriptions
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

Bot check for updates for all subscriptions in a regular intervals, configured by the configuration YAML parameter `telegram` - `updates` - `lookup_interval`.

By default it will check for updates every hour.

A different parameter `lookup_feed_delay` configures the delay between checking each feed.
This should prevent the bot from stopping responding to commands when it's checking for updates, since it might take a while.

You should check how long checking for each update takes in your case and modify the `lookup_feed_delay` accordingly, so the bot has the time to respond to commands in the mean time.
At the same time it shouldn't be so big, that last checks are done when next iteration of checking for updates starts.


### Randomness in delays and checking for updates

Randomness can be added to checking for updates on two levels:
1. Main job triggering check for each feed via `lookup_interval_randomness`
1. Between individual feeds via `lookup_feed_delay_randomness`

Main job still triggers every exactly `lookup_interval` seconds.
However only responsibility of this job is triggering delayed checks.
These delayed checks will happen after between `0` and `lookup_interval_randomness` seconds.

Delay between checking each feed is `lookup_feed_delay` plus a random value between `0` and `lookup_feed_delay_randomness`.
So minimum amount of seconds between checking for each feed is `lookup_feed_delay` and maximum is `lookup_feed_delay + lookup_feed_delay_randomness`.

However, the main job isn't taking into account any of the additional delays and randomness, it still triggers every `lookup_interval`, triggering delayed job every `0` to `lookup_interval_randomness` seconds, etc.

So minimum amout of secods between triggering checking for updates is `lookup_interval - lookup_interval_randomness` and maximum is `lookup_interval + lookup_interval_randomness`.
This, however, doesn't take into account neither `lookup_feed_delay` nor `lookup_feed_delay_randomness`.


### Sending updates and message formatting

Each RSS feed entry will be sent in a separate message.
If an entry contains more than 10 images/videos the update will be split into more messages, since Telegram only allows up to 10 images/videos per message. Only the final message will contain the caption.

Each message will contain the RSS feed source and type, RSS entry title, summary and link.

Bot assumes that RSS entry summary (or description) will be in HTML format.
Bot will send only raw text from summary, without any tags.


### Detecting when user blocks the bot and clearing chat data

Bot doesn't have any active way of checking that a user deleted their conversation with the bot and stopped it.
After this happens the bot will still check for updates.
When an update is meant to be sent, it will cause a `Forbidden` exception.
Bot will recognize this exception as a situation where this user stopped the conversation and will delete all their data from DB.
