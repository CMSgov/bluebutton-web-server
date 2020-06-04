FROM golang:1.13.5-alpine3.10

WORKDIR /go/src/app
COPY . .

RUN go install -v .

CMD ["msls"]
