# Table of Contents

- [Medicare Synthetic Patient Login Tester Tool Summary](#summary)
- [How to Use the Tool Locally](#localusage)
  - [Considerations for Usage](#localusage1)
  - [Python Virtual Enviornment Setup](#localusage2)
  - [Tool Command Line Options](#localusage3)
  - [Usage Example](#localusage4)
- [How to Use the Tool Via Jenkins CBC](#cbcusage)


# Medicare Synthetic Patient Login Tester Tool Summary<a id="summary"></a>

This README has information on the usage of a tool for testing Medicare.gov synthetic user account logins. This is for testing ranges of accounts with usernames in the "BBUserXXXXX" format.

This tool can be used periodicaly to verify the synthetic accounts are working as expected and to prevent activity expiration for those accounts that do not get used on a regular basis.

# How to Use the Tool Locally<a id="localusage"></a>

## Considerations for Usage:<a id="localusage1"></a>
- When running you should be connected to the VPN.
- Tests using a large set of accounts can take a long time to finish.
- Using too short of a sleep time between actions may cause your IP to be blocked.
- There is a limit to the number of logins per Selenium browser (driver) session. See `DRIVER_RESTART_COUNT` setting for how to configure, if needed.

## Python Virtual Enviornment Setup<a id="localusag2"></a>

Use the following command line to setup a virtual environment with needed packages installed.

If needed for your OS, you can change the Python version in the `setup_venv.sh` script. Edit the script and change this line, if needed:

```
PYTHON_VERSION=3.7
```

Run the script with the following command line:

```
sh setup_venv.sh
```

Now source the venv in the shell (terminal window) you will be running the tool from: 

```
source /tmp/venv_python/bin/activate
```

## Tool Command Line Options<a id="localusage3"></a>

To get a list of the available command line options, run the following command:

```
python test_medicare_logins.py -h
```
Output:
```
usage: test_medicare_logins.py [-h] [--url-base URL_BASE] --begin-user-number
                               BEGIN_USER_NUMBER --end-user-number
                               END_USER_NUMBER
                               [--sleep-between-actions SLEEP_BETWEEN_ACTIONS]
                               [--max-retry MAX_RETRY] [--headless]
                               [--driver-restart-count DRIVER_RESTART_COUNT]
                               [--connection-issue-sleep CONNECTION_ISSUE_SLEEP]
                               [--max-connection-issue-count MAX_CONNECTION_ISSUE_COUNT]

Utility to test a medicare.gov login using Selenium

optional arguments:
  -h, --help            show this help message and exit
  --url-base URL_BASE, -u URL_BASE
                        URL Base. Default = https://www.medicare.gov
  --begin-user-number BEGIN_USER_NUMBER, -b BEGIN_USER_NUMBER
                        The beginning synth account number. Ex. -b 0 for
                        BBUser00000.
  --end-user-number END_USER_NUMBER, -e END_USER_NUMBER
                        The ending synth account number. Ex. -b 10 for
                        BBUser00010.
  --sleep-between-actions SLEEP_BETWEEN_ACTIONS, -s SLEEP_BETWEEN_ACTIONS
                        Sleep time between actions. Default = 2.0
  --max-retry MAX_RETRY, -r MAX_RETRY
                        The max retry for each login attempt. Default = 3
  --headless            Run in headless mode. Default = False
  --driver-restart-count DRIVER_RESTART_COUNT, -d DRIVER_RESTART_COUNT
                        Restart the driver/browser after X logins. Default =
                        10
  --connection-issue-sleep CONNECTION_ISSUE_SLEEP, -c CONNECTION_ISSUE_SLEEP
                        Sleep time when connection/network/driver issue.
                        Default = 600
  --max-connection-issue-count MAX_CONNECTION_ISSUE_COUNT, -m MAX_CONNECTION_ISSUE_COUNT
                        Max connection issues before aborting! Default = 10
```

## Usage Example<a id="localusage4"></a>

The following is a usage example. This will test logins for accounts in the range `BBUser09998` through `BBUser10000`. It will sleep for 1 second between the different actions used by the tool to perform a login.

Run the following command line:
```
python test_medicare_logins.py --url-base https://test.medicare.gov \
    --begin-user-number 9998 --end-user-number 10000 \
    --sleep-between-actions 1.0 
```


The standard output will include the following information:
- A Selenium window pop-up showing the web browser activity while the tests are running.
  - To disabled this, use the `--headless` command line option.
- Info on the options used: url_base, sleep time and user account range.
- Activity while the login tests are being performed.
- A CSV format report when completed that includes the test status. This is one of the following:

  | Status | Description |
  | ------- |----------- |
  | SUCCESS | Login successful |
  | FAIL-LOGIN | Username/Password doesn't match | 
  | FAIL-PW-EXPIRED | Password has expired due to inactivity |
  | FAIL-UNKNOWN  | Unknown reason |
  - NOTE: If you wish to terminate the tool while it is running, you can press CTRL-c twice and you will still get the CSV report afterward. 

Output example:
```
# Using options: 
#                Using url_base:   https://test.medicare.gov
#   Using SLEEP_BETWEEN_ACTIONS:  1.0
#                     MAX_RETRY:  3
#                 HEADLESS_MODE:  True
#          DRIVER_RESTART_COUNT:  10
#        CONNECTION_ISSUE_SLEEP:  600
#    MAX_CONNECTION_ISSUE_COUNT:  10
#
# Beginning User Number:  9998
#    Ending User Number:  10000
#
# Starting.... Press CTRL-c twice to abort.
#
# ----
# TESING(0):  n=9998 username=BBUser09998 passwd=PW09998!
# LOGIN FAILED with:  FAIL-PW-EXPIRED
# ----
# TESING(0):  n=9999 username=BBUser09999 passwd=PW09999!
# LOGIN SUCCESSFUL!
#
# ----
# TESING(0):  n=10000 username=BBUser10000 passwd=PW10000!
# LOGIN FAILED with:  FAIL-PW-EXPIRED
#---
#---
#--- CSV REPORT ---
https://test.medicare.gov, BBUser09998, FAIL-PW-EXPIRED
https://test.medicare.gov, BBUser09999, SUCCESS
https://test.medicare.gov, BBUser10000, FAIL-PW-EXPIRED
#---
#---
```

# How to Use the Tool Via Jenkins CBC<a id="cbcusage"></a>

Jenkins CBC can be used to run the tester using a container node.

There is a Jenkins CBC project called "RUN - Login Tester". This utilizes the Jenkinsfile `Jenkinsfiles/Jenkinsfile.cbc-run-medicare-login-tester`. 

The tester command options can be passed in via the build parameters at launch time.

Note that this method of running the login tester will randomly get interrupted/aborted if running for too long. You should use an alternate method for runs taking over an hour or two. For example, running locally or via a canary instance are good options.