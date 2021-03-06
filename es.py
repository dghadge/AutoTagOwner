from __future__ import print_function
import json
import boto3
import logging
import time
import datetime
import urllib2
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    resourceName = ''

    try:
        region = event['region']
        detail = event['detail']
        eventname = detail['eventName']
        arn = detail['userIdentity']['arn']
        principal = detail['userIdentity']['principalId']
        userType = detail['userIdentity']['type']

        if userType == 'IAMUser':
            user = detail['userIdentity']['userName']
        elif userType == 'Root':
            user = detail['userIdentity']['userName']
        else:
            try:
                user = principal.split(':')[1]
            except:
                user = accountNumber

        if not detail['responseElements']:
            logger.warning('Not responseElements found')
            if detail['errorCode']:
                logger.error('errorCode: ' + detail['errorCode'])
            if detail['errorMessage']:
                logger.error('errorMessage: ' + detail['errorMessage'])
            return False

        es = boto3.client('es')
        sns = boto3.client('sns')

        if eventname == 'CreateElasticsearchDomain':
            resourceName=detail['responseElements']['domainStatus']['aRN']
            if not resourceName:
               resourceName=detail['responseElements']['domainStatus']['arn']
            logger.info(resourceName)

        else:
            logger.warning('Not supported action')

        if resourceName:
            logger.info("Delaying 3s before checking tags..")
            time.sleep(3)
            tags = es.list_tags(ARN=resourceName)
            tag_names = set(subd.get('Key') for subd in tags['TagList'])
            # Apply creator tag if none is found
            creatorTagFound = all(tag in tag_names for tag in ('Creator'))
            if not creatorTagFound:
                logger.info('Creator tag missing, applying tag...')
                es.add_tags(ARN=resourceName, TagList=[{'Key': 'CreatedBy', 'Value': user}])

        logger.info(' Remaining time (ms): ' + str(context.get_remaining_time_in_millis()) + '\n')
        return True
    except Exception as e:
        logger.error('Something went wrong: ' + str(e))
        return False