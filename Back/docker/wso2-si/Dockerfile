FROM wso2/wso2si:4.4.0

ARG SI_HOME=/home/wso2carbon/wso2si-4.4.0

USER root

COPY ./drivers/mysql-connector-j-9.7.0.jar ${SI_HOME}/lib/mysql-connector-j-9.7.0.jar
COPY ./drivers/siddhi-io-rabbitmq-3.0.8.jar ${SI_HOME}/lib/siddhi-io-rabbitmq-3.0.8.jar

RUN chmod 644 ${SI_HOME}/lib/mysql-connector-j-9.7.0.jar && \
    chmod 644 ${SI_HOME}/lib/siddhi-io-rabbitmq-3.0.8.jar

RUN echo "=== COMPROBANDO LIBRERIAS ===" && \
    ls -l ${SI_HOME}/lib | grep -Ei "mysql|rabbit|rdbms" && \
    find ${SI_HOME}/lib -iname "*rabbit*" | grep rabbit

USER wso2carbon