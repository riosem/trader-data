
aws ecr create-repository --repository-name $APP --region $REGION 2>/dev/null || true

docker build -f ./processing/tasks/Dockerfile -t $APP:latest .

docker tag $APP:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$APP:latest

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$APP:latest