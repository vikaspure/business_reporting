import dateutil
import datetime
import json

from reportGenerators.JiraFetcher import JIRA_Fetcher
from reportGenerators.CircleCI_Fetcher import CircleCI_Fetcher
from reportGenerators.Sonarcloud_Fetcher import generate_a_report_file_for_code_coverage_per_repo, generate_coverage_for_all_repos


project_name = 'OWA'

def generate_all_reporting_data_for_specific_week(target_versions: list, start_date: datetime, end_date: datetime):
    j1 = JIRA_Fetcher()
    c4 = CircleCI_Fetcher()

    report_object = j1.get_a_list_of_DONE_tickets_within_a_period(start_date, end_date, project_name,
                                                                         target_versions)
    j1.create_data_as_csv_for_DONE_tickets(report_object, True)

    for version in target_versions:
        report_object = j1.get_breakdown_of_tickets_with_hours_booked2(start_date, end_date, project_name,
                                                                             version)
        j1.create_data_as_csv_for_logged_work_for2(report_object, True)

    config = c4.get_basic_configuration_file()
    config["start_date_as_str"] = start_date.strftime("%Y/%m/%d")
    config["end_date_as_str"] = end_date.strftime("%Y/%m/%d")
    report_object = c4.check_several_branches(config)

    c4.show(report_object)
    c4.create_reporting_file_for_a_period(report_object)

    all_repos = {
        # 'pure-escapes_booking-manager-service': 0,
        'pure-escapes_pdf-service': 0,
        'pure-escapes_events-service': 0,
        'pure-escapes_webapp-admin': 0,
        'pure-escapes_webapp-admin-api': 0,
        'pure-escapes_webapp-backend': 0,
        'pure-escapes_webapp-client-api': 0,
        'pure-escapes_webapp-frontend': 0
    }
    report_object = generate_coverage_for_all_repos(all_repos)
    generate_a_report_file_for_code_coverage_per_repo(report_object, start_date)



def run_week_23():
    target_versions = ["1.0.0", "1.1.0", "1.2.0"]
    start_date = datetime.datetime(2020, 6, 1)
    end_date = datetime.datetime(2020, 6, 5, 23, 59, 59)
    generate_all_reporting_data_for_specific_week(target_versions, start_date, end_date)


def run_week_24():
    # last time of v1 for time tracking
    target_versions = ["1.0.0", "1.1.0", "1.2.0"]
    start_date = datetime.datetime(2020, 6, 8, 0, 0, 1)
    end_date = datetime.datetime(2020, 6, 14, 23, 59, 59)
    generate_all_reporting_data_for_specific_week(target_versions, start_date, end_date)

def run_week_25():
    #introduced v2 for time tracking
    target_versions = ["1.1.0", "1.2.0"]
    start_date = datetime.datetime(2020, 6, 15, 0, 0, 1)
    end_date = datetime.datetime(2020, 6, 19, 23, 59, 59)
    generate_all_reporting_data_for_specific_week(target_versions, start_date, end_date)

def run_week_26():
    target_versions = ["1.0.0", "1.1.0", "1.2.0"]
    start_date = datetime.datetime(2020, 6, 22, 0, 0, 1)
    end_date = datetime.datetime(2020, 6, 26, 23, 59, 59)
    generate_all_reporting_data_for_specific_week(target_versions, start_date, end_date)

def run_week_27():
    target_versions = ["1.0.0", "1.1.0", "1.2.0"]
    start_date = datetime.datetime(2020, 6, 29, 0, 0, 1)
    end_date = datetime.datetime(2020, 7, 3, 23, 59, 59)
    generate_all_reporting_data_for_specific_week(target_versions, start_date, end_date)

def lambda_handler(event, context):
    print(event)
    target_versions = ["1.0.0", "1.1.0", "1.2.0"]
    try:
        timing = event.loads(event)
        start_day = timing["start_day"]
        end_day = timing["end_day"]
        end_date = datetime.datetime.now().replace(day=end_day, hour=23, minute=59, second=59)
        start_date = datetime.datetime.now().replace(day=start_day,hour=0, minute=0, second=1)
    except Exception as e:
        end_date = datetime.datetime.now().replace(hour=23, minute=59, second=59)
        start_date = datetime.datetime.now().replace(day=end_date.day-4,hour=0, minute=0, second=1)
    generate_all_reporting_data_for_specific_week(target_versions, start_date, end_date)

if __name__ == "__main__":
    #run_week_27()
    lambda_handler("", "")