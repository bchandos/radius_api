import requests
from requests.auth import HTTPDigestAuth
import time
from datetime import date
from urllib.parse import urlencode, urlparse
import csv
from .exceptions import APIError


class RadiusInstance:
    """The RadiusInstance class is a wrapper for the Radius CRM web services.
    Provide username and password as provided by the web service, and base_url
    as listed in the web services documentation."""

    def __init__(self, user, password, base_url):
        self.base_server = base_url
        self.user = user
        url_parts = urlparse(base_url)
        self.server_url = 'https://' + url_parts.hostname + '/crm/webservice/modules/'
        self.authentication = HTTPDigestAuth(user, password)
        self.all_modules = None
        self.all_modules = self._get(
            parameters={'useSystemAndDisplayLabels': 'true'})

    def __repr__(self):
        return '<Instance of Radius Web Service on %s, as user: %s>' % (self.base_server, self.user)

    def _get_module_name(self, module):
        """Checks for a module name in all_modules and returns the official name."""
        for m in self.all_modules:
            if m['module name'] == module or m['module display name'] == module:
                return m['module name']
        raise APIError('Module <%s> does not exist in instance.' % module)

    def _get(self, module=None, url_append='', parameters=None):
        """Processes HTTP GET request to the Radius Web Service and returns
        the payload or Exception."""
        if self.all_modules:
            u = self.server_url + \
                self._get_module_name(module) + '/' + url_append
        else:
            u = self.server_url
        r = requests.get(u, auth=self.authentication, params=parameters)
        # An HTTP request can return many unexpected things, depending on the inputs, network status, etc.
        # For the purposes of this API, we want to return the payload, if it exists, or an APIError that
        # is as descriptive as possible. In the case that the server response is not OK, and does not
        # return JSON that might tell us why, we fall back on requests.raise_from_status().
        if r.ok:
            try:
                return r.json()['payload']
            except KeyError:
                raise APIError(
                    'JSON returned from %s, but does not contain expected payload.' % r.url)
            except TypeError:
                raise APIError(
                    'Response OK, but no JSON returned from %s' % r.url)
        elif not r.ok:
            status_code = r.status_code
            try:
                status = r.json()['status']
                error_message = (
                    r.json()['payload']['Error Message'] if module == 'ExportFilters' else r.json()['message'])
            except KeyError:
                raise APIError('Status not OK <%s> and JSON returned from %s, but does not contain expected payload.' % (
                    status_code, r.url))
            except TypeError:
                raise APIError(
                    'Status not OK <%s> and no JSON returned from %s' % (status_code, r.url))
            else:
                raise APIError('HTTP Response Code: %s; API Response Status: %s; Error Message: %s' % (
                    status_code, status, error_message))
        else:
            raise r.raise_for_status()

    def _post(self, module, payload, url_append='', parameters=None):
        """Processes HTTP POST request to the Radius Web Service and returns
        the payload or Exception."""
        p = (parameters if parameters else '')
        u = self.server_url + \
            self._get_module_name(module) + '/' + \
            url_append + '?' + urlencode(p)
        r = requests.post(u, auth=self.authentication, json=payload)
        if r.json()['status'] == 'ok':
            return r.json()['payload']
        else:
            status_code = r.status_code
            status = r.json()['status']
            error_message = (r.json()['payload']['Error Message']
                             if module == 'ExportFilters' else r.json()['message'])
            raise APIError('Error in server response, status not ok. Code: %s; Status: %s; Error Message: %s' % (
                status_code, status, error_message))

    def _put(self, module, payload, url_append='', parameters=None):
        """Processes HTTP PUT request to the Radius Web Service and returns
        the payload or Exception."""
        u = self.server_url + self._get_module_name(module) + '/' + url_append
        if parameters:
            u += '?' + urlencode(parameters)
        r = requests.put(u, auth=self.authentication, json=payload)
        if r.json()['status'] == 'ok':
            return r.json()['payload']
        else:
            status_code = r.status_code
            status = r.json()['status']
            error_message = (r.json()['payload']['Error Message']
                             if module == 'ExportFilters' else r.json()['message'])
            raise APIError('Error in server response, status not ok. Code: %s; Status: %s; Error Message: %s' % (
                status_code, status, error_message))

    def _delete(self, module, url_append='', parameters=None):
        """Processes HTTP DELETE request to the Radius Web Service and returns
        the server response."""
        u = self.server_url + self._get_module_name(module) + '/' + url_append
        if parameters:
            u += '?' + urlencode(parameters)
        r = requests.delete(u, auth=self.authentication)
        return r.text

    def get_all_fields(self, module, details=False):
        """Returns all the fields of a particular module as a list. Provides
        all field details when details=True.

        :param module: the name of the Radius module
        :param details: whether to return full field details, default=False
        :type module: str
        :type details: bool
        :returns: all fields within specified module, with or without details
        :rtype: dict
        """
        p = None
        if details:
            p = {'includeDetails': 'true'}
        return self._get(module=module, url_append='fields', parameters=p)

    def get_metadata(self, module):
        """Returns all metadata about a Radius module.

        :param module: the name of the Radius module
        :type module: str
        :returns: module metadata
        :rtype: dict
        """
        return self._get(module=module)

    def get_entity(self, module, entity_id, return_fields=None):
        """Given an entity id number and module, will return that entity.
        Specific fields can be provided as a comma-separated list.
        Default will return all fields.

        :param module: the name of the Radius module
        :param entity_id: the id number of the Radius entity
        :param return_fields: module fields to return, default=None which returns all fields
        :type module: str
        :type entity_id: int, str
        :type return_fields: list
        :returns: Provided fields for Radius entity, or all fields
        :rtype: dict
        """
        if return_fields:
            p = {'returnFields': ','.join(return_fields)}
        else:
            p = None
        return self._get(module=module, url_append=str(entity_id), parameters=p)

    def create_entity(self, module, request_body):
        """Create an entity within a specific module. Accepts a JSON object
        consisting of createFields and, optionally, returnFields. Returns an
        entity ID, or other requested fields.

        :param module: the name of the Radius module
        :param request_body: the structured Radius request
        :type module: str
        :type request_body: dict
        :returns: Radius entity id of created object
        :rtype: dict

        .. note:: use ``create_request_object`` to generate the request_body
        """
        if 'createFields' in request_body.keys():
            return self._post(module=module, payload=request_body)['entity']

    def update_entity(self, module, entity_id, request_body):
        """Update an entity within a specific module. Accepts a JSON object
        consisting of createFields and, optionally, returnFields. Returns an
        entity ID, or other requested fields.

        :param module: the name of the Radius module
        :param entity_id: the id number of the Radius entity
        :param request_body: the structured Radius request
        :type module: str
        :type request_body: dict
        :type entity_id: int, str
        :returns: Radius entity id of created object
        :rtype: dict

        .. note:: use ``create_request_object`` to generate the request_body
        """
        if self._get_module_name(module) == 'Registrations' and (
            'Participant' not in request_body['createFields'].keys() or
                'Iteration Name' not in request_body['createFields'].keys()):
            # Per web services documentation, all Registrations updates must include
            # Participant and Iteration Name fields in the payload. Server returns
            # NullPointerException when it's not included. Participant is the Contact
            # Entity ID, and Iteration Name is also an ID number. Both are available in
            # the Registration passed via entity_id.
            registration = self.get_entity('Registrations', entity_id, return_fields=[
                                           'Participant', 'Iteration Name'])
            request_body['createFields']['Participant'] = registration['entity']['Participant']
            request_body['createFields']['Iteration Name'] = registration['entity']['Iteration Name']
        return self._put(module=module, url_append=str(entity_id), payload=request_body)

    def delete_entity(self, module, entity_id):
        """Deletes an entity within a specific module. Accepts an entity ID,
        and returns a status and message.

        :param module: the name of the Radius module
        :param entity_id: the id number of the Radius entity
        :type module: str
        :type entity_id: int, str
        :returns: deletion confirmation message
        :rtype: str
        """
        return self._delete(module=module, url_append=str(entity_id))

    def search_for_entities(self, module, request_body):
        """Performs a search on a specific module. Accepts a JSON object
        consisting of searchFields and, optionally, returnFields. Returns
        all module fields if returnFields is not specified. Note: currently
        Radius Web Services will not return all fields if any field names have
        a period (.) and so it is best to specify return fields.

        :param module: the name of the Radius module
        :param request_body: the structured Radius request
        :type module: str
        :type request_body: dict
        :returns: List of matching entities, with requested fields or all fields
        :rtype: list

        .. note:: use ``create_request_object`` to generate the request_body
        .. note:: provide ``return_fields`` parameter to ``create_request_object``
                  to avoid issues with Radius Web Services and field names with '.'
        """
        e = self._post(module=module, url_append='search',
                       payload=request_body)
        if e['total pages'] == 0 or e['total pages'] == 1:
            return e['entities']
        else:
            all_entities = e['entities']
            pages = e['total pages']
            query_id = e['queryId']
            for page in range(2, pages + 1):
                p = {'page': page, 'queryId': query_id}
                e = self._post(module=module, url_append='search',
                               payload=request_body, parameters=p)
                all_entities.extend(e['entities'])
            return all_entities

    def export_filter_create_task(self, filter_id):
        """Creates a task to execute an Export Filter. Accepts
        the Export Filter ID.

        :param filter_id: the id of the Radius Export Filter
        :type filter_id: int, str
        :returns: execution task ID
        :rtype: str
        """
        t = self._post(module='ExportFilters',
                       url_append='createExecutionTask/' + str(filter_id), payload=None)
        return t['Execution Task ID']

    def get_export_filter_as_file(self, task_id, filename):
        """Generates a CSV file from export filter results. Although Radius
        Web Services can return file contents natively, it returns a corrupted
        ZIP file that cannot be handled in software.

        :param task_id: the execution task ID returned by ``export_filter_create_task``
        :param filename: the target filename for the CSV-formatted results
        :type task_id: str
        :type filename: str
        :returns: nothing
        """
        export_filter_as_list = self.get_export_filter_as_list(task_id)
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = list(export_filter_as_list[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for entry in export_filter_as_list:
                writer.writerow(entry)

    def get_export_filter_as_list(self, task_id, checks=3):
        """Returns the export filter results as a list of dictionaries.

        :param task_id: the execution task ID returned by ``export_filter_create_task``
        :param checks: number of 2-second waits between checks, default=3
        :type task_id: str
        :type checks: int
        :returns: Export Filter results as a list of dictionaries
        :rtype: list

        :raises APIError: when execution task times out
        """
        f = self._get(module='ExportFilters',
                      url_append='getExecutionTask/' + task_id)
        if f['Execution Task Status'] != 'Finished':
            for _ in range(checks):
                time.sleep(2)
                f = self._get(module='ExportFilters',
                              url_append='getExecutionTask/' + task_id)
                if f['Execution Task Status'] == 'Finished':
                    break
            else:
                raise APIError('Task timed out after %s seconds. Status returned as %s' %
                               (checks * 2, f['Execution Task Status']))
        if f['Total Records'] == 0:
            return []
        t = self._get(module='ExportFilters',
                      url_append='getExecutionTaskResult/' + task_id)
        results_as_list = t['entities']
        pages = t['total pages']
        query_id = t['queryId']
        # make additional requests only if necessary
        if pages > 1:
            for page in range(2, pages + 1):
                p = {'page': page, 'queryId': query_id}
                t = self._get(
                    module='ExportFilters', url_append='getExecutionTaskResult/' + task_id, parameters=p)
                results_as_list.extend(t['entities'])
        return results_as_list

    def get_active_export_filters(self):
        """Returns all active Export Filters in the Radius instance.

        :returns: list of active Export Filters
        :rtype: list
        """
        search_object = self.create_request_object(
            'ExportFilters', {'Status': 'Active'},
            request_type='search',
            return_fields=[
                'Filter Name', 'Description',
                'Primary Module', 'Entity ID'])
        return self.search_for_entities('ExportFilters', search_object)

    def get_export_filter_id_by_name(self, export_filter_name):
        """Searches for an Export Filter by name and returns either
        the Export Filter ID, or an Exception if not found.

        :param export_filter_name: the exact name of the Export Filter
        :type export_filter_name: str
        :returns: entity ID of the export filter
        :rtype: str

        :raises APIError: when matching Export Filter is not found
        """
        search_object = self.create_request_object(
            'ExportFilters', {'Filter Name': export_filter_name},
            request_type='search', return_fields=['Entity ID'])
        filter_id = self.search_for_entities('ExportFilters', search_object)
        if filter_id:
            return filter_id[0]['Entity ID']
        else:
            raise APIError('Export Filter <%s> not found.' %
                           export_filter_name)

    def get_export_filter_by_name_as_list(self, export_filter_name, checks=None):
        """This helper function combines a few web service calls to
        retrieve a named Export filter as a list.

        :param export_filter_name: the exact name of the Export Filter
        :param checks: number of 2-second waits between checks to pass to `get_export_filter_as_list`, default=None
        :type export_filter_name: str
        :type checks: int
        :returns: Export Filter results as a list of dictionaries
        :rtype: list
        """
        filter_id = self.get_export_filter_id_by_name(export_filter_name)
        task_id = self.export_filter_create_task(filter_id)
        if checks:
            return self.get_export_filter_as_list(task_id, checks=checks)
        else:
            return self.get_export_filter_as_list(task_id)

    def create_request_object(self, module, fields, request_type='search', return_fields=None, strict=False):
        """Creates a dictionary to send in POST and PUT requests (as JSON) to the web service.
        Requires module to verify fields exist. If strict is True, will
        raise Exception if any field cannot be found. Otherwise, will silently
        drop fields from request. If field has Possible Values attribute, will
        check submitted value against list.

        :param module: the name of the Radius module
        :param fields: a dictionary of field name and value pairs
        :param request_type: what type of request object to create: search, update, or create. Default='search' 
        :param return_fields: a list of fields to return, default=None which returns all fields for search, or Entity ID for others
        :param strict: indicates if invalid field names should be dropped silently, or raise an exception. Default=False
        :type module: str
        :type fields: dict
        :type request_type: str
        :type return_fields: list
        :type strict: bool

        :raises APIError: in strict mode, if any field cannot be found
        :raises APIError: if field not in Possible Values attribute (e.g. Multi-Select field type)

        ..note:: web services spec encourages the use of Field IDs in requests for consistency.
        An entity search using Field IDs will return Field IDs, which are less clear
        and not useful without lookup functionality. This may be a future functionality.
        """

        all_fields = self.get_all_fields(module, details=True)
        checked_fields = dict()
        checked_returns = list()
        if not return_fields:
            return_fields = list()
        if request_type == 'create' or request_type == 'update':
            field_name = 'createFields'
        else:
            field_name = 'searchFields'
        for field in fields.keys():
            positive_id = False
            for a in all_fields:
                if 'Display Label' in all_fields[a].keys():
                    if field == a or field == all_fields[a]['Display Label']:
                        if 'Possible Values' in all_fields[a].keys():
                            # multi-select field must be list type or web service will return error
                            if all_fields[a]['Data Type'] == 'Multi-Select' and type(fields[field]) != list:
                                fields[field] = [fields[field]]
                            # to allow for multi-select list checking, convert single values to list
                            # and use set mebership to test they are in possible values
                            v = fields[field] if type(fields[field]) == list else [
                                fields[field]]
                            if set(v) <= set(all_fields[a]['Possible Values']):
                                checked_fields[a] = fields[field]
                                positive_id = True
                            else:
                                raise APIError('Field value(s) <%s> not found in possible values for field <%s>.' % (
                                    fields[field], field))
                        elif field_name == 'searchFields' and all_fields[a]['Data Type'] == 'Date':
                            # all displayed and returned dates are in format mm/dd/YYYY
                            # web service expects dates in ISO format (YYYY-mm-dd)
                            # but only when searching. we will convert.
                            d = fields[field]
                            parts = list(map(int, d.split('/')))
                            checked_fields[a] = date(
                                month=parts[0], day=parts[1], year=parts[2]).isoformat()
                            positive_id = True
                        else:
                            checked_fields[a] = fields[field]
                            positive_id = True
                elif field == 'Entity ID':
                    checked_fields['Entity ID'] = fields[field]
                    positive_id = True
            if not positive_id and strict:
                raise APIError(
                    'Field name <%s> not found in module <%s>.' % (field, module))

        for rf in return_fields:
            positive_id = False
            for a in all_fields:
                if 'Display Label' in all_fields[a].keys():
                    if rf == a or rf == all_fields[a]['Display Label']:
                        checked_returns.append(rf)
                        positive_id = True
                elif rf == 'Entity ID':
                    checked_returns.append('Entity ID')
                    positive_id = True
            if not positive_id and strict:
                raise APIError(
                    'Field name <%s> not found in module <%s>.' % (field, module))
        request_object = {field_name: checked_fields}
        if checked_returns:
            request_object['returnFields'] = checked_returns
        return request_object
