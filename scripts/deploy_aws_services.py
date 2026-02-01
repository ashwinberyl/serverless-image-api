#!/usr/bin/env python3
"""
Setup script to initialize LocalStack resources (S3 bucket, DynamoDB table, Lambda, API Gateway).
Run this script after starting LocalStack with docker-compose.
"""
import boto3
import os
import sys
import shutil
import time
import zipfile

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system env vars

# Configuration from environment variables
LOCALSTACK_ENDPOINT = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'image-storage-bucket')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'ImageMetadata')
LAMBDA_ROLE_ARN = "arn:aws:iam::000000000000:role/lambda-role"


def get_client(service):
    """Get AWS client for LocalStack."""
    return boto3.client(
        service,
        endpoint_url=LOCALSTACK_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )


def create_s3_bucket():
    """Create S3 bucket for image storage."""
    s3 = get_client('s3')
    try:
        s3.head_bucket(Bucket=S3_BUCKET_NAME)
        print(f"✓ S3 bucket '{S3_BUCKET_NAME}' already exists")
    except s3.exceptions.ClientError:
        s3.create_bucket(Bucket=S3_BUCKET_NAME)
        print(f"✓ Created S3 bucket '{S3_BUCKET_NAME}'")
        cors_config = {
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
                'AllowedOrigins': ['*'],
                'ExposeHeaders': ['ETag']
            }]
        }
        s3.put_bucket_cors(Bucket=S3_BUCKET_NAME, CORSConfiguration=cors_config)


def create_dynamodb_table():
    """Create DynamoDB table for image metadata."""
    dynamodb = get_client('dynamodb')
    try:
        dynamodb.describe_table(TableName=DYNAMODB_TABLE_NAME)
        print(f"✓ DynamoDB table '{DYNAMODB_TABLE_NAME}' already exists")
    except dynamodb.exceptions.ResourceNotFoundException:
        dynamodb.create_table(
            TableName=DYNAMODB_TABLE_NAME,
            KeySchema=[{'AttributeName': 'image_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[
                {'AttributeName': 'image_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[{
                'IndexName': 'UserIdIndex',
                'KeySchema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            }],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print(f"✓ Created DynamoDB table '{DYNAMODB_TABLE_NAME}'")
        get_client('dynamodb').get_waiter('table_exists').wait(TableName=DYNAMODB_TABLE_NAME)


def package_lambda_code():
    """Package source code into a zip file."""
    if os.path.exists('lambda_package.zip'):
        os.remove('lambda_package.zip')
    
    # Create zip file manually to control structure
    with zipfile.ZipFile('lambda_package.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through src directory
        for root, dirs, files in os.walk('src'):
            for file in files:
                # Include python files and others if valid, but exclude cache
                if file.endswith('.py') and '__pycache__' not in root:
                    file_path = os.path.join(root, file)
                    # Calculate arcname to be relative to src/
                    arcname = os.path.relpath(file_path, 'src')
                    zipf.write(file_path, arcname)
    
    print("✓ Packaged Lambda code to lambda_package.zip")
    return 'lambda_package.zip'


def create_lambda_functions(zip_file):
    """Create Lambda functions."""
    client = get_client('lambda')
    
    with open(zip_file, 'rb') as f:
        code_content = f.read()
    
    functions = [
        {'name': 'upload_image', 'handler': 'handlers.upload_image.upload_image'},
        {'name': 'list_images', 'handler': 'handlers.list_images.list_images'},
        {'name': 'get_image', 'handler': 'handlers.get_image.get_image'},
        {'name': 'delete_image', 'handler': 'handlers.delete_image.delete_image'},
    ]
    
    function_arns = {}
    
    for func in functions:
        try:
            response = client.create_function(
                FunctionName=func['name'],
                Runtime='python3.9',
                Role=LAMBDA_ROLE_ARN,
                Handler=func['handler'],
                Code={'ZipFile': code_content},
                Environment={
                    'Variables': {
                        'S3_BUCKET_NAME': S3_BUCKET_NAME,
                        'DYNAMODB_TABLE_NAME': DYNAMODB_TABLE_NAME,
                        'LOCALSTACK_ENDPOINT': 'http://localstack:4566',
                        'AWS_REGION': AWS_REGION,
                        'STAGE': 'dev'
                    }
                },
                Timeout=30
            )
            function_arns[func['name']] = response['FunctionArn']
            print(f"✓ Created Lambda function '{func['name']}'")
        except client.exceptions.ResourceConflictException:
            client.update_function_code(
                FunctionName=func['name'],
                ZipFile=code_content
            )
            response = client.get_function(FunctionName=func['name'])
            function_arns[func['name']] = response['Configuration']['FunctionArn']
            print(f"✓ Updated Lambda function '{func['name']}'")
            
    return function_arns


def create_api_gateway(function_arns):
    """Create API Gateway and link to Lambdas."""
    apigateway = get_client('apigateway')
    
    # Create API
    apis = apigateway.get_rest_apis().get('items', [])
    api_id = next((api['id'] for api in apis if api['name'] == 'ImageServiceAPI'), None)
    
    if not api_id:
        api = apigateway.create_rest_api(name='ImageServiceAPI')
        api_id = api['id']
        print(f"✓ Created API Gateway 'ImageServiceAPI' (ID: {api_id})")
    else:
        print(f"✓ Found existing API Gateway 'ImageServiceAPI' (ID: {api_id})")

    # Get Root Resource
    resources = apigateway.get_resources(restApiId=api_id).get('items', [])
    root_id = next(r['id'] for r in resources if r['path'] == '/')
    
    # Create /images Resource
    images_resource = next((r for r in resources if r.get('pathPart') == 'images'), None)
    if not images_resource:
        images_resource = apigateway.create_resource(
            restApiId=api_id,
            parentId=root_id,
            pathPart='images'
        )
        print(f"✓ Created /images resource")
    else:
        print(f"✓ Found /images resource")
    images_id = images_resource['id']
    
    # Create /images/{image_id} Resource
    image_id_resource = next((r for r in resources if r.get('pathPart') == '{image_id}' and r.get('parentId') == images_id), None)
    if not image_id_resource:
        image_id_resource = apigateway.create_resource(
            restApiId=api_id,
            parentId=images_id,
            pathPart='{image_id}'
        )
        print(f"✓ Created /images/{{image_id}} resource")
    else:
        print(f"✓ Found /images/{{image_id}} resource")
    image_detail_id = image_id_resource['id']

    # Link Methods to Lambdas
    integration_opts = {
        'POST': {'func': 'upload_image', 'resource_id': images_id},
        'GET': {'func': 'list_images', 'resource_id': images_id},
    }
    
    detail_integration_opts = {
        'GET': {'func': 'get_image', 'resource_id': image_detail_id},
        'DELETE': {'func': 'delete_image', 'resource_id': image_detail_id}
    }

    def setup_method(http_method, resource_id, func_name):
        func_arn = function_arns[func_name]
        try:
            apigateway.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                authorizationType='NONE'
            )
            
            uri = f"arn:aws:apigateway:{AWS_REGION}:lambda:path/2015-03-31/functions/{func_arn}/invocations"
            
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                type='AWS_PROXY',
                integrationHttpMethod='POST',  # Only for integration
                uri=uri
            )
            print(f"✓ Configured {http_method} method for {func_name}")
        except apigateway.exceptions.ConflictException:
            # Re-put integration just in case
            uri = f"arn:aws:apigateway:{AWS_REGION}:lambda:path/2015-03-31/functions/{func_arn}/invocations"
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=uri
            )
            print(f"✓ Updated integration for {http_method} method")

    for method, opts in integration_opts.items():
        setup_method(method, opts['resource_id'], opts['func'])
        
    for method, opts in detail_integration_opts.items():
        setup_method(method, opts['resource_id'], opts['func'])
        
    # Deploy API
    apigateway.create_deployment(
        restApiId=api_id,
        stageName='dev'
    )
    print("✓ Deployed API to 'dev' stage")
    
    # Construct API Endpoint URL
    # Format: http://localhost:4566/restapis/{api_id}/{stage_name}/_user_request_/{path_part}
    api_url = f"{LOCALSTACK_ENDPOINT}/restapis/{api_id}/dev/_user_request_/images"
    return api_url


def main():
    print("=" * 60)
    print("Setting up LocalStack Full Stack (S3, DynamoDB, Lambda, API Gateway)")
    print("=" * 60)
    
    try:
        print("\n[1/4] Creating S3 & DynamoDB...")
        create_s3_bucket()
        create_dynamodb_table()
        
        print("\n[2/4] Packaging Lambda Code...")
        zip_file = package_lambda_code()
        
        print("\n[3/4] Deploying Lambdas...")
        func_arns = create_lambda_functions(zip_file)
        
        print("\n[4/4] Configuring API Gateway...")
        api_url = create_api_gateway(func_arns)
        
        print("\n" + "=" * 60)
        print("✓ SETUP COMPLETE")
        print("=" * 60)
        print(f"Your API is ready at:")
        print(f"{api_url}")
        print("\nUse this URL in your API calls!")
        print("=" * 60)
        
        # Write the URL to a file for easy access
        with open('api_url.txt', 'w') as f:
            f.write(api_url)
            
    except Exception as e:
        print(f"\n✗ Error during setup: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if os.path.exists('lambda_package.zip'):
            os.remove('lambda_package.zip')

if __name__ == '__main__':
    sys.exit(main())
