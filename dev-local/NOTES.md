
  # metabase:
  #   image: metabase/metabase:latest
  #   volumes:
  #     - ${PWD}/data:/data
  #   ports:
  #     - "3000:3000"
  #   depends_on:
  #     - db
  #   environment:
  #     MB_DB_TYPE: postgres
  #     MB_DB_DBNAME: bluebutton
  #     MB_DB_PORT: 5432
  #     MB_DB_USER: postgres
  #     MB_DB_PASS: toor
  #     MB_DB_HOST: db
  #   healthcheck:
  #     test: curl --fail -I http://localhost:3000/api/health || exit 1
  #     interval: 15s
  #     timeout: 5s
  #     retries: 5