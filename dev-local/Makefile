BFD_MOUNT_POINT ?= "beneficiary-fhir-data"
# psword for certs: changeit
build:
	cd ${BFD_MOUNT_POINT}/apps; mvn clean install -DskipITs

verify:
	cd ${BFD_MOUNT_POINT}/apps; mvn clean verify

run: build
	cd ${BFD_MOUNT_POINT}/apps/bfd-server; mvn --projects bfd-server-war package dependency:copy antrun:run org.codehaus.mojo:exec-maven-plugin:exec@server-start

docker: build
	cd ${BFD_MOUNT_POINT}/apps/bfd-server; mvn -Dits.db.url="jdbc:postgresql://bfddb:5432/bfd?user=bfd&password=InsecureLocalDev" --projects bfd-server-war package dependency:copy antrun:run org.codehaus.mojo:exec-maven-plugin:exec@server-start
	tail -f ${BFD_MOUNT_POINT}/apps/bfd-server/bfd-server-war/target/server-work/server-console.log

stop:
	cd ${BFD_MOUNT_POINT}/apps/bfd-server; mvn --projects bfd-server-war package dependency:copy antrun:run org.codehaus.mojo:exec-maven-plugin:exec@server-stop

fix: build
	cd ${BFD_MOUNT_POINT}/apps/bfd-pipeline/bfd-pipeline-rif-extract; mvn exec:java -Dexec.mainClass="gov.cms.bfd.pipeline.rif.extract.synthetic.SyntheticDataFixer4" -Dexec.classpathScope=test

load: build
	cd ${BFD_MOUNT_POINT}/apps/bfd-pipeline/bfd-pipeline-rif-load; mvn -Dits.db.url=jdbc:postgresql://bfddb:5432/bfd -Dits.db.username=bfd -Dits.db.password=InsecureLocalDev -Dit.test=RifLoaderIT#loadSyntheticData clean verify
