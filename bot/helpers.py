import requests
from locale import LC_ALL, setlocale, format_string
from datetime import datetime as dt
from pytz import timezone
from PIL import Image, ImageDraw, ImageFont

setlocale(LC_ALL, "en_US")


def get_active_polls():
    """Gets poll IDs"""

    response = requests.get("https://vote.makerdao.com/api/polling/all-polls")
    data = response.json()

    current_date = dt.now(timezone("UTC"))
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
                active_polls[0:5],
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


def get_polls_results(polls):
    """Gets the vote breakdown for multiple polls"""

    for poll in polls:
        response = requests.get(
            f"https://vote.makerdao.com/api/polling/tally/{poll['id']}"
        )
        data = response.json()
        poll["type"] = data["parameters"]["inputFormat"]["type"]
        poll["results"] = list(
            map(
                lambda result: {
                    "option_name": result["optionName"],
                    "mkr_support": float(result["mkrSupport"]),
                    "percentage": result["firstPct"] / 100,
                },
                data["results"],
            )
        )
    return polls


def generate_progress_bar(poll_votes):
    """Generates the vote breakdown progress bars"""

    colors = ["#5bbeae", "#dc7d39", "#7e7e86"]
    margin = 10
    bar_width, bar_height = (250, 5)
    option_height = 30
    border_radius = 5
    canvas_width, canvas_height = (
        margin + (bar_width + margin) * len(poll_votes),
        option_height
        * len(
            max(
                map(lambda poll: poll["results"], poll_votes),
                key=lambda poll: len(poll),
            )
        )
        + 40
        + margin * 2,
    )
    bar_background = (15, 15, 15)
    s_font = ImageFont.truetype("fonts/Roboto-Regular.ttf", 12)
    m_font = ImageFont.truetype("fonts/Roboto-Regular.ttf", 14)

    # Create an image
    img = Image.new("RGB", (canvas_width, canvas_height), (55, 57, 62))

    # Get a drawing context
    draw = ImageDraw.Draw(img)

    for j, poll in enumerate(poll_votes):
        draw.text(
            (margin + (margin + bar_width) * j, margin),
            f"Poll {poll.get('id')}:",
            font=m_font,
        )
        poll_title = poll.get("title")
        while draw.textlength(poll_title, m_font) > bar_width:
            poll_title = f"{poll_title[:-2]}…"
        draw.text(
            (margin + (margin + bar_width) * j, margin + 16), poll_title, font=m_font
        )

        for i, result in enumerate(poll.get("results")):
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
                    if poll.get("type") != "single-choice"
                    else colors[i],
                    radius=border_radius,
                )

    img.save("progress_bars.png", "PNG")
