# Splunk BB2 Authorization Flow Dashboard Setup

A dashboard was created in Splunk as a tool to help with analysis of the authorization flow trace logging.

If there is a need to reinstall the dashboard in Spunk, follow these steps:

1. Create a new empty dashboard.
2. Click on the -Edit- button.
3. Click on the -Source- button.
4. Right click and choose "Select all".
5. Copy the contents of the bb2_splunk_authorization_flow_dashboard.xml file in to your clipboard.
6. Past the contents over top of the selected (all) source in Splunk.
7. Click -Save-.

Note that there is probably an easier way to do the above in Splunk :-)

Some tips when working with the dashboard source:

* The "xmllint" (linux) command line tool is useful for formatting. The following is an example:

  ```bash
  $ xmllint -format -recover unformatted.xml > formatted.xml
  ```

* The "xsel" (linux) command line tool is useful for quickly copying the file contents in to your clipboard. The following is an example:

  ```bash
  $ cat bb2_splunk_authorization_flow_dashboard.xml | xsel -ib
  ```

* You can drill in to almost any cell or chart item on the dashboard by clicking on it. To open in a new browser tab, use \<CTRL\>-\<mouse click\>. This will bring up a new search that includes the related parameters clicked on.

