ARG ACMED_PLUGIN_BASE_IMAGE=python:3.12-slim
FROM ${ACMED_PLUGIN_BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/plugin

USER root
COPY acmed-issuer-acmesh/addon/apt-packages.txt /tmp/apt-packages.txt
RUN apt-get update \
    && xargs -r apt-get install --yes --no-install-recommends < /tmp/apt-packages.txt \
    && rm -rf /var/lib/apt/lists/* /tmp/apt-packages.txt

COPY acmed-issuer-acmesh/addon/install.sh /tmp/install-addon.sh
RUN chmod 0755 /tmp/install-addon.sh \
    && /tmp/install-addon.sh \
    && rm -f /tmp/install-addon.sh

COPY acmed-plugin-sdk /opt/src/acmed-plugin-sdk
RUN pip install --no-cache-dir /opt/src/acmed-plugin-sdk[server] \
    && rm -rf /opt/src/acmed-plugin-sdk

COPY acmed-issuer-acmesh /opt/src/acmed-issuer-acmesh
RUN pip install --no-cache-dir /opt/src/acmed-issuer-acmesh \
    && rm -rf /opt/src/acmed-issuer-acmesh

EXPOSE 8081
CMD ["python", "-m", "uvicorn", "plugin_service.main:app", "--host", "0.0.0.0", "--port", "8081"]
