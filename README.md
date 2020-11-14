The script reads payroll data from the CSV input file and creates payments in the Justworks dashboard.

## Installation

Install virtualenv with python3:
```bash
virtualenv .venv -p python3
```

Install python dependencies:
```bash
.venv/bin/pip install -Ur requirements.txt
```

## Running

Display help text:
```bash
python ./src/main.py --help
```

Dry run with the example data:
```bash
python ./src/main.py example.csv --username=your_justworks_username --dry
```

## CSV format

```text
name,amount,type,note
John Fox,1884.00,employer_provided_vehicle,Code1
Tony Pony,553.05,restricted_stock_vesting,Code2
Anna Good,1010.03,housing_allowance,"Test, Payment, Comma"
Anton Anon,1000,moving_expenses,222
```

## Example output
```text
Start request, id: 2020-11-14_18:34:04_6F80
INFO: Renew session
INFO: Update csrf token
INFO: Authenticate user
INFO: Bypass otp

Persons found: 101

Supported payment dates:
weekly
  2020-11-20, November 20th
  2020-11-27, November 27th
  2020-12-04, December 4th
biweekly
  2020-11-27, November 27th
  2020-12-11, December 11th
  2020-12-24, December 24th
semimonthly
  2020-11-30, November 30th
  2020-12-15, December 15th
  2020-12-31, December 31st

Supported payment types:
moving_expenses — Moving expenses
...

Parse CSV file
ERROR: Can't find employee: {'name': 'John Fox', 'amount': '84.00', 'type': 'some_type', 'note': 'Code1'}

Payments to create:
name                 pay_date          amount    subtype                note
Tony Pony            2020-11-30       3443.00    moving_expenses        2020-11-14_16:39:49_FD9F Code1
Anna Good            2020-11-27        553.05    moving_expenses        2020-11-14_16:39:49_FD9F Code2
```