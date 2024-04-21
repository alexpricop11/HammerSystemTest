FROM ubuntu:latest
LABEL authors="Smart"

ENTRYPOINT ["top", "-b"]