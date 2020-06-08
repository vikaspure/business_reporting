import dateutil
import datetime

from reportGenerators.JiraFetcher import JIRA_Fetcher
from reportGenerators.CircleCI_Fetcher import CircleCI_Fetcher


project_name = 'OWA'

def generate_all_reporting_data_for_specific_week(target_versions: list, start_date: datetime, end_date: datetime):
    j1 = JIRA_Fetcher()
    c4 = CircleCI_Fetcher()

    report_object = j1.get_a_list_of_DONE_tickets_within_a_period(start_date, end_date, project_name,
                                                                         target_versions)
    j1.create_data_as_csv_for_DONE_tickets(report_object, True)

    for version in target_versions:
        report_object = j1.get_breakdown_of_tickets_with_hours_booked(start_date, end_date, project_name,
                                                                             version)
        j1.create_data_as_csv_for_logged_work_for(report_object, True)

    config = c4.get_basic_configuration_file()
    config["start_date_as_str"] = start_date.strftime("%Y/%m/%d")
    config["end_date_as_str"] = end_date.strftime("%Y/%m/%d")
    report_object = c4.check_several_branches(config)

    c4.show(report_object)
    c4.create_reporting_file_for_a_period(report_object)

def run_week_23():
    target_versions = ["1.0.0", "1.1.0", "1.2.0"]
    start_date = datetime.datetime(2020, 6, 1)
    end_date = datetime.datetime(2020, 6, 5, 23, 59, 59)
    generate_all_reporting_data_for_specific_week(target_versions, start_date, end_date)

if __name__ == "__main__":
    run_week_23()