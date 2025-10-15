"""
AgentCore Memory Management Script
Creates and manages memory for conversation context
"""
import argparse
import boto3
import sys


class AgentCoreMemoryManager:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.ssm = boto3.client('ssm', region_name=region)
        self.project_name = 'autorescue'
        
    def create_memory(self, name: str, event_expiry_days: int = 30):
        """Create AgentCore Memory configuration"""
        print(f"🚀 Creating AgentCore Memory: {name}")
        
        # Store memory configuration in SSM
        params = {
            f'/app/{self.project_name}/agentcore/memory_name': name,
            f'/app/{self.project_name}/agentcore/memory_expiry_days': str(event_expiry_days),
            f'/app/{self.project_name}/agentcore/memory_enabled': 'true'
        }
        
        for param_name, param_value in params.items():
            self.ssm.put_parameter(
                Name=param_name,
                Value=param_value,
                Type='String',
                Overwrite=True,
                Tags=[
                    {'Key': 'Project', 'Value': 'AutoRescue'},
                    {'Key': 'Component', 'Value': 'Memory'}
                ]
            )
            print(f"  ✅ Created parameter: {param_name}")
        
        print(f"\n✅ Memory configuration created successfully!")
        print(f"\n📋 Configuration Details:")
        print(f"   Memory Name: {name}")
        print(f"   Event Expiry: {event_expiry_days} days")
        print(f"   Memory Enabled: true")
        
        return {
            'name': name,
            'expiry_days': event_expiry_days
        }
    
    def delete_memory(self, confirm: bool = False):
        """Delete AgentCore Memory configuration"""
        try:
            response = self.ssm.get_parameter(
                Name=f'/app/{self.project_name}/agentcore/memory_name'
            )
            memory_name = response['Parameter']['Value']
        except:
            print("❌ No memory configuration found to delete")
            return
        
        if not confirm:
            confirm_input = input(f"Delete memory configuration '{memory_name}'? (yes/no): ")
            if confirm_input.lower() != 'yes':
                print("Cancelled")
                return
        
        print(f"🗑️  Deleting memory configuration: {memory_name}")
        
        # Delete SSM parameters
        param_names = [
            f'/app/{self.project_name}/agentcore/memory_name',
            f'/app/{self.project_name}/agentcore/memory_expiry_days',
            f'/app/{self.project_name}/agentcore/memory_enabled'
        ]
        
        for param_name in param_names:
            try:
                self.ssm.delete_parameter(Name=param_name)
                print(f"  ✅ Deleted: {param_name}")
            except:
                pass
        
        print("✅ Memory configuration deleted successfully")


def main():
    parser = argparse.ArgumentParser(description='Manage AgentCore Memory')
    parser.add_argument('action', choices=['create', 'delete'], help='Action to perform')
    parser.add_argument('--name', help='Memory name')
    parser.add_argument('--event-expiry-days', type=int, default=30, help='Event expiry in days')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    manager = AgentCoreMemoryManager(region=args.region)
    
    if args.action == 'create':
        if not args.name:
            print("Error: --name required for create action")
            sys.exit(1)
        manager.create_memory(args.name, args.event_expiry_days)
    elif args.action == 'delete':
        manager.delete_memory(args.confirm)


if __name__ == '__main__':
    main()
