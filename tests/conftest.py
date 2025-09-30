"""
Test configuration and fixtures for BloodHound CLI
"""
import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Any


@pytest.fixture
def mock_neo4j_session():
    """Mock Neo4j session for unit tests - no real database needed"""
    session = Mock()
    
    # Mock common query responses
    session.run.return_value.data.return_value = []
    
    # Mock for ACL queries
    def mock_acl_response():
        return [
            {
                "result": {
                    "source": "testuser",
                    "sourceType": "User", 
                    "target": "testgroup",
                    "targetType": "Group",
                    "type": "MemberOf",
                    "sourceDomain": "test.local",
                    "targetDomain": "test.local",
                    "targetEnabled": True
                }
            }
        ]
    
    # Mock for user queries
    def mock_user_response():
        return [
            {"samaccountname": "admin"},
            {"samaccountname": "user1"},
            {"samaccountname": "user2"}
        ]
    
    # Mock for computer queries  
    def mock_computer_response():
        return [
            {"name": "dc01.test.local"},
            {"name": "workstation01.test.local"}
        ]
    
    # Configure session.run to return different responses based on query
    def mock_run(query, **params):
        result = Mock()
        if "ACL" in query or "isacl" in query:
            result.data.return_value = mock_acl_response()
        elif "User" in query and "samaccountname" in query:
            result.data.return_value = mock_user_response()
        elif "Computer" in query and "name" in query:
            result.data.return_value = mock_computer_response()
        else:
            result.data.return_value = []
        return result
    
    session.run = mock_run
    return session


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver for unit tests"""
    driver = Mock()
    session = mock_neo4j_session()
    driver.session.return_value.__enter__.return_value = session
    driver.session.return_value.__exit__.return_value = None
    return driver


@pytest.fixture
def sample_ace_data():
    """Sample ACE data for testing"""
    return [
        {
            "source": "testuser",
            "sourceType": "User",
            "target": "testgroup", 
            "targetType": "Group",
            "type": "MemberOf",
            "sourceDomain": "test.local",
            "targetDomain": "test.local",
            "targetEnabled": True
        }
    ]


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return [
        {"samaccountname": "admin"},
        {"samaccountname": "user1"},
        {"samaccountname": "user2"}
    ]


@pytest.fixture
def sample_computer_data():
    """Sample computer data for testing"""
    return [
        {"name": "dc01.test.local"},
        {"name": "workstation01.test.local"}
    ]


@pytest.fixture
def mock_ce_response():
    """Mock CE API responses"""
    return {
        "auth": {
            "status_code": 200,
            "json": {"data": {"session_token": "mock_token_123"}}
        },
        "upload": {
            "status_code": 200,
            "json": {"data": {"id": 123}}
        }
    }


@pytest.fixture
def mock_requests_session():
    """Mock requests session for CE tests"""
    session = Mock()
    
    def mock_post(url, **kwargs):
        response = Mock()
        if "login" in url:
            response.status_code = 200
            response.json.return_value = {"data": {"session_token": "mock_token"}}
        elif "upload" in url:
            response.status_code = 200
            response.json.return_value = {"data": {"id": 123}}
        else:
            response.status_code = 200
            response.json.return_value = {}
        return response
    
    session.post = mock_post
    session.get = mock_post  # Same mock for simplicity
    return session
