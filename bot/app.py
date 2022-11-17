import discord
from typing import Optional
from discord import app_commands
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timezone
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


class VotesEmbed(discord.Embed):
    def __init__(self, image, footer_text=None):
        super().__init__(
            title="Active votes",
            description="Vote breakdown for currently active on-chain polls and executive votes",
            color=0xF4B731,
            timestamp=datetime.now(timezone.utc),
        )
        self.set_image(url=image)
        self.set_footer(text=footer_text)


class NavigationRow(discord.ui.View):
    def __init__(self, results):
        super().__init__()
        self.value = None
        self.results = results
        self.page = 0

    @discord.ui.button(emoji="⬅️", disabled=True, custom_id="previous_button")
    async def navigate_previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.page -= 1
        if self.children[1].disabled:
            self.children[1].disabled = False
        button.disabled = True if self.page == 0 else False
        items_displayed = (self.page * 3, (self.page * 3) + 3)

        generate_progress_bar(self.results[(items_displayed[0]) : (items_displayed[1])])
        progress_bar_file = discord.File("progress_bars.png")

        await interaction.response.edit_message(
            attachments=[progress_bar_file],
            embed=VotesEmbed(
                image="attachment://progress_bars.png",
                footer_text=f"Displaying {items_displayed[0] + 1}-{items_displayed[1]} of {len(self.results)} active votes",
            ),
            view=self,
        )

    @discord.ui.button(emoji="➡️", disabled=False, custom_id="next_button")
    async def navigate_next(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.page += 1
        if self.children[0].disabled:
            self.children[0].disabled = False
        button.disabled = True if (self.page * 3) + 3 >= len(self.results) else False
        items_displayed = (
            self.page * 3,
            len(self.results) if button.disabled else (self.page * 3) + 3,
        )
        generate_progress_bar(self.results[items_displayed[0] : items_displayed[1]])
        progress_bar_file = discord.File("progress_bars.png")

        await interaction.response.edit_message(
            attachments=[progress_bar_file],
            embed=VotesEmbed(
                image="attachment://progress_bars.png",
                footer_text=f"Displaying {items_displayed[0] + 1}-{items_displayed[1]} of {len(self.results)} active votes",
            ),
            view=self,
        )


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.tree.command()
async def votes(interaction: discord.Interaction):
    """Displays the vote breakdown for the currently active on-chain votes"""

    await interaction.response.defer()

    active_votes = get_active_votes()
    results = get_votes_results(active_votes)
    votes_length = len(results)

    generate_progress_bar(results if votes_length <= 3 else results[0:3])
    progress_bar_file = discord.File("progress_bars.png")

    if votes_length <= 3:
        await interaction.followup.send(
            file=progress_bar_file,
            embed=VotesEmbed(image="attachment://progress_bars.png"),
        )
    else:
        await interaction.followup.send(
            file=progress_bar_file,
            embed=VotesEmbed(
                image="attachment://progress_bars.png",
                footer_text=f"Displaying 1-3 of {votes_length} active votes",
            ),
            view=NavigationRow(results=results),
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
