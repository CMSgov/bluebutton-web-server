# Creating Fixtures for testing

Run the following command to create fixtures from the data in the database

    python manage.py dumpdata --format=json bluebutton > ./apps/fhir/bluebutton/fixtures/fhir_bluebutton_testdata.json

The above command will:
 - Run the dumpdata process
 - format the output as json
 - just export from the models in apps.fhir.bluebutton app
 - pipe the output to a file in the apps.fhir.bluebutton.fixtures folder
 
This file can be imported into tests in the apps.fhir.bluebutton app using the following 
statement:

        fixtures = ['fhir_bluebutton_testdata.json']
