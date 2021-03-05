import csv
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class BonusPayment:

    source_csv_columns = ["name", "amount"]
    csv_columns = ["name", "amount"]

    # sanity check
    max_amount = Decimal("100000.00")
    min_amount = Decimal("0.01")

    def __init__(self, employees, payment_date, request_id):
        self.request_id = request_id
        self.employees = employees
        self.payments = []
        self.employees_by_name = {e["name"]: e for e in self.employees}
        self.has_errors = False

    def load_from_csv(self, csv_file_path):
        self.employees = []

        with open(csv_file_path) as csv_file:
            payroll_data = csv.DictReader(csv_file, fieldnames=self.source_csv_columns)

            # Validste CSV column names
            if payroll_data.fieldnames != self.source_csv_columns:
                logger.error(
                    "CSV must contain these columns: %s" % self.source_csv_columns
                )
                return False

            for payment_data in payroll_data:

                # Skip the header
                if payment_data["name"] == "name":
                    continue

                employee = self._parse_employee(payment_data)

                if not employee:
                    logger.error("Can't find employee: %s" % payment_data)
                    self.has_errors = True
                    continue

                if not employee["payable"]:
                    logger.error("This employee can't be payed: %s" % employee["name"])
                    self.has_errors = True
                    continue

                amount = self._parse_amount(payment_data)

                if not amount or amount > self.max_amount or amount < self.min_amount:
                    logger.error("Wrong amount to pay: %s" % payment_data)
                    self.has_errors = True
                    continue

                self.payments.append(
                    {
                        "name": employee["name"],
                        "member_uuid": employee["uuid"],
                        "amount": amount,
                    }
                )

        return not self.has_errors

    def _parse_employee(self, payment_data):
        name = payment_data.get("name", "").strip()
        return self.employees_by_name.get(name)

    def _parse_amount(self, payment_data):
        amount = payment_data.get("amount", "").strip()
        try:
            amount = Decimal(amount)
        except:
            amount = None
        return amount

    # def print_payments(self, stream):
    #     writer = csv.DictWriter(
    #         stream,
    #         fieldnames=self.csv_columns,
    #         quoting=csv.QUOTE_MINIMAL,
    #         escapechar='\\',
    #         lineterminator='\n',
    #     )
    #     writer.writeheader()
    #     writer.writerows(self.payments)

    def print_payments(self, stream):
        row_h = "{name:<30s}\t{amount:>10s}"
        row = "{name:<30s}\t{amount:>10.2f}"
        print(
            row_h.format(**{"name": self.csv_columns[0], "amount": self.csv_columns[1]})
        )
        for payment in self.payments:
            print(row.format(**payment))
