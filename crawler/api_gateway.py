import asyncio
import boto3
import random

from .common import logger

ALL_REGIONS = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-west-2", "eu-west-3", "eu-north-1",
    "eu-central-1", "ca-central-1",
    "ap-south-1", "ap-northeast-3", "ap-northeast-2",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
    "sa-east-1"
]


class ApiGateway:
    def __init__(self, uri: str, region=None, stage_name="default"):
        self.uri = uri

        self.region = region
        if self.region == None:
            self.region = random.choice(ALL_REGIONS)

        self.stage_name = stage_name
        self.rest_api_id = self.__new_api_gateway()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.delete_api_gateway()

    def __del__(self):
        asyncio.run(self.delete_api_gateway())

    @property
    def endpoint(self) -> str:
        return f"{self.rest_api_id}.execute-api.{self.region}.amazonaws.com/{self.stage_name}"

    def __new_api_gateway(self):
        # Init client
        session = boto3.session.Session()
        awsclient = session.client("apigateway", region_name=self.region)

        # Create simple rest API resource
        api_name = "corporate-info-crawler"
        create_api_response = awsclient.create_rest_api(
            name=api_name,
            endpointConfiguration={"types": ["REGIONAL"]}
        )

        logger.info(f"Created new API Gateway {create_api_response}")

        # Get ID for new resource
        get_resource_response = awsclient.get_resources(
            restApiId=create_api_response["id"]
        )
        rest_api_id = create_api_response["id"]

        # Create "Resource" (wildcard proxy path)
        create_resource_response = awsclient.create_resource(
            restApiId=create_api_response["id"],
            parentId=get_resource_response["items"][0]["id"],
            pathPart="{proxy+}"
        )

        # Allow all methods to new resource
        awsclient.put_method(
            restApiId=create_api_response["id"],
            resourceId=get_resource_response["items"][0]["id"],
            httpMethod="ANY",
            authorizationType="NONE",
            requestParameters={
                "method.request.path.proxy": True,
                "method.request.header.X-My-X-Forwarded-For": True
            }
        )

        # Make new resource route traffic to new host
        awsclient.put_integration(
            restApiId=create_api_response["id"],
            resourceId=get_resource_response["items"][0]["id"],
            type="HTTP_PROXY",
            httpMethod="ANY",
            integrationHttpMethod="ANY",
            uri=self.uri,
            connectionType="INTERNET",
            requestParameters={
                "integration.request.path.proxy": "method.request.path.proxy",
                "integration.request.header.X-Forwarded-For": "method.request.header.X-My-X-Forwarded-For"
            }
        )

        awsclient.put_method(
            restApiId=create_api_response["id"],
            resourceId=create_resource_response["id"],
            httpMethod="ANY",
            authorizationType="NONE",
            requestParameters={
                "method.request.path.proxy": True,
                "method.request.header.X-My-X-Forwarded-For": True
            }
        )

        awsclient.put_integration(
            restApiId=create_api_response["id"],
            resourceId=create_resource_response["id"],
            type="HTTP_PROXY",
            httpMethod="ANY",
            integrationHttpMethod="ANY",
            uri=f"{self.uri}/{{proxy}}",
            connectionType="INTERNET",
            requestParameters={
                "integration.request.path.proxy": "method.request.path.proxy",
                "integration.request.header.X-Forwarded-For": "method.request.header.X-My-X-Forwarded-For"
            }
        )

        # Creates deployment resource, so that our API to be callable
        awsclient.create_deployment(
            restApiId=rest_api_id,
            stageName=self.stage_name,
        )

        # Return endpoint name and whether it show it is newly created
        return rest_api_id

    async def delete_api_gateway(self):
        for i in range(5):
            try:
                self.__delete_api_gateway()
            except Exception:
                await asyncio.sleep(2**i)

    def __delete_api_gateway(self):
        session = boto3.session.Session()
        awsclient = session.client('apigateway', region_name=self.region)
        status = awsclient.delete_rest_api(restApiId=self.rest_api_id)
        logger.info(f"Deleted API Gateway {status}")
