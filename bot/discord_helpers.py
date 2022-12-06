import discord
from discord import Interaction
from typing import Optional
from helpers import get_polls, get_executives, generate_progress_bar
from ui_elements import VotesEmbed, NavigationRow
from constants import VoteType


async def display_polls(
    interaction: Interaction, tag: Optional[str], finished: bool, poll_tags
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
    if not polls:
        await interaction.followup.send(
            f"There were no {'finished' if finished else 'active'} polls found{' for the tag you specified. Please, try with another tag.' if tag else '. Please, try again later.'}"
        )
        return

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


async def display_execs(interaction: Interaction):
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
            finished=False,
        ),
        view=NavigationRow(
            votes=found_execs,
            vote_type=VoteType.EXECUTIVE.value,
            vote_selected=found_execs[0],
            finished=False,
        ),
    )
