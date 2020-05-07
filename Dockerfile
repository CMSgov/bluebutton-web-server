FROM python:3.6
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN pip install pip-tools
RUN make reqs-compile
RUN make reqs-download
RUN make reqs-install
RUN pip install psycopg2
RUN if [ ! -d "bluebutton-css" ] ; then git clone https://github.com/CMSgov/bluebutton-css.git ; else echo "CSS already installed." ; fi

