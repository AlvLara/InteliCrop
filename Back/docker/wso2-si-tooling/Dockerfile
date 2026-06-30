FROM eclipse-temurin:11-jdk-jammy

ARG TOOLING_HOME=/opt/wso2si-tooling-4.3.0

USER root

RUN apt-get update && \
    apt-get install -y curl unzip ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fL \
    -o /tmp/wso2si-tooling.zip \
    https://github.com/wso2/streaming-integrator-tooling/releases/download/v4.3.0/wso2si-tooling-4.3.0.zip && \
    unzip /tmp/wso2si-tooling.zip -d /opt && \
    rm /tmp/wso2si-tooling.zip

RUN mkdir -p ${TOOLING_HOME}/wso2/editor/deployment/workspace && \
    chmod +x ${TOOLING_HOME}/bin/tooling.sh

COPY ./drivers/mysql-connector-j-9.7.0.jar ${TOOLING_HOME}/lib/mysql-connector-j-9.7.0.jar

RUN chmod 644 ${TOOLING_HOME}/lib/mysql-connector-j-9.7.0.jar

EXPOSE 9390

WORKDIR ${TOOLING_HOME}

CMD ["sh", "-c", "/opt/wso2si-tooling-4.3.0/bin/tooling.sh --run"]