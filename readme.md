# IBM Spectrum Virtualize Python Client

This repository contains the IBM Command-line Interface (CLI) Python client, which establishes terminal connection with IBM Spectrum Virtualize storage systems. The Python client protocol enables full management and monitoring of these storage arrays by issuing dedicated command-line interface (CLI) commands.

## Getting started

Clone the repository, and then add it to your PYTHONPATH directory. The Python client is then ready for import and use.

## Usage examples

Usage examples of the Python client are available in the **examples.py** file.

## Displaying the command-line reference information

Each storage system and major software version has its own set of CLI commands. The commands are detailed in the CLI reference guides that are available on IBM Knowledge Center (KC).

To display the full CLI Reference Guide of a specific storage system and a specific software version:

1.	Navigate to a storage system welcome page on KC:

IBM SAN Volume Controller on IBM Knowledge Center: http://www.ibm.com/support/knowledgecenter/STPVGU

IBM Storwize V3500 on IBM Knowledge Center: http://ibm.com/support/knowledgecenter/STLM6B

IBM Storwize V3700 on IBM Knowledge Center: http://ibm.com/support/knowledgecenter/STLM5A

IBM Storwize V5000 on IBM Knowledge Center: http://ibm.com/support/knowledgecenter/STHGUJ

IBM Storwize V7000 on IBM Knowledge Center: http://ibm.com/support/knowledgecenter/ST3FR7

IBM Storwize V7000 Unified on IBM Knowledge Center: http://ibm.com/support/knowledgecenter/ST5Q4U

IBM FlashSystem V9000 on IBM Knowledge Center: http://ibm.com/support/knowledgecenter/STKMQV

2. On the welcome page, select a storage system software version. For example, select **Version 8.2.1**.

![Software version](https://github.com/IBM/pysvc/blob/master/docs/images/1.jpg)

The welcome page of the selected software version is displayed.

3. If needed, select the **Table of contents** tab.

![Table of contents](https://github.com/IBM/pysvc/blob/master/docs/images/2.jpg)

4. On the table of contents, click **Command-line interface**.

![CLI interface](https://github.com/IBM/pysvc/blob/master/docs/images/3.jpg)

5.	Refer to **Host commands** and to all subsequent chapters.

## Contributing
We do not accept any contributions at the moment. This may change in the future, so you can fork, clone, and suggest a pull request.

## Running tests
Use nosetests command to run a test.

    nosetests -v
