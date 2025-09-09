ARG BUILD_FROM
FROM $BUILD_FROM

# Install runtime deps
RUN apk add --no-cache python3 py3-pip bash jq

# Create isolated virtual environment to avoid PEP 668 restrictions
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN /opt/venv/bin/pip install --no-cache-dir --upgrade pip

# Python deps (inside venv)
COPY requirements.txt /requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir -r /requirements.txt

# Copy app
WORKDIR /app
COPY app/ /app/
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# Always keep the container alive via our runner
CMD [ "/run.sh" ]

