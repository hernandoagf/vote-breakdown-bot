import discord
from discord import app_commands, Interaction
import os
from dotenv import load_dotenv
import logging
from discord_helpers import display_polls, display_execs
from helpers import get_new_polls
import schedule
import requests
from typing import Optional
import csv

load_dotenv()
bot_token = os.getenv("BOT_TOKEN")


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


intents = discord.Intents.default()
client = MyClient(intents=intents)
poll_tags = []


def fetch_tags_job():
    response = requests.get(
        "https://raw.githubusercontent.com/makerdao/community/master/governance/polls/meta/tags.json"
    )
    data = response.json()
    global poll_tags
    poll_tags = [tag["id"] for tag in data]


schedule.every().day.do(fetch_tags_job)
schedule.run_all()


async def tag_autocomplete(interaction: Interaction, current: str):
    return [
        app_commands.Choice(name=tag, value=tag)
        for tag in poll_tags
        if current.lower() in tag.lower()
    ][:25]


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


polls_group = app_commands.Group(
    name="polls", description="Displays the vote breakdown for on-chain polls"
)


@polls_group.command(name="active")
@app_commands.describe(tag="Optional: the poll tag to filter for")
@app_commands.autocomplete(tag=tag_autocomplete)
async def active_votes(interaction: Interaction, tag: Optional[str]):
    """Displays the vote breakdown for active on-chain polls"""
    await display_polls(interaction, tag, finished=False, poll_tags=poll_tags)


@polls_group.command(name="finished")
@app_commands.describe(tag="Optional: the poll tag to filter for")
@app_commands.autocomplete(tag=tag_autocomplete)
async def finished_votes(interaction: Interaction, tag: Optional[str]):
    """Displays the vote breakdown for finished on-chain polls"""
    await display_polls(interaction, tag, finished=True, poll_tags=poll_tags)


@polls_group.command(name="new")
@app_commands.describe(
    github="Optional: Whether to display the GitHub copy for the poll"
)
async def new_votes(interaction: Interaction, github: bool = False):
    """Displays the list of polls posted in the last 24 hours"""
    await interaction.response.defer()
    new_polls = get_new_polls()

    if not new_polls:
        await interaction.followup.send(
            content="There are currently no new polls created in the last 24 hours. Please, try again later.",
        )
        return

    with open("./polls_list.csv", "w") as csvfile:
        csvwriter = csv.writer(csvfile)

        csvwriter.writerow(["id", "title", "github"] if github else ["id", "title"])
        csvwriter.writerows(
            (
                [[poll["id"], poll["title"], poll["github"]] for poll in new_polls]
                if github
                else [[poll["id"], poll["title"]] for poll in new_polls]
            )
        )

    polls_csv_file = discord.File("polls_list.csv")

    await interaction.followup.send(
        content="Here's the list of polls created in the last 24 hours.",
        file=polls_csv_file,
    )


client.tree.add_command(polls_group)


@client.tree.command(name="execs")
async def active_execs(interaction: Interaction):
    """Displays the vote breakdown for active or latest executive votes"""
    await display_execs(interaction)


client.run(bot_token, log_handler=logging.StreamHandler())
