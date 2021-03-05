import sys
import uuid

import click
import logging
from datetime import datetime

from employee import BonusPayment
from justworks import API


@click.command()
@click.argument("data_csv", type=click.Path(exists=True))
@click.option(
    "--username", prompt="Username", help="Justworks account username.", required=True
)
@click.option(
    "--password",
    prompt="Password (hidden)",
    help="Justworks account password.",
    hide_input=True,
)
@click.option(
    "--pay-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    required=True,
    help="Payment date.",
)
@click.option(
    "--dry", default=False, is_flag=True, help="Dry run. Do not change anything."
)
def main(data_csv, username, password, pay_date, dry):
    """The script reads payroll data from the CSV input file
    and creates payments in the Justworks dashboard.

    CSV file must contain these columns: name, amount, type, note.
    """

    utc_dt = datetime.utcnow().replace(microsecond=0).isoformat("_")

    request_id = "{}_{}".format(utc_dt, uuid.uuid4().hex[:4].upper())

    click.secho("Start request, id: %s" % request_id, fg="bright_blue")

    api = API(username=username, password=password)

    # Get predefined values from Justworks website
    employees, _, _ = api.get_constants()

    click.secho("\nPersons found: %s" % len(employees), fg="bright_blue")

    bonuses = BonusPayment(employees=employees, payment_date="", request_id=request_id)

    click.secho("\nParse CSV file", fg="bright_blue")

    # Parse CSV, validate and match values
    all_good = bonuses.load_from_csv(data_csv)

    click.secho("\nPayments to create:", fg="bright_blue")

    # Print payment list
    bonuses.print_payments(sys.stdout)

    if not all_good:
        click.secho(
            "\nThere was some errors. Please fix it before continuing.", fg="bright_red"
        )
        sys.exit()

    if not dry:
        click.secho("\nCreate payments", fg="bright_blue")

        # Create Justworks bonus payments
        res = api.create_bonus_payments(
            bonuses.payments, pay_date=pay_date, note=request_id,
        )

        if res:
            click.secho("\nPayments creation error.", fg="bright_red")
            click.secho("status code: %s" % res.status_code, fg="bright_red")
            click.secho("response text: %s" % res.text, fg="bright_red")
        else:
            click.secho("DONE", fg="green")

        # Validate created payments
        # api.validate_payments() ???


if __name__ == "__main__":
    logging.basicConfig(
        format="%(levelname)s: %(message)s", level=logging.INFO,
    )
    main()
