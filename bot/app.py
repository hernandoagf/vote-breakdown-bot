import discord
from discord import app_commands, Interaction
import os
from dotenv import load_dotenv
import logging
from helpers import get_polls, get_executives, generate_progress_bar
from ui_elements import VotesEmbed, NavigationRow
from constants import VoteType
import schedule
import requests
from typing import Optional

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
    print("Executing job")
    response = requests.get(
        "https://raw.githubusercontent.com/makerdao/community/master/governance/polls/meta/tags.json"
    )
    data = response.json()
    global poll_tags
    poll_tags = [tag["id"] for tag in data]


schedule.every(10).seconds.do(fetch_tags_job)
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
    name="test", description="Displays the vote breakdown for on-chain polls"
)


@polls_group.command(name="finished")
async def finished_votes(interaction: Interaction):
    await interaction.response.send_message("Hello")


client.tree.add_command(polls_group)


@client.tree.command()
@app_commands.describe(
    tag="Optional: the poll tag to filter for",
    finished="Optional: whether to display finished instead of active polls",
)
@app_commands.autocomplete(tag=tag_autocomplete)
async def votes(
    interaction: Interaction,
    tag: Optional[str],
    test_param: discord.AppCommandType,
    finished: bool = False,
):
    """Displays the vote breakdown for on-chain polls"""

    if tag:
        tag = tag.lower()
    if tag and tag not in poll_tags:
        await interaction.response.send_message(
            content="The tag you specified was not found in the list of available tags, please try again.",
            ephemeral=True,
        )
        return

    await interaction.response.defer()

    polls = get_polls(finished, tag)
    polls_length = len(polls)
    generate_progress_bar(polls[0])
    progress_bar_file = discord.File("progress_bars.png")

    await interaction.followup.send(
        file=progress_bar_file,
        embed=VotesEmbed(
            vote_type=VoteType.POLL.value,
            vote=polls[0],
            tag_filter=tag,
            votes_length=polls_length,
            finished=finished,
        ),
        view=NavigationRow(
            votes=polls,
            vote_type=VoteType.POLL.value,
            vote_selected=polls[0],
            finished=finished,
        ),
    )


@client.tree.command(name="execs")
@app_commands.describe(
    finished="Optional: whether to display finished instead of active or latest executive votes",
)
async def executives(interaction: Interaction, finished: bool = False):
    """Displays the vote breakdown for executive votes"""

    await interaction.response.defer()

    found_execs = get_executives()
    execs_length = len(found_execs)
    generate_progress_bar(found_execs[0])
    progress_bar_file = discord.File("progress_bars.png")

    await interaction.followup.send(
        file=progress_bar_file,
        embed=VotesEmbed(
            vote_type=VoteType.EXECUTIVE.value,
            vote=found_execs[0],
            votes_length=execs_length,
            finished=finished,
        ),
        view=NavigationRow(
            votes=found_execs,
            vote_type=VoteType.EXECUTIVE.value,
            vote_selected=found_execs[0],
            finished=finished,
        ),
    )


client.run(bot_token, log_handler=logging.StreamHandler())
