#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (C) Pure Escapes 2020 - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential

Written by Christos Tsotskas <info@pure-escapes.com>, April 2020

"""
from jira import JIRA, Issue
import re
import requests
import json
import os
import datetime
import dateutil.parser

from typing import Any, Dict, Generator, List, Tuple, Sequence

import requests
from requests.auth import HTTPBasicAuth
import json
import csv
import pytz





class JIRA_Fetcher:
    __jira_handler = None
    __project_name = None
    __version = None

    def __init__(self, project_name:str = None, version:str = None):
        '''

        :param project_name: as it appears on jira e.g., "OWA"
        :param version: as it appears on jira e.g., "1.1.0"
        '''
        self.utc = pytz.UTC


        options = {"server": "https://pureescapes.atlassian.net"}
        # print(os.getenv("PE_JIRA_USERNAME"), os.getenv("PE_JIRA_PASSWORD"))
        # jira = JIRA(options)
        self.__jira_handler = JIRA(options=options, basic_auth=(os.getenv("PE_JIRA_USERNAME"), os.getenv("PE_JIRA_BI_LISTENER")))
        if project_name is not None:
            self.__project_name = project_name

        if version is not None:
            self.__version = version

        self.__where = {'in_progress_on_the_board':'Blocked, "Code Review", "In Development", "Preparing Tests", QA, UAT',
                        'board': 'Blocked, "Code Review", "In Development", "Preparing Tests", QA, "Selected for Development", UAT',
                        'backlog': 'Backlog',
                        'full_board': 'Blocked, "Code Review", "In Development", "Preparing Tests", QA, "Selected for Development", UAT, Done',
                        }

        self.__types_of_tickets= { 'stories_and_bugs':'(Bug,Story)',
                                   'all_possible':'(Bug,Story,Task, Sub-task)',
                                   'all_possible_and_epic': '(Bug,Story,Task, Sub-task, Epic)'

        }

    def get_now_as_a_string(self):
        now_time_object = datetime.datetime.now()
        return now_time_object.strftime("%Y%m%d_%H%M")


    def get_number_of_bugs_in_backlog_for(self, project_name, version):
        bugs_found = 0

        template_of_JQL_command = "issuetype in (Bug) AND project = {} AND fixVersion = {} AND status = Backlog"

        JQL_command = template_of_JQL_command.format(project_name, version)

        results = self.__jira_handler.search_issues(JQL_command, startAt=0, maxResults=200)
        bugs_found = len(results)
        return bugs_found

    def get_size_of_backlog_for (self, project_name, version):
        tickets_found = 0

        template_of_JQL_command = "issuetype in (Bug, Story) AND project = {} AND fixVersion = {} AND status = Backlog"
        JQL_command = template_of_JQL_command.format(project_name, version)

        results = self.__jira_handler.search_issues(JQL_command, startAt=0, maxResults=200)

        tickets_found = len(results)
        return tickets_found

    def get_tickets_completed_within_period(self, project_name, start_date, end_date, version):
        tickets_found = 0

        template_of_JQL_command = 'project = "{}" AND issuetype in (Bug,Story) AND status changed TO Done AND updatedDate > "{} 00:00" AND updatedDate < "{} 00:00" AND fixVersion = {}'
        JQL_command = template_of_JQL_command.format(project_name, start_date, end_date, version)
        JQQ = 'project = "OWA" AND issuetype in (Bug,Story) AND status changed TO Done AND updatedDate > "2020/04/01 00:00" AND updatedDate < "2020/04/20 00:00" AND fixVersion = 1.0.0'
        results = self.__jira_handler.search_issues(JQL_command, startAt=0, maxResults=200)
        tickets_found = len(results)
        return tickets_found

    def get_stories_and_bugs_from_backlog(self):
        pass

    def get_stories_and_bugs_from_board_that_are_in_progress(self):
        pass

    def get_tickets_that_do_not_have_story_points_and(self):
        pass

    def check_target_issue(self,issue, target_ticket:str):
        '''
        helper function to see the contents of a ticket
        :param issue: jira object
        :param target_ticket: e.g. 'OWA-1315'
        :return:
        '''
        ticket_name = str(issue.key)

        if ticket_name == target_ticket:
            fmt = json.dumps(issue.raw, indent=2)
            print('raw issue fields', fmt)

    def get_complex_time_estimation(self, issue):

        not_having_time_estimation = (issue.fields.timeoriginalestimate in (None, 0) ) ^ \
                                     (issue.fields.timeestimate in (None, 0)) #^ \
                                     # (issue.raw.fields.aggregatetimeestimate in (0))

        return not_having_time_estimation

    def get_quality_from_the_main_board_for_a_specific_version(self, project_name: str = None, version: str = None):
        where_option = 'board'
        return self.get_quality_for_a_specific_version(where_option, project_name, version)

    def get_quality_from_backlog_for_a_specific_version(self, project_name: str = None, version: str = None):
        where_option = 'backlog'
        return self.get_quality_for_a_specific_version(where_option, project_name, version)

    def get_quality_of_multiple_versions(self, project_name: str, assessment_by_versions: dict):
        '''

        :param project_name: e.g. 'OWA'
        :param assessment_by_versions: e.g. {
                            "1.1.0":{},
                            "1.2.0":{},
                            "1.3.0":{},
                            "2.0.0":{}
                            }
        :return:
        '''
        for version in assessment_by_versions.keys():
            # print('checking version', version)
            report_object = self.get_quality_from_backlog_for_a_specific_version(
                project_name=project_name, version=version)

            print('version', version, ', failure rate:',report_object['calculations']['failure_rate']*100)
            assessment_by_versions[version] = report_object


    def get_quality_for_a_specific_version(self, where_option: str, project_name: str = None, version: str = None):
        if version is None:
            version = self.__version

        if project_name is None:
            project_name = self.__project_name


        output = {'timestamp_this_was_created':self.get_now_as_a_string()}
        output['version'] = version

        if where_option == 'board':
            output['where'] = 'Kanban Board'
        else:
            output['where'] = '(just the) Backlog'

        output['feature'] = []
        output['maintenance'] = []
        output['rework'] = []
        output['defect'] = []
        output['unclassified'] = []
        output['statistics'] = {"number_of_features": 0,
                                "number_of_maintenance": 0,
                                "number_of_rework": 0,
                                "number_of_calculations": 0,
                                "number_of_unclassified": 0}
        output['calculations'] = {"value_supply": 0,
                                  "failure_supply": 0,
                                  "total_number_of_items": 0,
                                  "failure_rate": 0}

        columns_to_query = self.__where[where_option]

        query = 'issuetype in (Bug, Story) AND project = '+project_name+' AND fixVersion = '+version+' AND resolution = Unresolved AND status in ('+columns_to_query+') ORDER BY priority DESC, updated DESC'
        results = self.__jira_handler.search_issues(query, startAt=0, maxResults=200)



        for issue in results:

            obj = {}
            ticket_name = str(issue.key)
            status = str(issue.fields.status)
            member_of_team = str(issue.fields.assignee)
            jira_issue_type = str(issue.fields.issuetype).lower()
            item_type = str(issue.fields.customfield_10037).lower()

            if item_type == 'feature':
                output['feature'].append(ticket_name)
            if item_type == 'maintenance':
                output['maintenance'].append(ticket_name)
            if item_type == 'rework':
                output['rework'].append(ticket_name)
            if item_type == 'defect':
                output['defect'].append(ticket_name)
            if item_type not in ('feature', 'maintenance', 'rework', 'defect'):
                output['unclassified'].append(ticket_name)



        number_of_features = len(output['feature'])
        number_of_maintenance = len(output['maintenance'])
        number_of_rework = len(output['rework'])
        number_of_defect = len(output['defect'])
        number_of_unclassified = len(output['unclassified'])
        output['statistics']["number_of_features"] = number_of_features
        output['statistics']["number_of_maintenance"] = number_of_maintenance
        output['statistics']["number_of_rework"] = number_of_rework
        output['statistics']["number_of_calculations"] = number_of_defect
        output['statistics']["number_of_unclassified"] = number_of_unclassified

        value_supply = number_of_features + number_of_maintenance
        failure_supply = number_of_rework + number_of_defect
        total_number_of_items = value_supply + failure_supply

        if total_number_of_items == 0:
            output['calculations']["value_supply"] = 0
            output['calculations']["failure_supply"] = 0
            output['calculations']["total_number_of_items"] = total_number_of_items
            output['calculations']["failure_rate"] = 1

        else:
            failure_rate = 1.0 * failure_supply / total_number_of_items
            output['calculations']["value_supply"] = value_supply
            output['calculations']["failure_supply"] = failure_supply
            output['calculations']["total_number_of_items"] = total_number_of_items
            output['calculations']["failure_rate"] = failure_rate






        return output

    def get_stories_and_bugs_tickets_that_are_in_progress_for_a_specific_version(self, project_name: str = None, version: str = None):
        if version is None:
            version = self.__version

        if project_name is None:
            project_name = self.__project_name


        output = {'timestamp_this_was_created':self.get_now_as_a_string()}
        output['version'] = version
        output['where'] = 'Kanban Board'


        query = 'issuetype in (Bug, Story) AND project = '+project_name+' AND fixVersion = '+version+' AND resolution = Unresolved AND status in (Blocked, "Code Review", "In Development", "Preparing Tests", "Selected for Development") ORDER BY priority DESC, updated DESC'
        results = self.__jira_handler.search_issues(query, startAt=0, maxResults=200)



        for issue in results:

            obj = {}
            ticket_name = str(issue.key)
            status = str(issue.fields.status)
            member_of_team = str(issue.fields.assignee)
            issue_type = str(issue.fields.issuetype).lower()


            not_having_time_estimation = (issue.fields.timeestimate in (None, 0))
            being_a_story_without_story_points = (issue.fields.customfield_10026 in (None,0) ) and (issue_type == 'story')


            if not_having_time_estimation == True :
                if member_of_team not in output.keys():
                    output[member_of_team] = {}
                if ticket_name not in output[member_of_team].keys():
                    output[member_of_team][ticket_name] = {}
                if 'column' not in output[member_of_team][ticket_name].keys():
                    output[member_of_team][ticket_name] = {'column': status}

                # print(issue.key, issue_type, 'no time estimate from', member_of_team)
                output[member_of_team][ticket_name] = {'remaining_time':'<---please add remaining time'}


            if being_a_story_without_story_points == True:
                if member_of_team not in output.keys():
                    output[member_of_team] = {}
                if ticket_name not in output[member_of_team].keys():
                    output[member_of_team][ticket_name] = {}
                if 'column' not in output[member_of_team][ticket_name].keys():
                    output[member_of_team][ticket_name] = {'column': status}
                # print(issue.key, issue_type,  'no story points from', member_of_team)
                output[member_of_team][ticket_name] = {'story points': '<---please add story points'}

        return output


    def print_short_message_for_update(self, input: dict):
        print('Updates required for ', input["where"], ', generated at',input["timestamp_this_was_created"], ":")



        counter=0
        for item in input.keys():
            if item not in ("timestamp_this_was_created", "version", "where"):
                print(item)
                for issue_name, ticket in input[item].items():
                    print("\t", issue_name, ticket)
                    counter += 1
        if counter == 0:
            print("\tAll good :)")

    def print_short_message_for_quality_assessment(self, input: dict, toggle_for_PS = True):
        print('Agile Quality assessment (via Jira) of ', input["where"], ' for version ', input["version"], ', generated at',input["timestamp_this_was_created"], ":")
        total_number_of_items = input['calculations']['total_number_of_items']
        number_of_unclassified_items = input['statistics']['number_of_unclassified']
        unclassified_tickets = input['unclassified']
        failure_rate = input['calculations']['failure_rate']


        print('total tickets:', str(total_number_of_items))
        if number_of_unclassified_items != 0:
            unclassified_tickets.sort()
            print('\tBUT, ', str(number_of_unclassified_items), 'more tickets are unclassified! (i.e., ', ", ".join(unclassified_tickets), ')')
        print("with failure_rate:", str(round(failure_rate*100, 2)), "% (ideally, as low as possible)")

        if toggle_for_PS == True :
            print("\n")
            print('\tPS1: more info about "how to read this?" at https://pureescapes.atlassian.net/wiki/spaces/PEOWA/pages/309493777/Refining+the+Agile+process#Assessing-versions-%26-backlog')
            print('\tPS2: the unclassified tickets are not considered in the calculations')
            print('\tPS3: how to log time -> https://support.atlassian.com/jira-software-cloud/docs/log-time-on-an-issue')


    def get_worklog_for_ticket(self, issue):
        '''
        INCOMPLETE, or at least not working. empty objects are generated. the issue is related to IDs
        from https://developer.atlassian.com/cloud/jira/platform/rest/v3/?_ga=2.226989019.757809754.1589814022-836559980.1589401490#api-rest-api-3-worklog-list-post
        :param issue:
        :return:
        '''
        ticket = issue.key
        # ID = 11810
        ID = issue.id

        import requests
        from requests.auth import HTTPBasicAuth
        import json

        # options["server"]
        base_url = "https://pureescapes.atlassian.net"
        url = base_url+"/rest/api/3/worklog/list"


        auth = HTTPBasicAuth(os.getenv("PE_JIRA_USERNAME"), os.getenv("PE_JIRA_BI_LISTENER"))

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        payload = json.dumps({
            "ids": [
                ID
            ]
        })

        response = requests.request(
            "POST",
            url,
            data=payload,
            headers=headers,
            auth=auth
        )

        print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))

    def get_list_of_all_members_that_participated_in_the_work_of_selected_tickets(self, selected_tickets, start_date, end_date):
        all_members_of_the_team = []
        for issue in selected_tickets:
            ticket_name = str(issue.key)
            break_down_of_ticket_per_member = self.get_time_tracking_of_a_ticket_per_user_for_a_specific_period(ticket_name, start_date, end_date)

            for member in break_down_of_ticket_per_member['members'].keys():
                if member not in all_members_of_the_team:
                    all_members_of_the_team.append(member)

        return all_members_of_the_team


    def get_breakdown_of_tickets_with_hours_booked(self,start_date: datetime, end_date: datetime, project_name: str, version: str):
        '''
        some approach:

        A.Use GET /rest/api/3/worklog/updated to get the IDs of worklogs in the time period. The timestamp refers to the time the worklog has been created/updated, not the date to which the entry refers. To make sure I have everything, I just go later in the past. The call is paginated, and the response is small, so listing too much is not a big problem. You just need to remove the worklogs you don't want afterwards
        B.Use POST /rest/api/3/worklog/list to get the actual worklogs. The payload is the list of IDs to you got in the first step. This is limited to 1000 entries, but you can call it multiple times
        C.Bonus - If you need the issues for the retrieved worklogs, use POST /rest/api/3/search. You need to use POST, because the query will be very long and does not fit in the URL. You can build the query from the issue ids in the worklogs retrieved in step 2 (`id in (12345, 456789, ...)`



        :param: start (inclusive)
        :return: end  (inclusive)
        '''

        start_date_as_str = start_date.strftime("%Y/%m/%d")
        end_date_as_str = end_date.strftime("%Y/%m/%d")
        output = {"timestamp_this_was_created":self.get_now_as_a_string(),
                  "version":str(version),
                  "where":self.__where['full_board'],
                  "start_date":start_date.strftime("%Y/%m/%d"), #       .strftime("%d/%m/%Y")
                  "end_date":end_date.strftime("%Y/%m/%d"),
                  "members":{},
                  "tickets_considered":self.__types_of_tickets['all_possible']
                  }
        template_of_JQL_command = 'issuetype in {}  AND project = "{}" AND fixVersion = "{}"  AND status in ({}) AND worklogDate >= "{}"    AND worklogDate <= "{}"  order by lastViewed DESC'
        JQL_command = template_of_JQL_command.format(output["tickets_considered"],
                                                     project_name,
                                                     version,
                                                     output['where'],
                                                     start_date_as_str,
                                                     end_date_as_str)




        selected_tickets = self.__jira_handler.search_issues(JQL_command, startAt=0, maxResults=200)


        all_members_of_the_team = self.get_list_of_all_members_that_participated_in_the_work_of_selected_tickets(selected_tickets, start_date, end_date)


        for member in all_members_of_the_team:
            output["members"].update({member: {}})


        for issue in selected_tickets:


            ticket_name = str(issue.key)
            # status = str(issue.fields.status)
            # member_of_team = str(issue.fields.assignee)
            # jira_issue_type = str(issue.fields.issuetype).lower()
            # item_type = str(issue.fields.customfield_10037).lower()

            break_down_of_ticket_per_member = self.get_time_tracking_of_a_ticket_per_user_for_a_specific_period(ticket_name, start_date, end_date)

            for member in break_down_of_ticket_per_member['members'].keys():
                hours_booked_on_this_ticket = 0
                if ticket_name not in output["members"][member].keys():
                    output["members"][member].update({ticket_name: {'total_hours_booked': hours_booked_on_this_ticket}})


            for member,booked_time_in_seconds in break_down_of_ticket_per_member['members'].items():
                hours_booked_on_this_ticket = booked_time_in_seconds/3600
                temp_data = {ticket_name: {'total_hours_booked': hours_booked_on_this_ticket}}

                output["members"][member][ticket_name]['total_hours_booked'] += hours_booked_on_this_ticket

        return output

    def get_breakdown_of_tickets_with_hours_booked2(self,start_date: datetime, end_date: datetime, project_name: str, version: str):
        '''
        some approach:

        A.Use GET /rest/api/3/worklog/updated to get the IDs of worklogs in the time period. The timestamp refers to the time the worklog has been created/updated, not the date to which the entry refers. To make sure I have everything, I just go later in the past. The call is paginated, and the response is small, so listing too much is not a big problem. You just need to remove the worklogs you don't want afterwards
        B.Use POST /rest/api/3/worklog/list to get the actual worklogs. The payload is the list of IDs to you got in the first step. This is limited to 1000 entries, but you can call it multiple times
        C.Bonus - If you need the issues for the retrieved worklogs, use POST /rest/api/3/search. You need to use POST, because the query will be very long and does not fit in the URL. You can build the query from the issue ids in the worklogs retrieved in step 2 (`id in (12345, 456789, ...)`



        :param: start (inclusive)
        :return: end  (inclusive)
        '''

        start_date_as_str = start_date.strftime("%Y/%m/%d")
        end_date_as_str = end_date.strftime("%Y/%m/%d")
        output = {"timestamp_this_was_created":self.get_now_as_a_string(),
                  "version":str(version),
                  "where":self.__where['full_board'],
                  "start_date":start_date.strftime("%Y/%m/%d"),
                  "end_date":end_date.strftime("%Y/%m/%d"),
                  "members":{}, # <---------- to delete
                  "tickets_considered":self.__types_of_tickets['all_possible_and_epic'],
                  "worklog_items":[]
                  }
        template_of_JQL_command = 'issuetype in {}  AND project = "{}" AND fixVersion = "{}"  AND status in ({}) AND worklogDate >= "{}"    AND worklogDate <= "{}"  order by lastViewed DESC'
        JQL_command = template_of_JQL_command.format(output["tickets_considered"],
                                                     project_name,
                                                     version,
                                                     output['where'],
                                                     start_date_as_str,
                                                     end_date_as_str)




        selected_tickets = self.__jira_handler.search_issues(JQL_command, startAt=0, maxResults=200)


        all_members_of_the_team = self.get_list_of_all_members_that_participated_in_the_work_of_selected_tickets(selected_tickets, start_date, end_date)


        for member in all_members_of_the_team:
            output["members"].update({member: {}})

        all_items = []
        for issue in selected_tickets:
            ticket_name = str(issue.key)

            break_down_of_a_single_ticket = self.get_time_tracking_of_a_ticket_per_user_for_a_specific_period2(ticket_name, start_date, end_date)

            for part_of_a_ticket in break_down_of_a_single_ticket:
                work_log_item = {}

                work_log_item["when"] = part_of_a_ticket["when"]
                work_log_item["booked_hours"] = part_of_a_ticket["booked_hours"]
                work_log_item["contribution_type"] = part_of_a_ticket["contribution_type"]
                work_log_item["member_of_team"] = part_of_a_ticket["member_of_team"]






                # for member in break_down_of_ticket_per_member['members'].keys():
                #     hours_booked_on_this_ticket = 0
                #     if ticket_name not in output["members"][member].keys():
                #         output["members"][member].update({ticket_name: {'total_hours_booked': hours_booked_on_this_ticket}})
                #
                #
                # for member,booked_time_in_seconds in break_down_of_ticket_per_member['members'].items():
                #     hours_booked_on_this_ticket = booked_time_in_seconds/3600
                #     temp_data = {ticket_name: {'total_hours_booked': hours_booked_on_this_ticket}}
                #
                #     output["members"][member][ticket_name]['total_hours_booked'] += hours_booked_on_this_ticket

                work_log_item["version"] = version
                work_log_item["ticket"] = ticket_name

                all_items.append(work_log_item)

        output["worklog_items"] = all_items

        return output

    def calculate_the_cycle_time_of_an_issue_from_its_activity(self, issue_name: str):
        '''
        go through the history of a ticket, find the time it was entered in column 'In Development' from the column 'Selected for Development'
        and then calculate the cycle time until the time it was Done
        :param issue_name:
        :return:
        '''

        base_url = "https://pureescapes.atlassian.net"
        url = base_url + "/rest/api/3/issue/"+issue_name+"/changelog"

        auth = HTTPBasicAuth(os.getenv("PE_JIRA_USERNAME"), os.getenv("PE_JIRA_BI_LISTENER"))

        headers = {
            "Accept": "application/json"
        }

        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth
        )
        structured_output = json.loads(response.text)

        #find the
        index_of_of_event_that_development_started = 0
        index = 0
        for event in structured_output["values"]:
            if "toString" in event['items'][0]:
                if event['items'][0]["toString"] == "Selected for Development":
                    index_of_of_event_that_development_started = index

            index += 1

        datestamp_the_ticket_was_selected_for_development_as_str = structured_output["values"][index_of_of_event_that_development_started]["created"]

        datestamp_the_ticket_was_selected_for_development_as_object = dateutil.parser.parse(datestamp_the_ticket_was_selected_for_development_as_str)

        # print(json.dumps(structured_output, sort_keys=True, indent=4, separators=(",", ": ")))

        return datestamp_the_ticket_was_selected_for_development_as_object

    def get_a_list_of_DONE_tickets_within_a_period(self,start_date: datetime, end_date: datetime, project_name: str, versions: list):
        '''

        alternatively, the JQL could had been something like: project = XYZ AND issuetype = bug AND resolved >= 2015-08-01 AND resolved <= 2016-09-15

        :param start_date:
        :param end_date:
        :param project_name:
        :param versions: list of strings with the versions e.g., ['1.2.0', '1.3.4', ....]
        :return:
        '''


        start_date_as_str = start_date.strftime("%Y/%m/%d")
        end_date_as_str = end_date.strftime("%Y/%m/%d")
        output = {"timestamp_this_was_created":self.get_now_as_a_string(),
                  "versions_considered": ", ".join(map(lambda x: '"'+str(x)+'"', versions)),
                  "where":self.__where['full_board'],
                  "start_date":start_date.strftime("%Y/%m/%d"),
                  "end_date":end_date.strftime("%Y/%m/%d"),
                  "types_of_tickets_considered":self.__types_of_tickets['stories_and_bugs'],
                  "data":[]
                  }
        template_of_JQL_command = 'issuetype in ({})  AND project = "{}" AND fixVersion  in ({})  AND status changed to done DURING ("{} 00:00","{}")'
        JQL_command = template_of_JQL_command.format(output["types_of_tickets_considered"],
                                                     project_name,
                                                     output["versions_considered"],
                                                     start_date_as_str,
                                                     end_date_as_str)



        selected_tickets = self.__jira_handler.search_issues(JQL_command, startAt=0, maxResults=200)





        for issue in selected_tickets:
            entry = {}

            entry["ticket_name"] = str(issue.key)
            entry["version"] = str(issue.fields.fixVersions[0])

            creation_of_issue_as_str = str(issue.fields.created)
            entry["when_was_created"] = creation_of_issue_as_str
            creation_of_issue_as_object = dateutil.parser.parse(creation_of_issue_as_str)

            finished_datestamp_of_issues_as_str = str(issue.fields.resolutiondate)
            entry["when_was_done"] = finished_datestamp_of_issues_as_str
            finished_datestamp_of_issues_as_object = dateutil.parser.parse(finished_datestamp_of_issues_as_str)

            entry['issue_type'] = str(issue.fields.issuetype).lower()
            entry['item_type'] = str(issue.fields.customfield_10037)

            lead_time_in_days = (finished_datestamp_of_issues_as_object-creation_of_issue_as_object).days
            entry['lead_time(days)'] = lead_time_in_days

            datestamp_that_the_task_started = self.calculate_the_cycle_time_of_an_issue_from_its_activity(entry["ticket_name"])
            cycle_time = (finished_datestamp_of_issues_as_object-datestamp_that_the_task_started).days
            entry['cycle_time(days)'] = cycle_time


            if issue.fields.customfield_10026 is not None:
                points = float(issue.fields.customfield_10026)
            else:
                points = 0

            if entry['issue_type'] == 'story':

                entry["points"] = points
            else:
                entry["points"] = 0



            output['data'].append(entry)

        return output

    def get_a_list_of_tickets_whose_progress_has_exceeded_the_threshold_towards_completion(self,start_date: datetime, end_date: datetime, project_name: str, versions: list, threshold: float):
        '''

        alternatively, the JQL could had been something like: project = XYZ AND issuetype = bug AND resolved >= 2015-08-01 AND resolved <= 2016-09-15

        :param start_date:
        :param end_date:
        :param project_name:
        :param versions: list of strings with the versions e.g., ['1.2.0', '1.3.4', ....]
        :param threshold:  if the ratio of hours booked over originally estimated hours is higher than the threshold, then the corresponding tickets will be selected
        :return:
        '''


        start_date_as_str = start_date.strftime("%Y/%m/%d")
        end_date_as_str = end_date.strftime("%Y/%m/%d")
        output = {"timestamp_this_was_created": self.get_now_as_a_string(),
                  "versions_considered": ", ".join(map(lambda x: '"'+str(x)+'"', versions)),
                  "where": self.__where['in_progress_on_the_board'],
                  "start_date": start_date.strftime("%Y/%m/%d"),
                  "end_date": end_date.strftime("%Y/%m/%d"),
                  "types_of_tickets_considered": self.__types_of_tickets['stories_and_bugs'],
                  "data": []
                  }
        template_of_JQL_command = 'issuetype in ({})  AND project = "{}" AND fixVersion  in ({}) AND status in ({}) AND updated >= "{}" AND updated <= "{}" '
        JQL_command = template_of_JQL_command.format(output["types_of_tickets_considered"],
                                                     project_name,
                                                     output["versions_considered"],
                                                     output["where"],
                                                     start_date_as_str,
                                                     end_date_as_str)



        selected_tickets = self.__jira_handler.search_issues(JQL_command, startAt=0, maxResults=200)




        temp_data = []
        for issue in selected_tickets:

            booked_over_estimated = issue.fields.workratio

            currently_booked_time = issue.fields.aggregatetimespent
            original_estimation = issue.fields.aggregatetimeestimate

            if issue.fields.aggregatetimeoriginalestimate == 0:
                print('warning! ', str(issue.key),' has zero estimation!')

            if (currently_booked_time is not None) and (original_estimation is not None):

                # check = currently_booked_time - threshold * original_estimation

                if (booked_over_estimated > 100*threshold) and (original_estimation > 0.0):

                    entry = {}
                    entry['week_commencing'] = start_date_as_str
                    entry["ticket_name"] = str(issue.key)
                    entry['booked_over_estimated'] = booked_over_estimated
                    entry['booked_hours'] = currently_booked_time / 3600
                    entry['originally_estimated_hours'] = original_estimation / 3600
                    entry["version"] = str(issue.fields.fixVersions[0])

                    entry['issue_type'] = str(issue.fields.issuetype).lower()
                    entry['item_type'] = str(issue.fields.customfield_10037)



                    temp_data.append(entry)

        sorted_data = sorted(temp_data, key=lambda x: x['booked_over_estimated'], reverse=True)
        output['data'] = sorted_data

        # output['data'] = temp_data

        # sorted(orders.items(), key=lambda x: x[1], reverse=True)

        return output

    def create_data_as_csv_for_overrun_tickets(self, input: dict):

        output_filename = '/tmp/' + 'Progress_of_tickets_from_'+input["start_date"].replace('/','_')+"_to_"+input["end_date"].replace('/','_')+'_created_at_'+input["timestamp_this_was_created"]+'.csv'

        with open(output_filename,'w') as csv_file:
            headers = list(input["data"][0].keys())
            writer = csv.DictWriter(csv_file, fieldnames=headers)

            writer.writeheader()

            for data_item in input["data"]:
                writer.writerow(data_item)

    def create_data_as_csv_for_DONE_tickets(self, input: dict, show_totals=False):

        output_filename = '/tmp/' + 'Agile_velocity_snapshot_of_DONE_tickets_from_'+input["start_date"].replace('/','_')+"_to_"+input["end_date"].replace('/','_')+'_created_at_'+input["timestamp_this_was_created"]+'.csv'

        with open(output_filename,'w') as csv_file:
            if len(input["data"]) == 0:
                print('No tickets finished between', input["start_date"], 'and', input["end_date"], 'for versions', input['versions_considered'])

            else:
                headers = list(input["data"][0].keys())
                # headers = ['ticket_name', 'version', 'when_was_created', 'when_was_done', 'points']
                writer = csv.DictWriter(csv_file, fieldnames=headers)

                writer.writeheader()

                for data_item in input["data"]:
                    writer.writerow(data_item)


    def show_message_for_logged_work(self, input: dict, show_totals=False):
        print('For version', input["version"],'between', input["start_date"], 'and', input["end_date"],'the following members of the team have logged their time against tickets ',input["tickets_considered"],':')
        print('by considering columns:', input["where"],
              ', generated at', input["timestamp_this_was_created"], ":")


        total_hours_booked = 0
        for member in input["members"].keys():
            print(member)
            for ticket in input["members"][member].keys():
                output_line=str(ticket)
                temp_hours_for_this_ticket = input["members"][member][ticket]['total_hours_booked']
                total_hours_booked += temp_hours_for_this_ticket
                if show_totals is True:
                    output_line += " {"+str(round(temp_hours_for_this_ticket,2))+" hours}"
                print("\t",output_line)


        if show_totals is True:
            print('Total:',round(total_hours_booked,2),'hours (=',round(total_hours_booked/8,2),'days, 8hr = 1day)')

        print("")

    def create_data_as_csv_for_logged_work_for(self, input: dict, show_totals=False):
        '''
        this is expected to be used within Google data studio or other analytics platform that utilises data
        :param input:
        :param show_totals:
        :return:
        '''
        print('For version', input["version"],'between', input["start_date"], 'and', input["end_date"],'the following members of the team have logged their time against tickets ',input["tickets_considered"],':')
        print('by considering columns:', input["where"],
              ', generated at', input["timestamp_this_was_created"], ":")

        output_filename = '/tmp/' + 'time_tracking_for_version_'+str(input["version"])+"_from_"+str(input["start_date"]).replace('/','_')+"_to_"+str(input["end_date"]).replace('/','_')+"_created_at_"+str(input["timestamp_this_was_created"])+".csv"

        with open(output_filename,'w') as csv_file:
            fieldnames = ['week_commencing', 'member', 'total_hours_booked', 'version','development_hours','support_hours']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()

            for member in input["members"].keys():
                print(member)
                total_hours_per_member = 0
                for ticket in input["members"][member].keys():
                    output_line = str(ticket)
                    temp_hours_for_this_ticket = input["members"][member][ticket]['total_hours_booked']

                    # if show_totals is True:
                    #     output_line += " {" + str(round(temp_hours_for_this_ticket, 2)) + " hours}"
                    # print("\t", output_line)
                    total_hours_per_member += temp_hours_for_this_ticket

                writer.writerow({'week_commencing': input["start_date"],
                                 'member': member,
                                 'total_hours_booked': total_hours_per_member,
                                 'version': str(input["version"]),
                                 'development_hours': 0,
                                 'support_hours': 0

                                 })



        total_hours_booked = 0
        for member in input["members"].keys():
            print(member)
            for ticket in input["members"][member].keys():
                output_line=str(ticket)
                temp_hours_for_this_ticket = input["members"][member][ticket]['total_hours_booked']
                total_hours_booked += temp_hours_for_this_ticket
                if show_totals is True:
                    output_line += " {"+str(round(temp_hours_for_this_ticket,2))+" hours}"
                print("\t",output_line)


        if show_totals is True:
            print('Total:',round(total_hours_booked,2),'hours (=',round(total_hours_booked/8,2),'days, 8hr = 1day)')

        print("")

    def create_data_as_csv_for_logged_work_for2(self, input: dict, show_totals=False):
        '''
        this is expected to be used within Google data studio or other analytics platform that utilises data
        :param input:
        :param show_totals:
        :return:
        '''
        print('For version', input["version"],'between', input["start_date"], 'and', input["end_date"],'the following members of the team have logged their time against tickets ',input["tickets_considered"],':')
        print('by considering columns:', input["where"],
              ', generated at', input["timestamp_this_was_created"], ":")

        output_filename = '/tmp/' + 'time_tracking_for_version_'+str(input["version"])+"_from_"+str(input["start_date"]).replace('/','_')+"_to_"+str(input["end_date"]).replace('/','_')+"_created_at_"+str(input["timestamp_this_was_created"])+".csv"

        team_total_hours = 0
        with open(output_filename,'w') as csv_file:
            fieldnames = ['week_commencing', 'member', 'total_hours_booked', 'version','development_hours','support_hours']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            aggreegation_per_member = {}
            for item in input['worklog_items']:
                ticket = item['ticket']
                member_of_team = item["member_of_team"]
                if member_of_team not in aggreegation_per_member.keys():
                    aggreegation_per_member[member_of_team] = {"development_hours": 0,
                                                               "support_hours": 0,
                                                               "tickets":{}}

                if ticket not in aggreegation_per_member[member_of_team]["tickets"].keys():
                    aggreegation_per_member[member_of_team]["tickets"][ticket] = 0

                aggreegation_per_member[member_of_team]["tickets"][ticket] += item['booked_hours']

                if item['contribution_type'] == "development":
                    aggreegation_per_member[member_of_team]["development_hours"] += item['booked_hours']
                else:
                    aggreegation_per_member[member_of_team]["support_hours"] += item['booked_hours']

            for member_of_team in aggreegation_per_member.keys():
                print(member_of_team)
                for ticket, hours in aggreegation_per_member[member_of_team]["tickets"].items():
                    print("\t", ticket, ":", hours, "hours")
                total_hours_per_member = aggreegation_per_member[member_of_team]["development_hours"] + aggreegation_per_member[member_of_team]["support_hours"]
                team_total_hours += total_hours_per_member
                print("\t total:",total_hours_per_member,'hours')
                writer.writerow({'week_commencing': input["start_date"],
                                 'member': member_of_team,
                                 'total_hours_booked': total_hours_per_member,
                                 'version': str(input["version"]),
                                 'development_hours': aggreegation_per_member[member_of_team]["development_hours"],
                                 'support_hours': aggreegation_per_member[member_of_team]["support_hours"]

                                 })

        filename_for_intermediate_table = '/tmp/' + 'intermediate_table_for_time_tracking_for_version_'+str(input["version"])+"_from_"+str(input["start_date"]).replace('/','_')+"_to_"+str(input["end_date"]).replace('/','_')+"_created_at_"+str(input["timestamp_this_was_created"])+".csv"
        with open(filename_for_intermediate_table,'w') as csv_file:
            if len(input['worklog_items']) == 0:
                print('Version',input['version'],'remained constant during this period')
            else:
                fieldnames = input['worklog_items'][0].keys()
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()

                for item in input['worklog_items']:
                    writer.writerow(item)

        print("Team total:", round(team_total_hours/8, 2),"days (8 hours = 1 day) = ", team_total_hours, "hours")
        print("")




    def get_author_of_ticket(self, ticket: str):

        base_url = "https://pureescapes.atlassian.net"
        url = base_url + "/rest/api/3/issue/" + ticket


        auth = HTTPBasicAuth(os.getenv("PE_JIRA_USERNAME"), os.getenv("PE_JIRA_BI_LISTENER"))

        headers = {
            "Accept": "application/json"
        }

        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth
        )



        structured_output = json.loads(response.text)

        # author_name = structured_output.fields.assignee.displayName #["attachment"]["displayName"]
        #todo: sometimes a ticket might not have an assignee!!! (so, it's unassigned, and this breaks the scripts).
        # which means that in the datamodel of jira `structured_output['fields']['assignee']['displayName'] is None`
        author_name = structured_output['fields']['assignee']['displayName']  # ["attachment"]["displayName"]

        return author_name

    def get_time_tracking_of_a_ticket_per_user_for_a_specific_period(self, ticket: str, start_date: datetime, end_date: datetime):
        #todo deprecate
        '''
        on jira's data model, each author object corresponds to a time booking, and the the field "started"
        represents when the time was spent.
        Eg. The expectation is that a user should book time for a specific week and on jira dialog the box 'Date Started' should point to the appropriate date of the week

        :param ticket:
        :return:
        '''
        time_tracking = {"timestamp_this_was_created":self.get_now_as_a_string(),
                         'comments':'the values represent time booked in seconds',
                            "ticket": ticket,
                            "members": {},
                            "support_hours_per_member":{},
                            "development_hours_by_the_author": 0
                         }

        base_url = "https://pureescapes.atlassian.net"
        url = base_url+"/rest/api/2/issue/"+ticket+"/worklog"

        auth = HTTPBasicAuth(os.getenv("PE_JIRA_USERNAME"), os.getenv("PE_JIRA_BI_LISTENER"))

        headers = {
            "Accept": "application/json"
        }

        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth
        )

        # challenge.datetime_start = self.utc.localize(challenge.datetime_start)
        # challenge.datetime_end = self.utc.localize(challenge.datetime_end)

        structured_output = json.loads(response.text)

        author_of_ticket = self.get_author_of_ticket(ticket)
        time_tracking['author'] = author_of_ticket


        for worklog_item in structured_output['worklogs']:
            member_of_team = worklog_item['author']['displayName']
            booked_time_in_seconds = worklog_item['timeSpentSeconds']

            # time_the_work_started_as_str=worklog_item['started']
            date_of_worklog_item = dateutil.parser.parse(worklog_item['started'])
            if self.utc.localize(start_date) <= date_of_worklog_item <= self.utc.localize(end_date):
                if member_of_team not in time_tracking['members'].keys():
                    time_tracking['members'][member_of_team] = booked_time_in_seconds
                else:
                    time_tracking['members'][member_of_team] += booked_time_in_seconds

                if member_of_team == author_of_ticket:
                    time_tracking["development_hours_by_the_author"] += booked_time_in_seconds/3600
                else:
                    if member_of_team not in time_tracking["support_hours_per_member"].keys():
                        time_tracking["support_hours_per_member"][member_of_team] = booked_time_in_seconds/3600
                    else:
                        time_tracking["support_hours_per_member"][member_of_team] += booked_time_in_seconds/3600




            # print (member_of_team, booked_time_in_seconds)




        return time_tracking

    def get_time_tracking_of_a_ticket_per_user_for_a_specific_period2(self, ticket: str, start_date: datetime, end_date: datetime):
        #todo deprecate
        '''
        on jira's data model, each author object corresponds to a time booking, and the the field "started"
        represents when the time was spent.
        Eg. The expectation is that a user should book time for a specific week and on jira dialog the box 'Date Started' should point to the appropriate date of the week

        :param ticket:
        :return:
        '''
        time_tracking = []
        # time_tracking = {"timestamp_this_was_created":self.get_now_as_a_string(),
        #                  'comments':'the values represent time booked in seconds',
        #                     "ticket": ticket,
        #                     "members": {},
        #                     "support_hours_per_member":{},
        #                     "development_hours_by_the_author": 0
        #                  }

        base_url = "https://pureescapes.atlassian.net"
        url = base_url+"/rest/api/2/issue/"+ticket+"/worklog"

        auth = HTTPBasicAuth(os.getenv("PE_JIRA_USERNAME"), os.getenv("PE_JIRA_BI_LISTENER"))

        headers = {
            "Accept": "application/json"
        }

        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth
        )

        # challenge.datetime_start = self.utc.localize(challenge.datetime_start)
        # challenge.datetime_end = self.utc.localize(challenge.datetime_end)

        structured_output = json.loads(response.text)

        author_of_ticket = self.get_author_of_ticket(ticket)



        for worklog_item in structured_output['worklogs']:
            item = {}
            member_of_team = worklog_item['author']['displayName']
            booked_time_in_seconds = worklog_item['timeSpentSeconds']

            # time_the_work_started_as_str=worklog_item['started']
            date_of_worklog_item = dateutil.parser.parse(worklog_item['started'])
            if self.utc.localize(start_date) <= date_of_worklog_item <= self.utc.localize(end_date):
                # if member_of_team not in time_tracking['members'].keys():
                #     time_tracking['members'][member_of_team] = booked_time_in_seconds
                # else:
                #     time_tracking['members'][member_of_team] += booked_time_in_seconds
                #
                # if member_of_team == author_of_ticket:
                #     time_tracking["development_hours_by_the_author"] += booked_time_in_seconds/3600
                # else:
                #     if member_of_team not in time_tracking["support_hours_per_member"].keys():
                #         time_tracking["support_hours_per_member"][member_of_team] = booked_time_in_seconds/3600
                #     else:
                #         time_tracking["support_hours_per_member"][member_of_team] += booked_time_in_seconds/3600

                item["when"] = date_of_worklog_item
                item["booked_hours"] = booked_time_in_seconds/3600

                if author_of_ticket == member_of_team:
                    item["contribution_type"] = "development"
                else:
                    item["contribution_type"] = "support"

                item["member_of_team"] = member_of_team

                time_tracking.append(item)







        return time_tracking





def try_with_standard_HTML():
    url = "https://pureescapes.atlassian.net"
    body = {
        "username": os.getenv("PE_JIRA_USERNAME"),
        "password": os.getenv("PE_JIRA_BI_LISTENER")
    }
    headers = {"content_type": "application/json"}
    r = requests.post(url, data=body, headers=headers)
    print(r.text)

def attempt_3():
    jira = JIRA(os.getenv("PE_JIRA_URI"), basic_auth=(os.getenv("PE_JIRA_USERNAME"), os.getenv("PE_JIRA_BI_LISTENER")))

    # print all of the project keys as an example
    for project in jira.projects():
        print(project.key)

def hello():
    # By default, the client will connect to a JIRA instance started from the Atlassian Plugin SDK
    # (see https://developer.atlassian.com/display/DOCS/Installing+the+Atlassian+Plugin+SDK for details).
    # Override this with the options parameter.
    options = {"server": "https://pureescapes.atlassian.net"}
    # print(os.getenv("PE_JIRA_USERNAME"), os.getenv("PE_JIRA_PASSWORD"))
    # jira = JIRA(options)
    j1 = JIRA(options, basic_auth=(os.getenv("PE_JIRA_USERNAME"), os.getenv("PE_JIRA_BI_LISTENER")))
    ticket = 'OWA-1400'
    issue = j1.issue(ticket)

    summary = issue.fields.summary

    print('ticket: ', ticket, summary)



if __name__ == "__main__":
    # hello()
    # try_with_standard_HTML()
    attempt_3()
