#!/bin/env -S poetry run python

import interactions
import re
import os

from typing import Union
from json import loads
from requests import get
from io import StringIO
from urllib.parse import quote

if os.path.exists("config.json"):
    with open("config.json") as file:
        config = loads(file.read())
else:
    config = {"bot_token": os.environ["BOT_TOKEN"]}

url_regex = re.compile(
    r"(?P<scheme>https?):\/\/(?P<domain>[\w_-]+(?:(?:\.[\w_-]+)+))(?P<directory>[\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])",
    flags=re.M,
)


def get_song_data(url: str) -> Union[interactions.Embed, interactions.File]:
    # get the data from the songwhip api
    response = get(
        url=f"https://api.song.link/v1-alpha.1/links?url={quote(url)}&userCountry=US"
    )
    data: dict = response.json()

    # check and make sure we have a valid response
    code = response.status_code
    if code not in range(200, 300):
        return interactions.File(file=StringIO(data), file_name=f"{code}.log")

    # parse the data we care about
    title = None
    artist = None
    thumbnail = None

    relevant_platforms = [
        "spotify",
        "youtubeMusic",
        "appleMusic",
        "amazonMusic",
        "bandcamp",
    ]
    relevant_data = []
    for platform in relevant_platforms:
        by_platform = data["linksByPlatform"].get(platform, None)
        if by_platform == None:
            continue
        url = by_platform["url"]
        id = by_platform["entityUniqueId"]
        entity = data["entitiesByUniqueId"][id]
        if title == None:
            title = entity.get("title", None)
        if artist == None:
            artist = entity.get("artistName", None)
        if thumbnail == None:
            thumbnail = entity.get("thumbnailUrl", None)

        relevant_data.append(
            {
                "platform": platform,
                "url": url,
            }
        )

    # discord caps embed titles at 256 characters
    artist_text = f" by {artist}"
    remaining_length = 256 - len(artist_text)
    if len(title) > remaining_length:
        title_section = title[: remaining_length - 2] + "…" + artist_text
    else:
        title_section = title + artist_text

    return interactions.Embed(
        title=title_section[:255],
        description="listen on:\n"
        + "\n".join([f"- [{x['platform']}]({x['url']})" for x in relevant_data]),
        color=0x00FFFF,
        url=data["pageUrl"],
        thumbnail=thumbnail,
    )


def attribution() -> interactions.EmbedAuthor:
    # required to use odesli per their terms
    return interactions.EmbedAuthor(
        name="Powered by Odesli.",
        url="https://odesli.co/",
    )


bot = interactions.Client()


@interactions.listen()
async def on_startup() -> None:
    print("Bot is ready!")


@interactions.slash_command(
    name="music",
    description="Generate a Songwhip link from a link.",
    options=[
        interactions.SlashCommandOption(
            name="url",
            description="A link to the song.",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
@interactions.integration_types(guild=True, user=True)
@interactions.contexts(guild=True, bot_dm=False, private_channel=True)
async def music(ctx, url: str) -> None:
    await ctx.defer()

    embed = get_song_data(url)
    embed.author = attribution()

    await ctx.respond(embed=embed)


@interactions.message_context_menu(name="Get Songs")
@interactions.integration_types(guild=True, user=True)
@interactions.contexts(guild=True, bot_dm=False, private_channel=True)
async def get_song_data_from_message(ctx: interactions.ContextMenuContext) -> None:
    await ctx.defer(ephemeral=False)

    embeds = []

    for match in url_regex.finditer(ctx.target.content):
        url = match.expand(r"\g<scheme>://\g<domain>\g<directory>")

        # get the song data
        embed = get_song_data(url)
        embed.author = attribution()

        embeds.append(embed)

    await ctx.respond(content="Found these song(s):", embeds=embeds, ephemeral=False)


if __name__ == "__main__":
    # run the bot
    bot.start(token=config["bot_token"])
