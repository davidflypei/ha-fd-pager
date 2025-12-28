FROM python:3.13-slim

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Python 3 HTTP Server serves the current working dir
# So let's set it to our add-on persistent data directory.

# Copy data for add-on
COPY . $VIRTUAL_ENV/
RUN pip3 install -r requirements.txt
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
