# Creating Fixtures for testing

Run the following command to create fixtures from the data in the database

    python manage.py dumpdata --format=json server > ./apps/fhir/server/fixtures/fhir_server_testdata.json

The above command will:
 - Run the dumpdata process
 - format the output as json
 - just export from the models in apps.fhir.server app
 - pipe the output to a file in the apps.fhir.server.fixtures folder
 
This file can be imported into tests in the apps.fhir.server app using the following 
statement:

        fixtures = ['fhir_server_testdata.json']

