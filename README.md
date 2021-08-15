# Radius CRM Web Services Wrapper

**Note**: This project is no longer under active development because I no longer have access to a Radius instance. If you use Radius and would like to request features, updates, or custom solutions, please contact me via [my personal webpage](https://billchandos.dev).

This package is a Python 3.6+ wrapper for the Radius CRM web services API. It instantiates most methods of the web services across all modules, including ExportFilters task creation, execution and results response. Currently missing methods: Enhanced Search for Entities; Test Scores; Create a Custom Field
## Class RadiusInstance
The RadiusInstance class accepts your Radius Web Services username and password, as well as the url of your server, provided in the Radius Web Services documentation. It creates the needed HTTPDigest authentication object that will be passed with all transactions. It also exposes all available Modules in your tenant via `all_modules`.
### Methods
#### `create_entity`
 Create an entity within a specific module. Accepts a JSON object consisting of createFields and, optionally, returnFields. Returns an entity ID, or other requested fields.
 #### `create_request_object`
 Creates a dictionary to send in POST and PUT requests (as JSON) to the web service. Requires module to verify fields exist. If strict is True, will raise Exception if any field cannot be found. Otherwise, will silently drop fields from request. If field has Possible Values attribute, will check submitted value against list.
 *Note: web services spec encourages the use of Field IDs in requests for consistency. An entity search using Field IDs will return Field IDs, which are less clear and not useful without lookup functionality. This may be a future functionality.*
 #### `delete_entity`
Deletes an entity within a specific module. Accepts an entity ID, and returns a status and message.
 #### `export_filter_create_task`
 Creates a task to execute an Export Filter. Accepts the Export Filter ID.
 #### `get_active_export_filters`
 Returns all active Export Filters in the Radius instance.
 #### `get_all_fields`
 Returns all the fields of a particular module as a list. Provides all field details when details=True.
 #### `get_entity`
 Given an entity id number and module, will return that entity. Specific fields can be provided as a comma-separated list. Default will return all fields.
 #### `get_export_filter_as_file`
 Generates a CSV file from export filter results. Although Radius Web Services can return file contents natively, it returns a corrupted ZIP file that cannot be handled in software.
 #### `get_export_filter_as_list`
 Returns the export filter results as a list of dictionaries.
 #### `get_export_filter_id_by_name`
 Searches for an Export Filter by name and returns either the Export Filter ID, or an Exception if not found.
 #### `get_export_filter_by_name_as_list`
 This helper function combines a few web service calls to retrieve a named Export filter as a list.
 #### `get_metadata`
 Returns all metadata about a Radius module.
 #### `search_for_entities`
 Performs a search on a specific module. Accepts a JSON object consisting of `searchFields` and, optionally, returnFields. Returns all module fields if `returnFields` is not specified. 
 *Note: currently Radius Web Services will not return all fields if any field names have a period (.) and so it is best to specify return fields explicitly.*
 #### `update_entity`
 Update an entity within a specific module. Accepts a JSON object consisting of `createFields` and, optionally, `returnFields`. Returns an entity ID, or other requested fields.