# ufiber-client-4
This is a quick dirty project built to provide a quick dirty client for Ubiquiti UFiber OLTs, using firmware version 4.x

More info about what am I doing this is on the following entries:

- https://arturobaldo.com.ar/ufiber-olt-api/
- https://arturobaldo.com.ar/digging-into-ubiquitis-ufiber-olt/

## olt.py
This is the core of the project. It uses the OLTCLient class to provide a middleware between you and the HTTP interface of the olt.

Initialize a new OLTClient instance with:

`# client = OLTClient(host='192.168.1.1', username='ubnt', password='ubnt', debug_level=logging.DEBUG)`

Required params are only host, and credentials.

The initialization will handle the login for you, altough you can call the `login()` method manually.

If the OLT is network reacheable, and you have provided the right credentials, and the OLT GUI is alive and well, you should be ready to start.

## What changes on v4
Well, UBNT got rid of the GPON profiles. :(

This software is intented to give you an alternative by keeping profiles as JSON in the ./profiles folder.

You can copy the `template.json` file and make your way using it as a starting point. It should be self descriptive.
There is an `schema.json` which validates your profile before pushing changes into the OLT.

## How to help
It would be awesome to have docs :D

Are you a pydoc master? Let'a add docstrings

Do you have an OLT for us to test? Ping me and we can set up a VPN.

### 
