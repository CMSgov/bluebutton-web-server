# Build, Tag, and Publish integration and selenium tests ECR image

Go to BB2 local repo base directory and do the followings (assume aws cli installed and configured properly):

```

aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/f5g8o1y9
cd <bb2-local-repo-base-dir>/Dockerfiles
docker build -f Dockerfile.selenium-jenkins -t bb2-cbc-build-selenium .
docker tag bb2-cbc-build-selenium:latest public.ecr.aws/f5g8o1y9/bb2-cbc-build-selenium:latest
docker push public.ecr.aws/f5g8o1y9/bb2-cbc-build-selenium:latest

```