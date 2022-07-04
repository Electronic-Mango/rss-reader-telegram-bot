from re import findall, match, sub


def parse_summary(entry):
    summary = entry.summary
    summary = sub(r"(<a.+</a>)+", "", summary)
    summary = sub(r"(<video controls>.+</video>)+", "", summary)
    summary = summary.replace("&quot;", '"')
    summary = sub(r"<br( )?(/)?>", "\n", summary)
    summary = sub(r"<p>", "", summary)
    summary = sub(r"</p>", "\n", summary)
    summary = sub(r"<img.+/>", "", summary)
    summary = summary.replace("(no text)", "")
    summary = "\n".join([line.strip() for line in summary.strip().splitlines() if line.strip()])
    return summary


def parse_media(entry):
    if entry.media:
        return entry.media
    summary = entry.summary
    img_pattern = r"<img.*? src=\"(.*?)\""
    match(img_pattern, summary)
    img_urls = findall(img_pattern, summary)
    return [(url, None) for url in img_urls]
