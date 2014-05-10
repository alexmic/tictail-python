"""
tictail.resource.base
~~~~~~~~~~~~~~~~~~~~~

Definitions for `Resource` and `Collection` with their corresponding capability
mixins.

"""

class ApiObject(object):
    def __init__(self, transport, parent=None):
        """Initializes the base `ApiObject` class.

        :param transport: An instance of the transport strategy.

        """
        self.transport = transport

    @property
    def attr_name(self):
        """Returns a string used when attaching this `ApiObject` as a property
        on another object.

        """
        return self.__class__.__name__.lower()

    def _remove_slashes(self, url):
        """Removes leading and trailing slashes from the url `fragment`.

        :param url: A url string.

        """
        if not url:
            return url
        start = 1 if url[0] == '/' else None
        end = -1 if url[-1] == '/' else None
        return url[start:end]

    def request(self, method, uri, **kwargs):
        """Performs an HTTP request using the underlying transport.

        :param method: The HTTP method.
        :param uri: The resource uri.
        :param kwargs: Pass-through parameters to the transport method.

        """
        method = method.lower()
        http_method = getattr(self.transport, method)
        return http_method(uri, **kwargs)


# =================
# Basic API objects
# =================


class Resource(ApiObject):
    """Describes an API resource."""

    # A set of attributes that should not be included in this instance's data.
    # Note: `transport` is inherited from `ApiObject`.
    _internal_attrs = set([
        'transport',
        'parent',
        'subresources',
        'identifier',
        '_data_keys',
        'singleton',
        'endpoint'
    ])

    # A list of `Resource` objects, that will be instantiated as subresources.
    subresources = []

    # The name of the primary key for this instance.
    identifier = 'id'

    # The endpoint of this resource.
    endpoint = None

    # Marks this resource as singleton. A singleton resource can be fetched
    # without a primary key e.g /stores/1/theme.
    singleton = False

    def __init__(self, transport, data=None, parent=None):
        """Initializes this resource.

        :param transport: An instance of the transport strategy.
        :param data: A optional dict of data for this resource.
        :param parent: An optional parent prefix to be attached to this
        resource's uri.

        """
        self._data_keys = set()
        self.parent = parent

        super(Resource, self).__init__(transport)

        if data is None:
            data = {}

        for k, v in data.iteritems():
            setattr(self, k, v)

        self.instantiate_subresources()

    def __setattr__(self, k, v):
        super(Resource, self).__setattr__(k, v)
        if k not in self._internal_attrs:
            self._data_keys.add(k)

    @property
    def pk(self):
        identifier = self.identifier
        if not hasattr(self, identifier):
            raise ValueError(
                "This instance does not have a property '{0}' for primary key."
                .format(identifier)
            )
        return getattr(self, identifier)

    @property
    def uri(self):
        uri = ''

        if self.parent:
            parent = self._remove_slashes(self.parent)
            uri += "/{0}".format(parent)

        uri += "/{0}".format(self.endpoint)

        if not self.singleton:
            uri += "/{0}".format(self.pk)

        return uri

    def instantiate_subresources(self):
        """Instantiates all subresources which are attached as properties."""
        for sub in self.subresources:
            inst = sub(self.transport, parent=self.uri)
            self._internal_attrs.add(inst.attr_name)
            setattr(self, inst.attr_name, inst)

    def instantiate_from_data(self, data):
        """Returns an instance of this `Resource` with the given `data`.

        :param data: A data dictionary.

        """
        return self.__class__(self.transport, data=data, parent=self.parent)

    def data_keys(self):
        return list(self._data_keys)

    def data_values(self):
        return [getattr(self, k) for k in self.data_keys()]

    def data_items(self):
        return zip(self.data_keys(), self.data_values())

    def to_dict(self):
        items = list(self.data_items())
        return dict(items)

    def __repr__(self):
        import pprint
        name = self.__class__.__name__
        return "{0}({1})".format(name, pprint.pformat(self.to_dict()))


class Collection(ApiObject):
    """Represents a collection of resources."""

    # The Resource class for this collection.
    resource = None

    def __init__(self, transport, parent=None):
        """Initializes an API collection resource.

        :param transport: An instance of the transport strategy.
        :param parent: An optional parent prefix to be attached to this
        collection's uri.

        """
        super(Collection, self).__init__(transport)
        self.parent = parent

    @property
    def uri(self):
        endpoint = self._remove_slashes(self.resource.endpoint)
        if not self.parent:
            return "/{0}".format(endpoint)
        parent = self._remove_slashes(self.parent)
        return "/{0}/{1}".format(parent, endpoint)

    def instantiate_from_data(self, data):
        """Returns an instance or list of instances of the `Resource` class for
        this collection.

        :param data: A data dictionary or a list of data dictionaries.

        """
        maker = lambda d: self.resource(self.transport, data=d, parent=self.parent)
        return map(maker, data) if isinstance(data, list) else maker(data)


# ============
# Capabilities
# ============


class Get(object):
    def get(self):
        data, _ = self.request('GET', self.uri)
        return self.instantiate_from_data(data)


class GetById(object):
    def get(self, id):
        uri = "{0}/{1}".format(self.uri, id)
        data, _ = self.request('GET', uri)
        return self.instantiate_from_data(data)


class List(object):
    def format_params(self, **params):
        return params

    def all(self, **params):
        params = self.format_params(**params)
        data, _ = self.request('GET', self.uri, params=params)
        return self.instantiate_from_data(data)


class Create(object):
    def create(self, body):
        data, _ = self.request('POST', self.uri, data=body)
        return self.instantiate_from_data(data)


class Delete(object):
    def delete(self):
        data, status = self.request('DELETE', self.uri)
        return status == 204


class DeleteById(object):
    def delete(self, id):
        uri = "{0}/{1}".format(self.uri, id)
        data, status = self.request('DELETE', uri)
        return status == 204


__all__ = [
    'ApiObject', 'Resource', 'Collection', 'Get', 'GetById', 'List', 'Create',
    'Delete', 'DeleteById'
]
