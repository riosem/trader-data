import boto3
import os

REGION = os.environ.get("REGION")
ecs_client = boto3.client('ecs', REGION)

# Specify the cluster name
cluster_name = os.environ.get("CLUSTER_NAME")


def stop_all_tasks(cluster):
    # List all tasks in the cluster
    tasks = ecs_client.list_tasks(cluster=cluster)
    if tasks['taskArns']:
        # Stop each task
        for task_arn in tasks['taskArns']:
            ecs_client.stop_task(cluster=cluster, task=task_arn)
            print(f"Stopped task: {task_arn}")
    else:
        print("No tasks found in the cluster.")


def delete_all_services(cluster):
    # List all services in the cluster
    services = ecs_client.list_services(cluster=cluster)
    if services['serviceArns']:
        # Delete each service
        for service_arn in services['serviceArns']:
            ecs_client.update_service(cluster=cluster, service=service_arn, desiredCount=0)
            ecs_client.delete_service(cluster=cluster, service=service_arn)
            print(f"Deleted service: {service_arn}")
    else:
        print("No services found in the cluster.")


if __name__ == "__main__":
    stop_all_tasks(cluster_name)
    delete_all_services(cluster_name)
