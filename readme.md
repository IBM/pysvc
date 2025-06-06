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

IBM Storwize V5000 on IBM Knowledge Center: http://ibm.com/support/knowledgecenter/STHGUJ

IBM Storwize V7000 on IBM Knowledge Center: http://ibm.com/support/knowledgecenter/ST3FR7

IBM Storwize V7000 Unified on IBM Knowledge Center: http://ibm.com/support/knowledgecenter/ST5Q4U

IBM FlashSystem V9000 on IBM Knowledge Center: http://ibm.com/support/knowledgecenter/STKMQV

2. On the welcome page, select a storage system software version.

3. If needed, expand the **Table of contents** tab.

4. On the table of contents, on the left hand side, click **Command-line interface**. (If this doesn't appear, type Command-Line interface in the filter tab.)

![CLI interface](https://github.com/IBM/pysvc/blob/master/images/3.jpg)

5.	Refer to **Host commands** and to all subsequent chapters.

## Contributing
We do not accept any contributions at the moment. This may change in the future, so you can fork, clone, and suggest a pull request.

## Running tests
Use nosetests command to run a test.

    nosetests -v
