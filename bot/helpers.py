import requests
from locale import LC_ALL, setlocale, format_string
from datetime import datetime as dt, timezone
from PIL import Image, ImageDraw, ImageFont
from math import floor

setlocale(LC_ALL, "en_US")


def get_active_votes():
    """Gets poll and executive vote IDs"""

    poll_response = requests.get("https://vote.makerdao.com/api/polling/all-polls")
    executive_response = requests.get("https://vote.makerdao.com/api/executive?limit=5")
    poll_data = poll_response.json()
    executive_data = executive_response.json()
    hat = next(e for e in executive_data if e["spellData"]["hasBeenCast"])

    current_date = dt.now(timezone.utc)
    active_polls = list(
        filter(
            lambda poll: dt.strptime(poll["endDate"], "%Y-%m-%dT%H:%M:%S.%f%z")
            > current_date,
            poll_data["polls"],
        )
    )
    active_executives = list(
        filter(
            lambda executive: executive["active"],
            executive_data,
        )
    )

    parsed_polls = sorted(
        list(
            map(
                lambda poll: {"id": poll["pollId"], "title": poll["title"]},
                active_polls,
            )
        ),
        key=lambda poll: poll["id"],
        reverse=True,
    )
    parsed_executives = sorted(
        list(
            map(
                lambda executive: {
                    "id": executive["address"],
                    "title": executive["title"],
                    "created_at": dt.strptime(
                        executive["date"],
                        "%a %b %d %Y %H:%M:%S %Z%z (Coordinated Universal Time)",
                    ),
                    "mkr_support": float(executive["spellData"]["mkrSupport"]) / 1e18,
                    "mkr_on_hat": float(hat["spellData"]["mkrSupport"]) / 1e18,
                },
                active_executives,
            )
        ),
        key=lambda executive: executive["created_at"],
        reverse=True,
    )

    return [*parsed_executives, *parsed_polls]


def get_active_polls():
    """Gets poll IDs"""

    response = requests.get("https://vote.makerdao.com/api/polling/all-polls")
    data = response.json()

    current_date = dt.now(timezone.utc)
    active_polls = list(
        filter(
            lambda poll: dt.strptime(poll["endDate"], "%Y-%m-%dT%H:%M:%S.%f%z")
            < current_date,
            data["polls"],
        )
    )

    parsed_polls = sorted(
        list(
            map(
                lambda poll: {"id": poll["pollId"], "title": poll["title"]},
                active_polls[0:12],
            )
        ),
        key=lambda poll: poll["id"],
        reverse=True,
    )

    return parsed_polls


def get_poll_votes(poll_id: str):
    """Gets the vote breakdown for a poll"""

    poll_response = requests.get(f"https://vote.makerdao.com/api/polling/{poll_id}")
    poll_data = poll_response.json()
    poll_title = poll_data.get("title")
    response = requests.get(f"https://vote.makerdao.com/api/polling/tally/{poll_id}")
    data = response.json()
    poll_results = [
        {
            "id": poll_id,
            "title": poll_title,
            "type": data["parameters"]["inputFormat"]["type"],
            "results": list(
                map(
                    lambda result: {
                        "option_name": result["optionName"],
                        "mkr_support": float(result["mkrSupport"]),
                        "percentage": result["firstPct"] / 100,
                    },
                    data["results"],
                )
            ),
        }
    ]
    return poll_results


def get_votes_results(votes):
    """Gets the vote breakdown for multiple votes"""

    for vote in votes:
        if str(vote["id"]).startswith("0x"):
            continue
        else:
            response = requests.get(
                f"https://vote.makerdao.com/api/polling/tally/{vote['id']}"
            )
            data = response.json()
            vote["type"] = data["parameters"]["inputFormat"]["type"]
            vote["results"] = list(
                map(
                    lambda result: {
                        "option_name": result["optionName"],
                        "mkr_support": float(result["mkrSupport"]),
                        "percentage": result["firstPct"] / 100,
                    },
                    data["results"],
                )
            )
    return votes


def generate_progress_bar(votes):
    """Generates the vote breakdown progress bars"""

    colors = ["#5bbeae", "#dc7d39", "#7e7e86"]
    margin = 10
    bar_width, bar_height = (250, 5)
    option_height = 30
    border_radius = 5
    canvas_width, canvas_height = (
        margin + (bar_width + margin) * len(votes),
        option_height
        * len(
            max(
                map(lambda vote: vote.get("results", []), votes),
                key=lambda vote: len(vote),
            )
        )
        + 40
        + margin * 2,
    )
    bar_background = (15, 15, 15)
    img_background = (47, 49, 54)
    s_font = ImageFont.truetype("fonts/Roboto-Regular.ttf", 12)
    m_font = ImageFont.truetype("fonts/Roboto-Regular.ttf", 14)

    # Create an image
    img = Image.new("RGB", (canvas_width, canvas_height), img_background)

    # Get a drawing context
    draw = ImageDraw.Draw(img)

    for j, vote in enumerate(votes):
        if str(vote["id"]).startswith("0x"):
            bar_y = margin + 45

            draw.text(
                (margin + (margin + bar_width) * j, margin),
                f"Executive {vote['id'][0:6]}...{vote['id'][-4:]}:",
                font=m_font,
            )
            spell_title = vote.get("title")
            while draw.textlength(spell_title, m_font) > bar_width:
                spell_title = f"{spell_title[:-2]}…"
            draw.text(
                (margin + (margin + bar_width) * j, margin + 16),
                spell_title,
                font=m_font,
            )

            draw.text(
                (margin + (margin + bar_width) * j, bar_y),
                f"{format_string('%d', vote['mkr_support'], grouping=True)} MKR ({floor((vote['mkr_support'] / vote['mkr_on_hat']) * 100)}%)",
                font=s_font,
            )
            draw.text(
                (margin + (margin + bar_width) * j + bar_width, bar_y),
                f"{format_string('%d', vote['mkr_on_hat'] - vote['mkr_support'], grouping=True)} more needed"
                if vote["mkr_on_hat"] - vote["mkr_support"] > 0
                else "",
                font=s_font,
                anchor="ra",
            )

            # Draw the background
            draw.rounded_rectangle(
                (
                    margin + (margin + bar_width) * j,
                    bar_y + 16,
                    margin + (margin + bar_width) * j + bar_width,
                    bar_y + 16 + bar_height,
                ),
                fill=bar_background,
                radius=border_radius,
            )
            # Draw the progress bar
            draw.rounded_rectangle(
                (
                    margin + (margin + bar_width) * j,
                    bar_y + 16,
                    margin
                    + (margin + bar_width) * j
                    + (bar_width * (vote["mkr_support"] / vote["mkr_on_hat"])),
                    bar_y + 16 + bar_height,
                ),
                fill="#f4b731",
                radius=border_radius,
            )

        else:
            draw.text(
                (margin + (margin + bar_width) * j, margin),
                f"Poll {vote.get('id')}:",
                font=m_font,
            )
            poll_title = vote.get("title")
            while draw.textlength(poll_title, m_font) > bar_width:
                poll_title = f"{poll_title[:-2]}…"
            draw.text(
                (margin + (margin + bar_width) * j, margin + 16),
                poll_title,
                font=m_font,
            )

            for i, result in enumerate(vote.get("results")):
                bar_y = margin + 45 + (option_height * i)
                bar_fill_width = bar_width * result.get("percentage", 0)

                option_name = result.get("option_name")
                while draw.textlength(option_name, s_font) > bar_width / 2:
                    option_name = f"{option_name[:-2]}…"
                draw.text(
                    (margin + (margin + bar_width) * j, bar_y), option_name, font=s_font
                )

                draw.text(
                    (margin + (margin + bar_width) * j + bar_width, bar_y),
                    f'{format_string("%10.0f", result.get("mkr_support"), grouping=True)} MKR - {round(result.get("percentage") * 100)}%',
                    font=s_font,
                    anchor="ra",
                )
                # Draw the background
                draw.rounded_rectangle(
                    (
                        margin + (margin + bar_width) * j,
                        bar_y + 16,
                        margin + (margin + bar_width) * j + bar_width,
                        bar_y + 16 + bar_height,
                    ),
                    fill=bar_background,
                    radius=border_radius,
                )
                # Draw the progress bar
                if result.get("percentage", 0) != 0:
                    draw.rounded_rectangle(
                        (
                            margin + (margin + bar_width) * j,
                            bar_y + 16,
                            margin + (margin + bar_width) * j + bar_fill_width,
                            bar_y + 16 + bar_height,
                        ),
                        fill=colors[0]
                        if vote.get("type") != "single-choice"
                        else colors[i],
                        radius=border_radius,
                    )

    img.save("progress_bars.png", "PNG")
