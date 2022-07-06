FROM python:latest

WORKDIR /usr/src/app
RUN /usr/local/bin/python -m pip install --upgrade pip
COPY requirements.txt ./

RUN pip install --upgrade pip setuptools==57.5.0
RUN pip install --upgrade python-pushover


RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./uscis_status.py" ]
