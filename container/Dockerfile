FROM registry.access.redhat.com/ubi7/ubi:7.6-177

ENV PATH="/opt/rh/rh-python36/root/usr/bin:${PATH}"﻿ \
    PYTHONPATH=/storage-agent \
    USER_UID=1001 \
    USER_NAME=storage-agent
COPY requirements.txt /storage-agent/

RUN yum install -y rh-python36-python-pip.noarch
RUN pip3 install -r /storage-agent/requirements.txt

COPY . /storage-agent/container
RUN chmod 755 /storage-agent/container/hack/docker-entrypoint.sh
USER ${USER_UID}
WORKDIR /storage-agent

ENTRYPOINT ["./container/hack/docker-entrypoint.sh"]
