from feedparser import FeedParserDict

# These could be the same type, as entire RSS feed and individual are "FeedParserDict".
# However, splitting them up makes it simpler to track which type is being used where,
# based on type hints.
type RssFeed = FeedParserDict
type RssEntry = FeedParserDict
