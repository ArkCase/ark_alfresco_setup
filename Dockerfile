#  Alfresco Setup build

FROM 345280441424.dkr.ecr.ap-south-1.amazonaws.com/ark_base:latest

LABEL ORG="Armedia LLC" \
      APP="Alfresco Setup" \
      VERSION="1.0" \
      IMAGE_SOURCE=https://github.com/ArkCase/ark_alfresco_setup \
      MAINTAINER="Armedia LLC"

WORKDIR /app

# Set default docker_context.
ARG resource_path=artifacts

COPY ${resource_path}/setup_alfresco.py .

RUN yum update -y && \
    yum install python3-pip -y && \
    pip3 install requests && \
    yum clean all && \
    useradd --system --no-create-home --home-dir /app alfresco && \
    chmod +x /app/setup_alfresco.py && \
    chown -R alfresco:alfresco /app 

USER alfresco

ENTRYPOINT ["python3","/app/setup_alfresco.py"]

