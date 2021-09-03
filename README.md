# ark_alfresco_setup

The purpose of the container app is to run the python code to create the required Alfresco sites, folders, categories, and memberships in order for ArkCase to work with Alfresco. 
This script uses the Alfresco REST API for all communication and API interaction.
The script relies on environment variables to identify the groups, sites, folder names, and categories to be created. 
The script is idempotent meaning that it can be re-run multiple times without failing or having adverse affects on Alfresco. If the resource already existing, it simply ignores it.
