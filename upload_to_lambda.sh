#!/bin/bash

pipenv install
venv_path=`pipenv --venv`
mkdir deploy_dir
cp -r ./* deploy_dir/
rm -r deploy_dir/deploy_dir
cp -r $venv_path/lib/python3.6/site-packages/* deploy_dir/
cd deploy_dir/
zip -r ../function.zip ./*
cd ..
aws s3 cp function.zip s3://pure-artifactory/business_reporting/
aws lambda update-function-code \
        --function-name  business_reporting \
        --s3-bucket pure-artifactory \
        --s3-key business_reporting/function.zip
rm -r deploy_dir