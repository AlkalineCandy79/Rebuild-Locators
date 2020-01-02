#-------------------------------------------------------------------------------
# Name:        LIS Locator Rebuild
# Purpose:  This scripts is designed to run a very simple set of instruction to
#           automatically rebuild our locator nightly when it is not in use.  The
#           script is designed to send a error message when it encounters a problem.
#           Full details of the error are included in the message.
#
# Author:      John Spence
#
# Created:     4/19/2019
# Modified:    10/2/2019
# Modification Purpose:  Script was adjusted to support shutting down of services
#                        on ArcGIS Server along with working with multiple locators
#                        located in different locations on different servers.
#
#
#-------------------------------------------------------------------------------

# 888888888888888888888888888888888888888888888888888888888888888888888888888888
# ------------------------------- Configuration --------------------------------
# Pretty simple setup.  Just change your settings/configuration below.  Do not
# go below the "DO NOT UPDATE...." line.
#
# 888888888888888888888888888888888888888888888888888888888888888888888888888888

# Configuration File - Contact GISSysAdmin to update if new locator needed, etc.
config_file = r'C:\Users\GISSysAdmin\Desktop\AppConfig\locator_rebuild.ini'

# ------------------------------------------------------------------------------
# DO NOT UPDATE BELOW THIS LINE OR RISK DOOM AND DISPAIR!  Have a nice day!
# ------------------------------------------------------------------------------

# Import Python libraries
import arcpy, time, smtplib, string, re, base64, httplib, urllib, urllib2, json, ssl, sys
from ConfigParser import ConfigParser


def sendmailmsg_svc(email_target_svc, svc_status, mail_server, mail_from):

    server = smtplib.SMTP(mail_server)

    if svc_status > 0:
        mail_priority = '1'
        mail_subject = 'WARNING! Locator Services Stopping in 15 minutes'
        mail_msg = ('Locator services for the City of Bellueve will shut down in 15 minutes.  Services will be' +
        ' restored after updates are complete.\n\n[SYSTEM AUTO GENERATED MESSAGE]')
    else:
        mail_priority = '5'
        mail_subject = 'SUCCESS! Locator Services Available'
        mail_msg = ('Locator services for the City of Bellueve are available now.' +
        '\n\n[SYSTEM AUTO GENERATED MESSAGE]')

    temp_mail = ''

    for email in email_target_svc:
        email = email + ', '
        temp_mail = temp_mail + email

    temp_mail = temp_mail[:-2]

    email_target_svc = temp_mail

    send_mail = 'To: {0}\nFrom: {1}\nX-Priority: {2}\nSubject: {3}\n\n{4}'.format(email_target_svc, mail_from, mail_priority, mail_subject, mail_msg)

    print "Sending message to recipients."

    server.sendmail(mail_from, email_target_svc, send_mail)
    server.quit()

def sendmailmsg(email_target, error_count, error_message, mail_server, mail_from):

    server = smtplib.SMTP(mail_server)

    if error_count > 0:
        mail_priority = '1'
        mail_subject = 'WARNING! COB Locator Rebuild Failed'
        mail_msg = ('Locators for the City of Bellueve have failed. Results are as follows:\n\n' +
        'Error Message As Follows: \n{0}'.format(error_message) +
        '\n\n[SYSTEM AUTO GENERATED MESSAGE]')
    else:
        mail_priority = '5'
        mail_subject = 'SUCCESS! COB Locator Rebuild Completed'
        mail_msg = ('Locator for the City of Bellueve has successfully been rebuilt. \n' +
        '{0}'.format(error_message) +
        '\n\n[SYSTEM AUTO GENERATED MESSAGE]')

    temp_mail = ''

    for email in email_target:
        email = email + ', '
        temp_mail = temp_mail + email

    temp_mail = temp_mail[:-2]

    email_target = temp_mail

    send_mail = 'To: {0}\nFrom: {1}\nX-Priority: {2}\nSubject: {3}\n\n{4}'.format(email_target, mail_from, mail_priority, mail_subject, mail_msg)

    print ('Sending message to recipients.')

    server.sendmail(mail_from, email_target, send_mail)
    server.quit()

def rebuild_locator (locator_loc):

    # Define Global Variables
    global error_count
    global error_message

    # Set Variables
    error_message = ''
    error_count = 0

    for locator in locator_loc:

        # Begin rebuild process.  On error set conditions for e-mail.
        try:
            arcpy.RebuildAddressLocator_geocoding(in_address_locator=locator)
            error_count = 0
            error_message = 'Locator Rebuild Success:  {0} \n'.format(locator)
        except Exception as error_check:
            print ('Status:  Failure to rebuild!')
            error_message = 'Locator Rebuild Failure:  {0} \n{1}'.format(locator, error_check.args[0])
            print (error_message)
            error_count += 1

        sendmailmsg(email_target, error_count, error_message, mail_server, mail_from)

    return ()

def read_config (config_file):

    # Define Global Variables
    global username
    global password
    global locator_loc
    global server_name
    global service_folder
    global mail_server
    global mail_from
    global email_target
    global email_target_svc
    global server_port
    global server_fqdn_suff
    global service_folder

    # Set Variables
    error_message = ''
    error_count = 0

    # Begin rebuild process.  On error set conditions for e-mail.
    try:
        config = ConfigParser()
        config.read(config_file)

        # Pull settings from configuration file
        # Only 1 user name and password can be present
        username = config.get ('config', 'username')
        password = config.get ('config', 'password')
        password = base64.b64decode(password)

        locator_loc = config.get ('config', 'locator_loc')
        # Split for multiple if present
        locator_loc = locator_loc.split(', ')

        server_name = config.get('servers', 'server_name')
        # Split for multiple if present
        server_name = server_name.split(', ')

        server_port = config.get('servers', 'server_port')

        server_fqdn_suff = config.get('servers', 'server_fqdn_suff')

        service_folder = config.get('service_collection', 'service_folder')
        # Split for multiple if present
        service_folder = service_folder.split(', ')

        mail_server = config.get ('email_configuration', 'mail_server')
        mail_from = config.get ('email_configuration', 'mail_from')

        email_target = config.get ('email_configuration', 'email_target')
        # Split for multiple if present
        email_target = email_target.split(', ')

        email_target_svc  = config.get ('email_configuration', 'email_target_svc')
        # Split for multiple if present
        email_target_svc  = email_target_svc .split(', ')

    except Exception as error_check:
        print "Status:  Failure to read configuration file!"
        error_message = '{0}'.format(error_check.args[0])
        print error_message
        error_count += 1

    return

def kill_services(username, password, server_name, server_port, server_fqdn_suff, service_folder, process):

#Roll through the various servers and execute tasks.

    for server in server_name:
        serverName = server + '.' + server_fqdn_suff
        serverPort = server_port

        #Snag me a token and get to work.
        try:
            token = getToken(username, password, serverName, serverPort)
        except:
            print ('Could not generate a token with the username and password provided.')

        for folder in service_folder:

            if str.upper(folder) == 'ROOT':
                folder = ''
            else:
                folder += '/'

            folderURL = "/arcgis/admin/services/" + folder

            # This request only needs the token and the response formatting parameter
            params = urllib.urlencode({'token': token, 'f': 'json'})

            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

            # Connect to URL and post parameters
            if serverPort == '6443':
                print ('SSL Required Connection')
                ssl_context = ssl.create_default_context()
                try:
                    httpConn = httplib.HTTPSConnection(serverName, serverPort, context=ssl_context)
                except:
                    httpConn = httplib.HTTPSConnection(serverName, serverPort, context=ssl._create_unverified_context())
            else:
                print ('Non-SSL Required Connection')
                httpConn = httplib.HTTPConnection(serverName, serverPort)

            httpConn.request("POST", folderURL, params, headers)

            # Read response
            response = httpConn.getresponse()
            if (response.status != 200):
                httpConn.close()
                print "Could not read folder information."
                return
            else:
                data = response.read()

                # Check that data returned is not an error object
                if not assertJsonSuccess(data):
                    print "Error when reading folder information. " + str(data)
                else:
                    print "Processed folder information successfully. Now processing services..."

                # Deserialize response into Python object
                dataObj = json.loads(data)
                httpConn.close()

                # Loop through each service in the folder and stop or start it
                for item in dataObj['services']:

                    fullSvcName = item['serviceName'] + "." + item['type']

                    # Construct URL to stop or start service, then make the request
                    stopOrStartURL = "/arcgis/admin/services/" + folder + fullSvcName + "/" + process
                    httpConn.request("POST", stopOrStartURL, params, headers)

                    # Read stop or start response
                    stopStartResponse = httpConn.getresponse()
                    if (stopStartResponse.status != 200):
                        httpConn.close()
                        print "Error while executing stop or start. Please check the URL and try again."
                        return
                    else:
                        stopStartData = stopStartResponse.read()

                        # Check that data returned is not an error object
                        if not assertJsonSuccess(stopStartData):
                            if str.upper(process) == "START":
                                print "Error returned when starting service " + fullSvcName + "."
                            else:
                                print "Error returned when stopping service " + fullSvcName + "."

                            print str(stopStartData)

                        else:
                            print "Service " + fullSvcName + " processed successfully."

                    httpConn.close()

    return

def getToken(username, password, serverName, serverPort):
    # Token URL is typically http://server + FQDN if HTTPS[:port]/arcgis/admin/generateToken
    tokenURL = "/arcgis/admin/generateToken"

    params = urllib.urlencode({'username': username, 'password': password, 'client': 'requestip', 'f': 'json'})

    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

    # Connect to URL and post parameters
    if serverPort == '6443':
        print serverName, serverPort
        ssl_context = ssl.create_default_context()
        try:
            httpConn = httplib.HTTPSConnection(serverName, serverPort, context=ssl_context)
        except:
            httpConn = httplib.HTTPSConnection(serverName, serverPort, context=ssl._create_unverified_context())
    else:
        print serverName, serverPort
        httpConn = httplib.HTTPConnection(serverName, serverPort)

    httpConn.request("POST", tokenURL, params, headers)

    # Read response
    response = httpConn.getresponse()
    if (response.status != 200):
        httpConn.close()
        print ('Error while fetching tokens.')
        return
    else:
        data = response.read()
        print data
        httpConn.close()

        # Check that data returned is not an error object
        if not assertJsonSuccess(data):
            return

        # Extract the token from it
        token = json.loads(data)
        return token['token']

# A function that checks that the input JSON object
#  is not an error object.
def assertJsonSuccess(data):
    obj = json.loads(data)
    if 'status' in obj and obj['status'] == "error":
        print "Error: JSON object returns an error. " + str(obj)
        return False
    else:
        return True


# ------ Main ------

# Read configuration file
read_config (config_file)

# Send warning message about stopping locator services
svc_status = 1
sendmailmsg_svc(email_target_svc, svc_status, mail_server, mail_from)

# Pause until ready to kill services.
time.sleep(900) #seconds  **900 for 15 minutes

# Stop all locator services (interative)
process = 'STOP'
kill_services(username, password, server_name, server_port, server_fqdn_suff, service_folder, process)

# Rebuild Locator
rebuild_locator (locator_loc)

# Start all locator services (interative)
process = 'START'
kill_services(username, password, server_name, server_port, server_fqdn_suff, service_folder, process)

# Send message about locator services restarted
svc_status = 0
sendmailmsg_svc(email_target_svc, svc_status, mail_server, mail_from)




