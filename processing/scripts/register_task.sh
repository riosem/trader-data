export APP=$APP
export IMAGE=$IMAGE
export MODULE=$MODULE
export CPU=$CPU
export MEMORY=$MEMORY
export EXEC_ROLE_NAME=$EXEC_ROLE_NAME
export TASK_ROLE_NAME=$TASK_ROLE_NAME
export LOG_GROUP=$LOG_GROUP
export LOG_REGION=$LOG_REGION

cd ./processing
envsubst < ecs-task-def-data-processing.json.template > ecs-task-def-data-processing.json
aws ecs register-task-definition --cli-input-json file://ecs-task-def-data-processing.json > /dev/null