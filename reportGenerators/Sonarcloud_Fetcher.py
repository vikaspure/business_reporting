#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (C) Pure Escapes 2020 - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential

Written by Christos Tsotskas <info@pure-escapes.com>, April 2020

"""

import os
import json
import requests

import datetime
import os

import json, requests, pprint
from requests.auth import HTTPBasicAuth

import datetime
import dateutil.parser
import copy
import csv
import boto3

from datetime import timedelta


def get_now_as_a_string():
    now_time_object = datetime.datetime.now()
    return now_time_object.strftime("%Y%m%d_%H%M")

def upload_file(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        print(str(e))
        return False
    return True

def get_coverage_for_component(component_name: str):
    '''

    :param component_name: as it appears on sonarcloud
    :return: float (which is a percentage already)
    '''

    url = 'https://sonarcloud.io/api/measures/component_tree'

    query = {'component': component_name,
             'metricKeys': "coverage",
             'ps': 100,
             'p': 1}
    r = requests.get(url, params=query, auth=(os.environ['PE_SONAR_TOKEN_FOR_BUSINESS_REPORT_TOKEN'], ''))
    metrics_dict = r.json()

    formatted_output = json.dumps(metrics_dict, indent=2)
    # print(formatted_output)

    coverage_value = 0.0
    if metrics_dict["baseComponent"]["measures"][0]["metric"] == "coverage":
        coverage_value = float(metrics_dict["baseComponent"]["measures"][0]["value"])

    print("coverage for "+component_name+":", str(coverage_value), "%")
    return coverage_value


def generate_coverage_for_all_repos(input: dict ):
    output =  { 'timestamp_this_was_created': get_now_as_a_string(),
                'coverage_per_repo': copy.deepcopy(input)
                }

    for repo in output['coverage_per_repo'].keys():
        output['coverage_per_repo'][repo] = get_coverage_for_component(repo)


    return output



def generate_a_report_file_for_code_coverage_per_repo(input: dict, week_start: datetime):
    time_for_five_days_later = week_start + timedelta(days=4)
    start_as_str = week_start.strftime("%d_%m_%Y")
    end_as_str = time_for_five_days_later.strftime("%d_%m_%Y")
    file_name = "Code_coverage_report_per_repository_from_"+start_as_str+"_to_"+end_as_str+"_generated_at_"+input['timestamp_this_was_created']+".csv"
    output_filename = '/tmp/' + file_name

    with open(output_filename, 'w') as csv_file:

        fieldnames = ['week_commencing', 'repository', 'coverage(%)']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()

        for repo_name, coverage in input['coverage_per_repo'].items():

            writer.writerow({'week_commencing': week_start.strftime("%Y/%m/%d"),
             'repository': repo_name.replace('pure-escapes_',''),
             'coverage(%)': coverage})

    upload_file(output_filename, "pure-business-reporting", file_name)

