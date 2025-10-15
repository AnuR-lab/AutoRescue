"""
Cognito Credentials Provider Management Script
Sets up Cognito for AgentCore Gateway authentication
"""
import argparse
import boto3
import json
import sys


class CognitoCredentialsProvider:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.cognito = boto3.client('cognito-idp', region_name=region)
        self.ssm = boto3.client('ssm', region_name=region)
        self.project_name = 'autorescue'
        
    def create_provider(self, name: str):
        """Create Cognito User Pool and App Client for authentication"""
        print(f"🚀 Creating Cognito Credentials Provider: {name}")
        
        # Create User Pool
        print("  Creating Cognito User Pool...")
        user_pool_response = self.cognito.create_user_pool(
            PoolName=f'{name}-user-pool',
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': True,
                    'RequireLowercase': True,
                    'RequireNumbers': True,
                    'RequireSymbols': False
                }
            },
            AutoVerifiedAttributes=['email'],
            UsernameAttributes=['email'],
            Schema=[
                {
                    'Name': 'email',
                    'AttributeDataType': 'String',
                    'Required': True,
                    'Mutable': True
                }
            ],
            UserPoolTags={
                'Project': 'AutoRescue',
                'Name': name
            }
        )
        
        user_pool_id = user_pool_response['UserPool']['Id']
        print(f"  ✅ User Pool created: {user_pool_id}")
        
        # Create User Pool Domain
        domain_name = f"{name.replace('_', '-').lower()}-{user_pool_id[:8]}"
        try:
            self.cognito.create_user_pool_domain(
                Domain=domain_name,
                UserPoolId=user_pool_id
            )
            print(f"  ✅ User Pool Domain created: {domain_name}")
        except Exception as e:
            print(f"  ⚠️  Domain creation skipped: {str(e)}")
        
        # Create App Client
        print("  Creating App Client...")
        app_client_response = self.cognito.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName=f'{name}-web-client',
            GenerateSecret=False,
            RefreshTokenValidity=30,
            AccessTokenValidity=60,
            IdTokenValidity=60,
            TokenValidityUnits={
                'AccessToken': 'minutes',
                'IdToken': 'minutes',
                'RefreshToken': 'days'
            },
            ExplicitAuthFlows=[
                'ALLOW_USER_PASSWORD_AUTH',
                'ALLOW_REFRESH_TOKEN_AUTH',
                'ALLOW_USER_SRP_AUTH'
            ],
            PreventUserExistenceErrors='ENABLED'
        )
        
        app_client_id = app_client_response['UserPoolClient']['ClientId']
        print(f"  ✅ App Client created: {app_client_id}")
        
        # Construct OAuth discovery URL
        discovery_url = f"https://cognito-idp.{self.region}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
        
        # Store in SSM
        params = {
            f'/app/{self.project_name}/agentcore/cognito_user_pool_id': user_pool_id,
            f'/app/{self.project_name}/agentcore/cognito_domain': domain_name,
            f'/app/{self.project_name}/agentcore/web_client_id': app_client_id,
            f'/app/{self.project_name}/agentcore/cognito_discovery_url': discovery_url,
            f'/app/{self.project_name}/agentcore/cognito_provider_name': name
        }
        
        for param_name, param_value in params.items():
            self.ssm.put_parameter(
                Name=param_name,
                Value=param_value,
                Type='String',
                Overwrite=True
            )
        
        print("\n✅ Cognito Credentials Provider created successfully!")
        print(f"\n📋 Configuration Details:")
        print(f"   User Pool ID: {user_pool_id}")
        print(f"   Domain: {domain_name}")
        print(f"   App Client ID: {app_client_id}")
        print(f"   Discovery URL: {discovery_url}")
        print(f"\n💡 Create a test user:")
        print(f"   aws cognito-idp admin-create-user --user-pool-id {user_pool_id} --username test@example.com --user-attributes Name=email,Value=test@example.com --temporary-password TempPass123!")
        
        return {
            'user_pool_id': user_pool_id,
            'app_client_id': app_client_id,
            'domain': domain_name,
            'discovery_url': discovery_url
        }
    
    def delete_provider(self, name: str = None, confirm: bool = False):
        """Delete Cognito User Pool"""
        try:
            if not name:
                # Get from SSM
                response = self.ssm.get_parameter(
                    Name=f'/app/{self.project_name}/agentcore/cognito_provider_name'
                )
                name = response['Parameter']['Value']
            
            response = self.ssm.get_parameter(
                Name=f'/app/{self.project_name}/agentcore/cognito_user_pool_id'
            )
            user_pool_id = response['Parameter']['Value']
        except:
            print("❌ No Cognito provider found to delete")
            return
        
        if not confirm:
            confirm_input = input(f"Delete Cognito provider '{name}' (User Pool: {user_pool_id})? (yes/no): ")
            if confirm_input.lower() != 'yes':
                print("Cancelled")
                return
        
        print(f"🗑️  Deleting Cognito provider: {name}")
        
        # Delete User Pool
        try:
            self.cognito.delete_user_pool(UserPoolId=user_pool_id)
            print(f"  ✅ User Pool deleted: {user_pool_id}")
        except Exception as e:
            print(f"  ⚠️  Error deleting user pool: {str(e)}")
        
        # Delete SSM parameters
        param_names = [
            f'/app/{self.project_name}/agentcore/cognito_user_pool_id',
            f'/app/{self.project_name}/agentcore/cognito_domain',
            f'/app/{self.project_name}/agentcore/web_client_id',
            f'/app/{self.project_name}/agentcore/cognito_discovery_url',
            f'/app/{self.project_name}/agentcore/cognito_provider_name'
        ]
        
        for param_name in param_names:
            try:
                self.ssm.delete_parameter(Name=param_name)
            except:
                pass
        
        print("✅ Cognito provider deleted successfully")


def main():
    parser = argparse.ArgumentParser(description='Manage Cognito Credentials Provider')
    parser.add_argument('action', choices=['create', 'delete'], help='Action to perform')
    parser.add_argument('--name', help='Provider name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    provider = CognitoCredentialsProvider(region=args.region)
    
    if args.action == 'create':
        if not args.name:
            print("Error: --name required for create action")
            sys.exit(1)
        provider.create_provider(args.name)
    elif args.action == 'delete':
        provider.delete_provider(args.name, args.confirm)


if __name__ == '__main__':
    main()
