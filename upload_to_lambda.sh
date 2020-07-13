#!/bin/bash

#pipenv install
#venv_path=`pipenv --venv`
#cp -r $venv_path/lib/python3.6/site-packages ./

zip -r function.zip ./*
scp -i ~/.ssh/pe-jenkins.pem function.zip ubuntu@52.16.177.114:
#aws lambda update-function-code --function-name business_reporting --zip-file fileb://function.zip
