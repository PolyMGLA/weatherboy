FROM python:3.11
WORKDIR /
COPY . /
RUN pip install -r requirements.txt
CMD ["/bin/bash", "-c", "python main.py"]