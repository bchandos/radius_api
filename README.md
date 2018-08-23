# Radius CRM Web Services Wrapper

This package is a Python 3.6+ wrapper for the Radius CRM web services API. It instantiates most methods of the web services across all modules, including ExportFilters task creation, execution and results response. Currently missing methods: Enhanced Search for Entities; Test Scores; Create a Custom Field
### Class RadiusInstance
The RadiusInstance class accepts your Radius Web Services username and password, as well as the url of your server, provided in the Radius Web Services documentation. It creates the needed HTTPDigest authentication object that will be passed with all transactions. It also exposes all available Modules in your tenant via `all_modules`.