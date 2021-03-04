import sys
import uuid
import click
import logging
from datetime import datetime
from justworks import API
from payroll import Payroll


@click.command()
@click.argument("data_csv", type=click.Path(exists=True))
@click.option("--username", prompt="Username", help="Justworks account username.")
@click.option(
    "--password",
    prompt="Password (hidden)",
    help="Justworks account password.",
    hide_input=True,
)
@click.option(
    "--dry", default=False, is_flag=True, help="Dry run. Do not change anything."
)
def main(data_csv, username, password, dry):
    """The script reads payroll data from the CSV input file
    and creates payments in the Justworks dashboard.

    CSV file must contain these columns: name, amount, type, note.
    """

    utc_dt = datetime.utcnow().replace(microsecond=0).isoformat("_")

    request_id = "{date}_{rnd}".format(
        **{"date": utc_dt, "rnd": uuid.uuid4().hex[:4].upper(),}
    )

    click.secho("Start request, id: %s" % request_id, fg="bright_blue")

    api = API(username=username, password=password)

    # Get predefined values from Justworks website
    employees, payment_dates, fringe_benefits_subtypes = api.get_constants()

    click.secho("\nPersons found: %s" % len(employees), fg="bright_blue")

    click.secho("\nSupported payment dates:", fg="bright_blue")
    for pd_key, pd_value in payment_dates.items():
        click.secho(pd_key, fg="bright_white")
        for day in pd_value:
            fg = "red" if day["disabled"] else None
            click.secho("  {value}, {description}".format(**day), fg=fg)

    click.secho("\nSupported payment types:", fg="bright_blue")
    for subtype in fringe_benefits_subtypes:
        click.secho("{value} — {description}".format(**subtype))

    payroll = Payroll(
        employees=employees,
        payment_dates=payment_dates,
        fringe_benefits_subtypes=fringe_benefits_subtypes,
        request_id=request_id,
    )

    click.secho("\nParse CSV file", fg="bright_blue")

    # Parse CSV, validate and match values
    all_good = payroll.load_from_csv(data_csv)

    click.secho("\nPayments to create:", fg="bright_blue")

    # Print payment list
    payroll.print_payments(sys.stdout)

    if not all_good:
        click.secho(
            "\nThere was some errors. Please fix it before continuing.", fg="bright_red"
        )
        sys.exit()

    if not dry:
        click.secho("\nCreate payments", fg="bright_blue")

        # Create Justworks payments
        res = api.create_payments(payroll.payments)

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
