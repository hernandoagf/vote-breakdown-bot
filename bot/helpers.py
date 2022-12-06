import requests
from locale import LC_ALL, setlocale, getdefaultlocale, format_string
from datetime import datetime as dt, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
from math import floor

setlocale(LC_ALL, getdefaultlocale())


def get_executives():
    """Gets information about executive votes"""

    response = requests.get("https://vote.makerdao.com/api/executive?limit=5")
    data = response.json()
    hat = next(e for e in data if e["spellData"]["hasBeenScheduled"])

    found_executives = [executive for executive in data if executive["active"]]

    return [
        {
            "id": executive["address"],
            "title": executive["title"],
            "created_at": dt.strptime(
                executive["date"],
                "%a %b %d %Y %H:%M:%S %Z%z (Coordinated Universal Time)",
            ),
            "mkr_support": float(executive["spellData"]["mkrSupport"]) / 1e18,
            "mkr_on_hat": float(hat["spellData"]["mkrSupport"]) / 1e18,
            "has_been_scheduled": executive["spellData"]["hasBeenScheduled"],
            "has_been_cast": executive["spellData"]["hasBeenCast"],
        }
        for executive in found_executives
    ]


def get_polls(finished: bool, tag):
    """Gets information about on-chain polls"""

    response = requests.get("https://vote.makerdao.com/api/polling/all-polls")
    data = response.json()
    current_date = dt.now(timezone.utc)

    tag_filtered_polls = (
        [
            poll
            for poll in data["polls"]
            for poll_tag in poll["tags"]
            if poll_tag["id"] == tag
        ]
        if tag
        else data["polls"]
    )

    found_polls = (
        [
            poll
            for poll in tag_filtered_polls
            if dt.strptime(poll["endDate"], "%Y-%m-%dT%H:%M:%S.%f%z") > current_date
        ]
        if not finished
        else [
            poll
            for poll in tag_filtered_polls
            if dt.strptime(poll["endDate"], "%Y-%m-%dT%H:%M:%S.%f%z") < current_date
        ][:10]
    )

    polls = [{"id": poll["pollId"], "title": poll["title"]} for poll in found_polls]

    for poll in polls:
        response = requests.get(
            f"https://vote.makerdao.com/api/polling/tally/{poll['id']}"
        )
        data = response.json()
        poll["type"] = data["parameters"]["inputFormat"]["type"]
        poll["results"] = [
            {
                "option_name": result["optionName"],
                "option_id": result["optionId"],
                "mkr_support": float(result["mkrSupport"])
                + float(result.get("transfer", 0)),
                "percentage": (result["firstPct"] + result.get("transferPct", 0)) / 100,
            }
            for result in data["results"]
        ]

    return sorted(polls, key=lambda poll: poll["id"])


def get_new_polls():
    """Gets the list of polls posted in the last 24 hours"""

    response = requests.get("https://vote.makerdao.com/api/polling/all-polls")
    data = response.json()
    current_date = dt.now(timezone.utc)
    one_day = timedelta(days=1)

    new_polls = [
        poll
        for poll in data["polls"]
        if dt.strptime(poll["startDate"], "%Y-%m-%dT%H:%M:%S.%f%z")
        >= current_date - one_day
    ]

    return [
        {
            "id": poll["pollId"],
            "title": poll["title"],
            "github": poll["url"].replace(
                "raw.githubusercontent.com/makerdao/community/",
                "github.com/makerdao/community/blob/",
            ),
        }
        for poll in new_polls
    ]


def generate_progress_bar(vote):
    """Generates the vote breakdown progress bars"""

    colors = ["#7e7e86", "#5bbeae", "#dc7d39"]
    margin = 10
    bar_width, bar_height = (380, 5)
    option_height = 30
    border_radius = 5
    canvas_width, canvas_height = (
        bar_width + (margin * 2),
        option_height * len(vote.get("results", [""])) + margin * 2,
    )
    bar_background = (15, 15, 15)
    img_background = (47, 49, 54)
    s_font = ImageFont.truetype("fonts/Roboto-Regular.ttf", 12)
    m_font = ImageFont.truetype("fonts/Roboto-Regular.ttf", 14)

    # Create an image
    img = Image.new("RGB", (canvas_width, canvas_height), img_background)

    # Get a drawing context
    draw = ImageDraw.Draw(img)

    if str(vote["id"]).startswith("0x"):
        draw.text(
            (margin, margin),
            f"{format_string('%d', vote['mkr_support'], grouping=True)} MKR ({floor((vote['mkr_support'] / vote['mkr_on_hat']) * 100)}%)",
            font=s_font,
        )
        draw.text(
            (margin + bar_width, margin),
            f"{format_string('%d', vote['mkr_on_hat'] - vote['mkr_support'], grouping=True)} more needed"
            if vote["mkr_on_hat"] - vote["mkr_support"] > 0
            else "",
            font=s_font,
            anchor="ra",
        )

        # Draw the background
        draw.rounded_rectangle(
            (
                margin,
                margin + 16,
                margin + bar_width,
                margin + 16 + bar_height,
            ),
            fill=bar_background,
            radius=border_radius,
        )
        # Draw the progress bar
        draw.rounded_rectangle(
            (
                margin,
                margin + 16,
                margin + (bar_width * (vote["mkr_support"] / vote["mkr_on_hat"])),
                margin + 16 + bar_height,
            ),
            fill="#f4b731",
            radius=border_radius,
        )

    else:
        for i, result in enumerate(vote.get("results")):
            bar_y = margin + (option_height * i)
            bar_fill_width = bar_width * result.get("percentage", 0)

            option_name = result.get("option_name")
            while draw.textlength(option_name, s_font) > bar_width * 0.70:
                option_name = f"{option_name[:-2]}…"
            draw.text((margin, bar_y), option_name, font=s_font)

            draw.text(
                (margin + bar_width, bar_y),
                f'{format_string("%10.0f", result.get("mkr_support"), grouping=True)} MKR - {round(result.get("percentage") * 100)}%',
                font=s_font,
                anchor="ra",
            )
            # Draw the background
            draw.rounded_rectangle(
                (
                    margin,
                    bar_y + 16,
                    margin + bar_width,
                    bar_y + 16 + bar_height,
                ),
                fill=bar_background,
                radius=border_radius,
            )
            # Draw the progress bar
            if result.get("percentage", 0) != 0:
                draw.rounded_rectangle(
                    (
                        margin,
                        bar_y + 16,
                        margin + bar_fill_width,
                        bar_y + 16 + bar_height,
                    ),
                    fill=colors[1]
                    if vote.get("type") != "single-choice"
                    else colors[result["option_id"]],
                    radius=border_radius,
                )

    img.save("progress_bars.png", "PNG")
