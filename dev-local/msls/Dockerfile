FROM golang:alpine

WORKDIR /go/src/app
COPY . .

RUN go install -v .

CMD ["app"]
