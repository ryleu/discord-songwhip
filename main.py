#!/bin/env -S poetry run python

import json
import requests
import os
import interactions
import re

if os.path.exists("config.json"):
    with open("config.json") as file:
        config = json.loads(file.read())
else:
    config = {
        "bot_token": os.environ["BOT_TOKEN"],
        "disable_branding": os.environ["DISABLE_BRANDING"],
    }

url_regex = re.compile(
    r"(?P<scheme>https?):\/\/(?P<domain>[\w_-]+(?:(?:\.[\w_-]+)+))(?P<directory>[\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])",
    flags=re.M,
)


def get_song_data(url: str) -> interactions.Embed:
    # get the data from the songwhip api
    response = requests.post(url="https://songwhip.com", data=json.dumps({"url": url}))
    data = response.json()

    # check and make sure we have a valid response
    data["status"] = data.get("status", "ok")

    if data["status"] == "error":
        return interactions.Embed(
            title="Error",
            description=data["error"]["message"],
            color=0xFF0000,
        )
    elif data["status"] != "ok":
        return interactions.Embed(
            title="Unknown status",
            description=json.dumps(data),
            color=0xFF0000,
        )

    # return the embed
    return interactions.Embed(
        title=data["name"],
        description="**By:** "
        + "".join(
            # create a list of artist names to combine into a string
            ["\n- " + artist["name"] for artist in data["artists"]]
        )
        + f"\n\n**Type:** {data['type']}",
        color=0x00FFFF,
        url=data["url"],
        thumbnail=data["image"],
    )


def author_branding():
    if config["disable_branding"]:
        return None
    return interactions.EmbedAuthor(
        name="Help pay for server costs!",
        icon_url="https://cdn.discordapp.com/attachments/810959625306243095/1160059628281929810/kofi_s_logo_nolabel.png",
        url="https://ko-fi.com/ryleu",
    )


bot = interactions.Client()


@interactions.listen()
async def on_startup():
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
async def music(ctx, url: str):
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


# run the bot
bot.start(token=config["bot_token"])
