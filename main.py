#!/bin/env -S poetry run python

import json
import requests
import os
import interactions
import re
import typing
from urllib.parse import quote

if os.path.exists("config.json"):
    with open("config.json") as file:
        config = json.loads(file.read())
else:
    config = {
        "bot_token": os.environ["BOT_TOKEN"],
    }

url_regex = re.compile(
    r"(?P<scheme>https?):\/\/(?P<domain>[\w_-]+(?:(?:\.[\w_-]+)+))(?P<directory>[\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])",
    flags=re.M,
)


def get_song_data(url: str) -> interactions.Embed:
    # get the data from the songwhip api
    response: requests.Response = requests.get(
        url= f"https://api.song.link/v1-alpha.1/links?url={quote(url)}&userCountry=US"
    )
    data: dict = response.json()

    # check and make sure we have a valid response
    if response.status_code not in range(200, 300):
        return interactions.Embed(
            title="Error",
            description=data,
            color=0xFF0000,
        )

    # parse the data we care about
    title = None
    artist = None
    thumbnail = None

    relevant_platforms = [
        "spotify",
        "youtubeMusic",
        "appleMusic",
        "amazonMusic",
    ]
    relevant_data = []
    for platform in relevant_platforms:
        by_platform = data["linksByPlatform"].get(platform, None)
        if by_platform == None:
            continue
        url = by_platform["url"]
        id = by_platform["entityUniqueId"]
        entity = data["entitiesByUniqueId"][id]
        if title == None: title = entity.get("title", None)
        if artist == None: artist = entity.get("artistName", None)
        if thumbnail == None: thumbnail = entity.get("thumbnailUrl", None)

        relevant_data.append({
            "platform": platform,
            "url": url,
        })

    # return the embed
    return interactions.Embed(
        title=f"{title} by {artist}",
        description="listen on:\n" + "\n".join([
            f"- [{x["platform"]}]({x["url"]})" for x in relevant_data
        ]),
        color=0x00FFFF,
        url=data["pageUrl"],
        thumbnail=thumbnail,
    )


def author_branding() -> interactions.EmbedAuthor:
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
async def music(ctx, url: str) -> None:
    await ctx.defer()

    embed = get_song_data(url)
    embed.author = author_branding()

    await ctx.respond(content=f"<{url}>", embed=embed)


@interactions.message_context_menu(name="Get Songs")
async def get_song_data_from_message(ctx: interactions.ContextMenuContext):
    await ctx.defer(ephemeral=True)

    embeds = []

    for match in url_regex.finditer(ctx.target.content):  # type: ignore
        url = match.expand(r"\g<scheme>://\g<domain>\g<directory>")

        # get the song data
        embed = get_song_data(url)
        embed.author = author_branding()

        embeds.append(embed)

    await ctx.respond(content="Found these song(s):", embeds=embeds, ephemeral=True)

if __name__ == "__main__":
    # run the bot
    bot.start(token=config["bot_token"])
