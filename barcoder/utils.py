import boto3


def get_cognito_ids(client, user_pool_id):
    """
    Return a sequence of (netid, cognito_id)

    example usage:

    client = boto3.client('cognito-idp')
    mapping = get_cognito_ids(client, 'us-west-2_wfuighQ6A')
    """

    paginator = client.get_paginator('list_users')
    user_iterator = paginator.paginate(
        UserPoolId=user_pool_id,
        AttributesToGet=[
            'sub',
        ])

    for page in user_iterator:
        for user in page['Users']:
            netid = user['Username'].split('_')[-1]
            cognito_id = user['Attributes'][0]['Value']
            yield (netid, cognito_id)
