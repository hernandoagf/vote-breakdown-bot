import discord
from typing import Optional
from discord import app_commands
import os
from dotenv import load_dotenv
import logging
from helpers import *

load_dotenv()
bot_token = os.getenv("BOT_TOKEN")


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    # async def setup_hook(self):
    #     await self.tree.sync()


intents = discord.Intents.default()
client = MyClient(intents=intents)


class NavigationRow(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(emoji="⬅️", disabled=True)
    async def navigate_previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.edit_message(content="Previous page", attachments=[])

    @discord.ui.button(emoji="➡️")
    async def navigate_next(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.edit_message(content="Next page", attachments=[])


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.tree.command()
async def votes(interaction: discord.Interaction):
    """Displays the vote breakdown for the currently active on-chain votes"""

    await interaction.response.defer()

    active_polls = get_active_polls()
    results = get_polls_results(active_polls)
    polls_length = len(results)

    generate_progress_bar(results if polls_length <= 3 else results[0:3])
    progress_bar_file = discord.File("progress_bars.png")

    if polls_length <= 3:
        await interaction.followup.send(file=progress_bar_file)
    else:
        await interaction.followup.send(
            f"Displaying 1-3 of {polls_length} votes",
            file=progress_bar_file,
            view=NavigationRow(),
        )


@client.tree.command()
@app_commands.describe(poll_id="ID of the poll")
async def poll_results(interaction: discord.Interaction, poll_id: int):
    """Displays the vote breakdown for a poll"""

    await interaction.response.defer()

    poll_votes = get_poll_votes(poll_id)
    generate_progress_bar(poll_votes)

    progress_bar_file = discord.File("progress_bars.png")
    await interaction.followup.send(file=progress_bar_file)


client.run(bot_token, log_handler=logging.StreamHandler())
