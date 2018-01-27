# Local Docker Development

```
docker-compose up
```

If you're working with a fresh db image
the migrations have to be run.
```
docker-compose exec web docker-compose/migrate.sh
# if any permissions errors are thrown try
# docker-compose exec web chmod +x docker-compose/migrate.sh
# then run the migrate script again
```

# Running tests from your host
```
# run tests
docker-compose exec web python runtests.py
```
