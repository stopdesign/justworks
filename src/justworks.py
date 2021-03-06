import re
import sys
import json
import pyotp
import requests
from datetime import datetime, timezone
import logging


logger = logging.getLogger(__name__)


LOGIN_URL = "https://secure.justworks.com/login"
OTP_URL = "https://secure.justworks.com/tfa"
FRINGE_BENEFITS_URL = "https://secure.justworks.com/fringe_benefits/submit"
FORM_URL = "https://secure.justworks.com/fringe_benefits/form"
BONUS_URL = "https://secure.justworks.com/masspay/BonusPayment"


class API:

    session_max_age = 300

    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/85.0.4183.121 Safari/537.36",
    }

    rx_hydration_tmpl = r'hydration\-key="%s" type="application/json">([^<]+)</'

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.s = requests.Session()
        self.s.headers = self.headers
        self.session_updated_at = datetime.min

        self.employees = None
        self.payment_dates = None
        self.fringe_benefits_subtypes = None

    def parse_hydration_data(self, text, key):
        rx = re.compile(self.rx_hydration_tmpl % key)
        mtc = rx.search(text)
        return json.loads(mtc.group(1))

    def poke_session(self):
        session_age = datetime.now() - self.session_updated_at
        if session_age.total_seconds() > self.session_max_age:
            self.renew_session()
        else:
            logger.info("Use old session")

    def renew_session(self):
        logger.info("Renew session")
        self.update_csrf_token()
        self.authenticate()
        self.bypass_otp()
        self.session_updated_at = datetime.now()

    def authenticate(self):
        logger.info("Authenticate user")
        data = {
            "username": self.username,
            "password": self.password,
        }
        response = self.s.post(LOGIN_URL, data=data)
        if "error" in response.text or response.status_code != 200:
            logger.error("Can't authenticate user: %s" % response.text)
            sys.exit()

    def bypass_otp(self):
        logger.info("Bypass otp")
        response = self.s.get(OTP_URL, allow_redirects=False)
        tfa_info = self.parse_hydration_data(response.text, "tfaInfo")
        otp_key = tfa_info.get("key")
        auth_code = pyotp.TOTP(otp_key).now()
        data = {
            "method": "app",
            "auth_code": auth_code,
            "key": otp_key,
            "remember_this_device": "false",
        }
        response = self.s.post(OTP_URL, data=data)
        if "error" in response.text or response.status_code != 200:
            logger.error("Can't bypass otp: %s" % response.text)
            sys.exit()

    def update_csrf_token(self):
        logger.info("Update csrf token")
        response = self.s.get(LOGIN_URL, allow_redirects=True)
        csrf_token = self.parse_hydration_data(response.text, "form_authenticity_token")
        self.s.headers.update({"x-csrf-token": csrf_token})

    def get_constants(self):
        self.poke_session()
        response = self.s.get(FORM_URL, allow_redirects=False)
        if response.status_code != 200:
            logger.error("Can't get constants: %s" % response.text)
            sys.exit()
        self.employees = self.parse_hydration_data(response.text, "members")
        self.payment_dates = self.parse_hydration_data(
            response.text, "upcomingPayDates"
        )
        self.fringe_benefits_subtypes = self.parse_hydration_data(
            response.text, "fringeBenefitsSubtypes"
        )
        return self.employees, self.payment_dates, self.fringe_benefits_subtypes

    def create_payments(self, payments):
        self.poke_session()
        self.update_csrf_token()

        formated_payments = []

        for payment in payments:
            formated_payments.append(
                {
                    "member_uuid": payment["member_uuid"],
                    "pay_date": payment["pay_date"],
                    "amount": "{:.2f}".format(payment["amount"]),
                    "subtype": payment["subtype"],
                    "note": payment["note"],
                }
            )

        payments_data = {"payments": formated_payments}

        # print(json.dumps(payments_data, indent=2, ensure_ascii=False))

        response = self.s.post(FRINGE_BENEFITS_URL, json=payments_data)
        if response.status_code == 200:
            return None
        else:
            return response

    def create_bonus_payments(self, payments, pay_date, note):
        self.poke_session()
        self.update_csrf_token()

        allocations = {}
        for payment in payments:
            allocations[payment["member_uuid"]] = {
                "amount": int(round(payment["amount"] * 100))
            }

        payments_data = {
            "formData": {
                "pay_date": pay_date.replace(tzinfo=timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "eft": "true",
                "net_pay": "false",
                "tax_method": "flat",
                "deductions_setting": "only401k",
                "notes": note,
                "work_start_date": "2021-01-01T05:00:00.000Z",
                "work_end_date": "2021-03-31T04:00:00.000Z",
            },
            "allocations": allocations,
        }
        print(json.dumps(payments_data, indent=2, ensure_ascii=False))

        response = self.s.post(BONUS_URL, json=payments_data)
        if response.status_code == 201:
            return None
        else:
            return response

    def get_user_payments(self, user_uuid, user_name):
        self.poke_session()
        url = "https://secure.justworks.com/payments/%s/one_time_payments" % user_uuid

        rx_payment = re.compile(
            r'<a href="/pay/view/([-a-f0-9]+)">([^<]+)</a>\s*'
            r"</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*<td>\s*<a"
        )

        response = self.s.get(url)
        mtcs = rx_payment.findall(response.text)

        return [
            {
                "name": user_name,
                "pay_uuid": mtc[0],
                "pay_date": mtc[1],
                "amount": mtc[2],
                "type": mtc[3],
            }
            for mtc in mtcs
        ]
