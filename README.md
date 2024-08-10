# discord-songwhip

discord bot to implement songwhip's api in-app

# usage

## configuration

With `config.json`:

```json
{
    "bot_token": "put your bot token here"
}
```

Then run as normal.

---

With environment variables, pass in the following:

```toml
BOT_TOKEN="bot token here"
```

## running without docker

Install poetry 1.8.x, then install the dependencies and run the bot:

```sh
poetry install
poetry run python3 main.py
```

## deploying to heroku

Press this funny button:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/ryleu/discord-songwhip/tree/main)

## running with docker

A Docker image is available here:
```
ghcr.io/ryleu/discord-songwhip:latest
```
