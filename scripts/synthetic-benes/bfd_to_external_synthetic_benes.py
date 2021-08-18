import csv
import datetime
import random
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--bfd", "-bi", help="The name of the bfd input csv file", type=str)
parser.add_argument(
    "--bedap", "-bo", help="The name of the bedap output csv file", type=str
)
parser.add_argument(
    "--sls", "-so", help="The name of the sls output csv file", type=str
)
parser.add_argument(
    "--benecount",
    "-bc",
    help="The number of synthetic benes loaded in sls (important for creating username/password)",
    type=int,
)

args = parser.parse_args()

if not args.benecount:
    raise Exception(
        "benecount is required, without it the correct sls username/passwords cannot be created"
    )


INPUT_FILE_NAME = args.bfd if args.bfd else "bfd_sample_benes.csv"
BEDAP_OUTPUT_FILE_NAME = args.bedap if args.bedap else "bedap_synthetic_benes.csv"
SLS_OUTPUT_FILE_NAME = args.sls if args.sls else "sls_synthetic_benes.csv"
INITIAL_SYNTHETIC_BENE_COUNT = args.benecount

DEFAULT_EMAIL_SUPPRESSED = "FALSE"
DEFAULT_MIDDLE_NAME = "Synthetic"
DEFAULT_EFFECTIVE_DATE_PART = "a"
DEFAULT_MAX_YEARS_AGO_FOR_EFFECTIVE_DATE = 30

BFD_DATE_FORMAT = "%d-%b-%Y"
SLS_DATE_FORMAT = "%Y-%m-%d"


def bfd_to_sls_date(bfd_date):
    datetime_object = datetime.datetime.strptime(bfd_date, BFD_DATE_FORMAT)
    return datetime_object.strftime(SLS_DATE_FORMAT)


def random_date():
    start_date = datetime.datetime.now() - datetime.timedelta(
        days=DEFAULT_MAX_YEARS_AGO_FOR_EFFECTIVE_DATE * 365
    )
    end_date = datetime.datetime.now()

    time_delta = end_date - start_date
    random_days = random.randrange(time_delta.days)
    return start_date + datetime.timedelta(days=random_days)


BEDAP_FIELD_MAPPING = {
    "BENE_CRNT_HIC_NUM": "hicn",
    "MBI_NUM": "mbi",
    "BENE_SRNM_NAME": "first_name",
    "BENE_GVN_NAME": "last_name",
    "BENE_ID": "beneficiary_key",
}

SLS_FIELD_MAPPING = {
    "MBI_NUM": "mbi",
    "BENE_GVN_NAME": "lastName",
    "BENE_BIRTH_DT": {"name": "dateOfBirth", "value": bfd_to_sls_date},
    "BENE_ZIP_CD": "zipCodeOrCity",
}

BEDAP_FIELDS = [
    "hicn",
    "mbi",
    "first_name",
    "last_name",
    "middle_name",
    "email_suppressed",
    "beneficiary_key",
]

SLS_FIELDS = [
    "mbi",
    "lastName",
    "dateOfBirth",
    "zipCodeOrCity",
    "effectiveDate",
    "effectiveDatePart",
    "username",
    "password",
    "challengeQuestionAndAnswers",
]


def convert_to_bedap_bene(bfd_bene):
    bedap_bene = {
        "email_suppressed": DEFAULT_EMAIL_SUPPRESSED,
        "middle_name": DEFAULT_MIDDLE_NAME,
    }

    for key in BEDAP_FIELD_MAPPING:
        bedap_bene[BEDAP_FIELD_MAPPING[key]] = bfd_bene[key]

    return bedap_bene


def convert_to_sls_bene(bfd_bene, bene_count):
    sls_bene = {
        "challengeQuestionAndAnswers": [
            {
                "question": "What is the nick name of your grandmother?",
                "answer": DEFAULT_MIDDLE_NAME,
            }
        ],
        "username": "BBUser" + bene_count,
        "password": "PW" + bene_count + "!",
        "effectiveDate": random_date().strftime(SLS_DATE_FORMAT),
        "effectiveDatePart": DEFAULT_EFFECTIVE_DATE_PART,
    }

    for key in SLS_FIELD_MAPPING:
        if isinstance(SLS_FIELD_MAPPING[key], str):
            sls_bene[SLS_FIELD_MAPPING[key]] = bfd_bene[key]
        else:
            sls_bene[SLS_FIELD_MAPPING[key]["name"]] = SLS_FIELD_MAPPING[key]["value"](
                bfd_bene[key]
            )

    return sls_bene


with open(INPUT_FILE_NAME, newline="") as input_csvfile:
    reader = csv.DictReader(input_csvfile, delimiter="|")

    with open(BEDAP_OUTPUT_FILE_NAME, "w+", newline="") as bedap_output_csvfile:
        bedap_writer = csv.DictWriter(bedap_output_csvfile, fieldnames=BEDAP_FIELDS)

        with open(SLS_OUTPUT_FILE_NAME, "w+", newline="") as sls_output_csvfile:
            sls_writer = csv.DictWriter(sls_output_csvfile, fieldnames=SLS_FIELDS)

            bedap_writer.writeheader()
            sls_writer.writeheader()

            new_bene_count = INITIAL_SYNTHETIC_BENE_COUNT

            for row in reader:
                bedap_bene = convert_to_bedap_bene(row)
                sls_bene = convert_to_sls_bene(row, str(new_bene_count))
                print(bedap_bene)
                print(sls_bene)
                bedap_writer.writerow(bedap_bene)
                sls_writer.writerow(sls_bene)
                new_bene_count += 1
