[[_TOC_]]

# Installation
Required assets are as follows:
- ArcGIS Desktop 10.5.1+
- ArcPy 2.7 or better.  (If better, check coding to make sure it conforms to accepted syntax)
- ArcGIS Server 10.5.1 or better
- A locator

Place the rebuild_locator.py within any folder of your choice.  Place locator_rebuild.ini in any folder of your choice.  Make sure that the user who will be running the script has the capacity to gain access to the folder(s) where/when appropriate.  You can also name your files anything you want.  There is no hard fix for either.

# Configuration
Within rebuild_locator.py, at the very top adjust the config_file settings to match where you placed your config file.  Take care to keep r in front of the path if you are going to copy and paste.  r just tells Python to take it literally.

Moving on to the configuration file, locator_rebuild.ini, using a standard text editor like notepad, open the file for editing.

- [ ] Update the user name for the user account that will be used to shut down ArcGIS Server Services.
- [ ] Update the password for the user account that will be used to shut down the ArcGIS Server Services.  Take heed of how the python script calls that password around line 158.
- [ ] Update the location(s) of all the locators you want to build.  You want to include the full path + the name of the locator minus the file extension.  For example if buildings.loc is what you want to rebuild, only put buildings.  Only use a , with a space to separate the locators from one another.
- [ ] Update the server_name(s) you want to work from.  Just put the server name as you know it.  For example, without the FQDN included, COBIGISPR02 would be used vs. COBIGISPR02.ci.bellevuewa.us.
- [ ] Update the server_port.  This python script has both 6080 and 6443 hard coded as options.
- [ ] Update the server_fqdn_suff which is the suffix to add after the server name is called.  This is needed for SSL based logons.
- [ ] Update service_folder.  You may have more than one folder here too, provided you place a , and a space following it.
- [ ] Update email_configuration.
- [ ] Update email_target.  Target can be target(s) provided you put a , and space between addresses.
- [ ] Update email_target_svc.  Same applies to the original email_target, but this one specifically notifies individuals of an outage of the service.

# Running the Script
By design, this script was intended to run as a task, however, if can be run independently provided you have access to the configuration file that runs the script.

# Trouble shooting
There are only a few places where there could be a problem.

1. Check if the locator has all its files.  There has been a moment or two where a locator was missing an essential file.  We have copies of the locator on another drive if that situation happens.  Stop the services and replace if necessary.
1. Most of the errors will come from the locator being unable to get an exclusive lock for the rebuild process.  Check with NSS and release the lock if it persists beyond a few days.  For services that are used by webservices, this would an unexpected situation and you must look at the server among other things.  Contact the GTS infrastructure manager for support.
1. If the script fails to run for some reason, this may be due to a password or access issue.  Contact the GTS infrastructure manager for support.
