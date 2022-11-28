import discord
from datetime import datetime, timezone
from helpers import generate_progress_bar
from constants import VoteType


class VotesEmbed(discord.Embed):
    def __init__(self, vote_type, vote, votes_length, finished, tag_filter=None):
        super().__init__(
            title=f"{'On-chain polls' if vote_type == VoteType.POLL.value else 'Executive votes'}",
            description=f"Vote breakdown for {'on-chain polls' if vote_type == VoteType.POLL.value else 'executive votes'}",
            color=0xF4B731,
            timestamp=datetime.now(timezone.utc),
        )
        self.set_image(url="attachment://progress_bars.png")
        self.set_footer(
            text=f"{votes_length} {'poll' if vote_type == VoteType.POLL.value else 'executive vote'}{'s' if votes_length > 1 else ''}"
        )
        self.add_field(
            name=vote_type,
            value=f"[{vote['id']}](https://vote.makerdao.com/polling/{vote['id']}) - {vote['title']}"
            if vote_type == VoteType.POLL.value
            else f"[{vote['id'][:6]}...{vote['id'][-4:]}](https://vote.makerdao.com/executive/{vote['id']}) - {vote['title']}",
            inline=False,
        )
        self.add_field(
            name="Status",
            value=(
                "Executed"
                if vote["has_been_cast"]
                else "Scheduled"
                if vote["has_been_scheduled"]
                else "Live"
            )
            if vote_type == VoteType.EXECUTIVE.value
            else ("Active" if not finished else "Ended"),
            inline=True,
        )
        if tag_filter:
            self.add_field(name="Tag filter", value=tag_filter, inline=True)


class Dropdown(discord.ui.Select):
    def __init__(self, votes, vote_type, vote_selected, finished):
        self.votes = votes
        self.vote_type = vote_type
        self.finished = finished
        options = [
            discord.SelectOption(
                label=f"{vote_type} {vote['id']}",
                value=vote["id"],
                description=vote["title"]
                if len(vote["title"]) <= 100
                else f"{vote['title'][:99]}…",
                default=True if vote["id"] == vote_selected["id"] else False,
            )
            for vote in votes
        ]

        super().__init__(
            placeholder=f"Select {'a poll' if vote_type == VoteType.POLL.value else 'an executive vote'}",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        next_vote = next(
            vote for vote in self.votes if str(vote["id"]) == self.values[0]
        )
        generate_progress_bar(next_vote)
        progress_bar_file = discord.File("progress_bars.png")

        await interaction.response.edit_message(
            attachments=[progress_bar_file],
            embed=VotesEmbed(
                vote_type=self.vote_type,
                vote=next_vote,
                votes_length=len(self.votes),
                finished=self.finished,
            ),
            view=NavigationRow(
                votes=self.votes,
                vote_type=self.vote_type,
                vote_selected=next_vote,
                finished=self.finished,
            ),
        )


class NavigationRow(discord.ui.View):
    def __init__(self, votes, vote_type, vote_selected, finished):
        super().__init__()
        self.add_item(Dropdown(votes, vote_type, vote_selected, finished=finished))
