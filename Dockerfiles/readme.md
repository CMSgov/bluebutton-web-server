# Build, Tag, and Publish integration and selenium tests ECR image - used by github CI check

Go to BB2 local repo base directory and do the followings (assume aws cli installed and configured properly):

```
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/q8j7a4l4

cd <bb2-local-repo-base-dir>/Dockerfiles

docker build --platform=linux/amd64 \
    -f Dockerfile.selenium-jenkins-python312-plus-chromedriver \
    -t bb2-cbc-build-selenium-python312-chromium .

docker tag bb2-cbc-build-selenium-python312-chromium:latest \
    public.ecr.aws/q8j7a4l4/bb2-cbc-build-selenium-python312-chromium:latest

docker push public.ecr.aws/q8j7a4l4/bb2-cbc-build-selenium-python312-chromium:latest
```
