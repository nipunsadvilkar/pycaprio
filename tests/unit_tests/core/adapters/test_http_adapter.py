from typing import IO
from unittest.mock import Mock

import pytest

from pycaprio.core.adapters.http_adapter import HttpInceptionAdapter
from pycaprio.core.objects import Project


@pytest.mark.parametrize('route, verb, function, parameters', [
    ('/projects', 'get', HttpInceptionAdapter.projects, ()),
    ('/projects/1/documents', 'get', HttpInceptionAdapter.documents, (1,)),
    ('/projects/1/documents/1/annotations', 'get', HttpInceptionAdapter.annotations, (1, 1)),
    ('/projects/1', 'delete', HttpInceptionAdapter.delete_project, (1,)),
    ('/projects/1/documents/1', 'delete', HttpInceptionAdapter.delete_document, (1, 1)),
    ('/projects/1/documents/1/annotations/test-username', 'delete', HttpInceptionAdapter.delete_annotation,
     (1, 1, 'test-username')),
    ('/projects/1/export.zip', 'get', HttpInceptionAdapter.export_project, (1,))
])
def test_list_resources_gets_good_route(route, verb, function, parameters, mock_http_adapter: HttpInceptionAdapter):
    function(mock_http_adapter, *parameters)
    assert getattr(mock_http_adapter.client, verb).call_args[0][0] == route


@pytest.mark.parametrize('route, verb, function, parameters', [
    ('/projects', 'get', HttpInceptionAdapter.projects, ()),
    ('/projects/1/documents', 'get', HttpInceptionAdapter.documents, (1,)),
    ('/projects/1/documents/1/annotations', 'get', HttpInceptionAdapter.annotations, (1, 1))
])
def test_list_resources_returns_list(route, verb, function, parameters, mock_http_adapter: HttpInceptionAdapter):
    resource_list = function(mock_http_adapter, *parameters)
    assert isinstance(resource_list, list)


def test_import_project_good_url(mock_http_adapter: HttpInceptionAdapter, mock_io: IO, mock_http_response: Mock,
                                 serialized_project: dict):
    mock_http_response.json.return_value = {'body': serialized_project}
    mock_http_adapter.client.post.return_value = mock_http_response
    mock_http_adapter.import_project(mock_io)
    assert mock_http_adapter.client.post.call_args[0][0] == '/projects/import'


def test_import_project_returns_project(mock_http_adapter: HttpInceptionAdapter, mock_io: IO, mock_http_response: Mock,
                                        serialized_project: dict):
    mock_http_response.json.return_value = {'body': serialized_project}
    mock_http_adapter.client.post.return_value = mock_http_response
    project = mock_http_adapter.import_project(mock_io)
    assert isinstance(project, Project)


@pytest.mark.parametrize('route, function, params, resource',
                         [('/projects/1', HttpInceptionAdapter.project, (1,), 'project'),
                          ('/projects/1/documents/1', HttpInceptionAdapter.document, (1, 1), 'document'),
                          ('/projects/1/documents/1/annotations/test-user', HttpInceptionAdapter.annotation,
                           (1, 1, 'test-user'), 'annotation')])
def test_get_single_resource_route_ok(route: str, function: callable, params: tuple, resource: dict,
                                      mock_http_adapter: HttpInceptionAdapter, mock_http_response: Mock,
                                      serializations: dict):
    mock_http_response.json.return_value = {'body': serializations[resource]}
    mock_http_adapter.client.get.return_value = mock_http_response
    function(mock_http_adapter, *params)
    assert mock_http_adapter.client.get.call_args[0][0] == route


def test_get_project_returns_good_instance(mock_http_adapter: HttpInceptionAdapter, mock_http_response: Mock,
                                           serialized_project: dict):
    mock_http_response.json.return_value = {'body': serialized_project}
    mock_http_adapter.client.get.return_value = mock_http_response
    response = mock_http_adapter.project(1)
    assert isinstance(response, Project)


@pytest.mark.parametrize('function, params', [('document', (1, 1)),
                                              ('annotation', (1, 1, 'test-username'))])
def test_resource_returns_bytes(mock_http_adapter: HttpInceptionAdapter, mock_http_response: Mock, function: str,
                                params: tuple):
    mock_http_response.content = bytes()
    mock_http_adapter.client.get.return_value = mock_http_response
    response = getattr(HttpInceptionAdapter, function)(mock_http_adapter, *params)
    assert isinstance(response, bytes)


@pytest.mark.parametrize('route, function, params, resource',
                         [('/projects', HttpInceptionAdapter.create_project, ("name", "creator"), 'project'),
                          ('/projects/1/documents', HttpInceptionAdapter.create_document, (1, "test-name", None,),
                           'document'),
                          ('/projects/1/documents/1/annotations/test-user', HttpInceptionAdapter.create_annotation,
                           (1, 1, "test-user", None,), 'annotation')])
def test_resource_creation_good_route(route: str, function: callable, params: tuple, resource: str,
                                      mock_http_adapter: HttpInceptionAdapter, mock_http_response: Mock,
                                      serializations: dict):
    mock_http_response.json.return_value = {'body': serializations[resource]}
    mock_http_adapter.client.post.return_value = mock_http_response
    function(mock_http_adapter, *params)
    assert mock_http_adapter.client.post.call_args[0][0] == route


@pytest.mark.parametrize('route, function, params, resource',
                         [('/projects', HttpInceptionAdapter.create_project, ("name", "creator"), 'project'),
                          ('/projects/1/documents', HttpInceptionAdapter.create_document, (1, "test-name", None,),
                           'document'),
                          ('/projects/1/documents/1/annotations/test-user', HttpInceptionAdapter.create_annotation,
                           (1, 1, "test-user", None,), 'annotation')])
def test_resource_creation_returns_resource_instance(route: str, function: callable, params: tuple, resource: str,
                                                     mock_http_adapter: HttpInceptionAdapter, mock_http_response: Mock,
                                                     serializations: dict, deserializations: dict):
    mock_http_response.json.return_value = {'body': serializations[resource]}
    mock_http_adapter.client.post.return_value = mock_http_response
    response = function(mock_http_adapter, *params)
    assert isinstance(response, deserializations[resource].__class__)


def test_document_has_project_id_injected_document_list(mock_http_adapter: HttpInceptionAdapter,
                                                        mock_http_response: Mock, serialized_document: dict):
    test_project_id = 1
    mock_http_response.json.return_value = {'body': [serialized_document]}
    mock_http_adapter.client.get.return_value = mock_http_response
    response = mock_http_adapter.documents(test_project_id)
    assert response[0].project_id == test_project_id


def test_document_has_project_id_injected_creation(mock_http_adapter: HttpInceptionAdapter,
                                                   mock_http_response: Mock, serialized_document: dict):
    test_project_id = 1
    mock_http_response.json.return_value = {'body': serialized_document}
    mock_http_adapter.client.post.return_value = mock_http_response
    response = mock_http_adapter.create_document(test_project_id, "test-name", None)
    assert response.project_id == test_project_id


def test_annotation_has_project_id_injected_annotation_list(mock_http_adapter: HttpInceptionAdapter,
                                                            mock_http_response: Mock, serialized_annotation: dict):
    test_project_id = 1
    test_document_id = 2
    mock_http_response.json.return_value = {'body': [serialized_annotation]}
    mock_http_adapter.client.get.return_value = mock_http_response
    response = mock_http_adapter.annotations(test_project_id, test_document_id)
    assert response[0].project_id == test_project_id


def test_annotation_has_document_id_injected_annotation_list(mock_http_adapter: HttpInceptionAdapter,
                                                             mock_http_response: Mock, serialized_annotation: dict):
    test_project_id = 1
    test_document_id = 2
    mock_http_response.json.return_value = {'body': [serialized_annotation]}
    mock_http_adapter.client.get.return_value = mock_http_response
    response = mock_http_adapter.annotations(test_project_id, test_document_id)
    assert response[0].document_id == test_document_id


def test_annotation_has_project_id_injected_creation(mock_http_adapter: HttpInceptionAdapter,
                                                     mock_http_response: Mock, serialized_annotation: dict):
    test_project_id = 1
    test_document_id = 2
    mock_http_response.json.return_value = {'body': serialized_annotation}
    mock_http_adapter.client.post.return_value = mock_http_response
    response = mock_http_adapter.create_annotation(test_project_id, test_document_id, "test-name", None)
    assert response.project_id == test_project_id


def test_annotation_has_document_id_injected_creation(mock_http_adapter: HttpInceptionAdapter,
                                                      mock_http_response: Mock, serialized_annotation: dict):
    test_project_id = 1
    test_document_id = 2
    mock_http_response.json.return_value = {'body': serialized_annotation}
    mock_http_adapter.client.post.return_value = mock_http_response
    response = mock_http_adapter.create_annotation(test_project_id, test_document_id, "test-name", None)
    assert response.document_id == test_document_id
