import csv
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class Payroll:

    source_csv_columns = ['name', 'amount', 'type', 'note']
    csv_columns = ['name', 'member_uuid', 'pay_date', 'amount', 'subtype', 'note']

    # sanity check
    max_amount = Decimal('100000.00')
    min_amount = Decimal('0.01')

    def __init__(self, employees, payment_dates, fringe_benefits_subtypes, request_id):
        self.request_id = request_id
        self.employees = employees
        self.payment_dates = payment_dates
        self.fringe_benefits_subtypes = fringe_benefits_subtypes
        self.payments = []
        self.employees_by_name = {e['name']: e for e in self.employees}
        self.fringe_benefits_subtypes_by_value = {s['value']: s for s in self.fringe_benefits_subtypes}
        self.has_errors = False

    def load_from_csv(self, csv_file_path):
        self.employees = []

        with open(csv_file_path) as csv_file:
            payroll_data = csv.DictReader(csv_file, fieldnames=self.source_csv_columns)

            # Validste CSV column names
            if payroll_data.fieldnames != self.source_csv_columns:
                logger.error('CSV must contain these columns: %s' % self.source_csv_columns)
                return False

            for payment_data in payroll_data:

                # Skip the header
                if payment_data['name'] == 'name':
                    continue

                employee = self._parse_employee(payment_data)

                if not employee:
                    logger.error('Can\'t find employee: %s' % payment_data)
                    self.has_errors = True
                    continue

                if not employee['payable']:
                    logger.error('This employee can\'t be payed: %s' % employee['name'])
                    self.has_errors = True
                    continue

                pay_frequency = employee['current_member_state']['pay_frequency']

                if not pay_frequency or pay_frequency not in self.payment_dates:
                    logger.error('Wrong pay_frequency: %s' % pay_frequency)
                    self.has_errors = True
                    continue

                pay_date = self._get_payment_date(pay_frequency)

                if not pay_date:
                    logger.error('No suitable payment date for employee: %s' % payment_data)
                    self.has_errors = True
                    continue

                note = '{request_id} {note}'.format(**{
                    'request_id': self.request_id,
                    'note': payment_data['note'],
                })

                subtype = self._parse_subtype(payment_data)

                if not subtype:
                    logger.error('Can\'t find fringe benefits subtype: %s' % payment_data)
                    self.has_errors = True
                    continue

                amount = self._parse_amount(payment_data)

                if not amount or amount > self.max_amount or amount < self.min_amount:
                    logger.error('Wrong amount to pay: %s' % payment_data)
                    self.has_errors = True
                    continue

                self.payments.append({
                    'name': employee['name'],
                    'member_uuid': employee['uuid'],
                    'pay_date': pay_date,
                    'amount': amount,
                    'subtype': subtype,
                    'note': note,
                })

        return not self.has_errors

    def _get_payment_date(self, pay_frequency):
        """ Get the nearest payment date for this payment frequency """
        dates = self.payment_dates[pay_frequency]
        # reorder by date
        dates = sorted(dates, key=lambda k: k['value'])
        # filter out disabled dates
        dates = list(filter(lambda x: x['disabled'] is False, dates))
        if dates:
            return dates[0].get('value')
        else:
            return None

    def _parse_employee(self, payment_data):
        name = payment_data.get('name', '').strip()
        return self.employees_by_name.get(name)

    def _parse_subtype(self, payment_data):
        st = payment_data.get('type', '').strip()
        return self.fringe_benefits_subtypes_by_value.get(st, {}).get('value')

    def _parse_amount(self, payment_data):
        amount = payment_data.get('amount', '').strip()
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
        row_h = "{name:<30s}\t{pay_date}\t{amount:>10s}\t{subtype:<40s}\t{note:<20s}"
        row = "{name:<30s}\t{pay_date}\t{amount:>10.2f}\t{subtype:<40s}\t{note:<20s}"
        print(row_h.format(**{
            'name': self.csv_columns[0],
            'pay_date': self.csv_columns[2],
            'amount': self.csv_columns[3],
            'subtype': self.csv_columns[4],
            'note': self.csv_columns[5],
        }))
        for payment in self.payments:
            print(row.format(**payment))
