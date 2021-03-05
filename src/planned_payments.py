import uuid
from time import sleep

import click
import logging
from datetime import datetime

from justworks import API


@click.command()
@click.option(
    "--username", prompt="Username", help="Justworks account username.", required=True
)
@click.option(
    "--password",
    prompt="Password (hidden)",
    help="Justworks account password.",
    hide_input=True,
)
def main(username, password):
    """
    """

    utc_dt = datetime.utcnow().replace(microsecond=0).isoformat("_")

    request_id = "{}_{}".format(utc_dt, uuid.uuid4().hex[:4].upper())

    click.secho("Start request, id: %s" % request_id, fg="bright_blue")

    api = API(username=username, password=password)

    # Get predefined values from Justworks website
    employees, _, _ = api.get_constants()

    planned_payments = []
    for employee in employees:
        planned_payments += api.get_user_payments(
            user_uuid=employee["uuid"], user_name=employee["name"]
        )
        sleep(0.1)

    click.secho("All currently planned payment:", fg="bright_blue")
    for planned_payment in planned_payments:
        print(planned_payment)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(levelname)s: %(message)s", level=logging.INFO,
    )
    main()
