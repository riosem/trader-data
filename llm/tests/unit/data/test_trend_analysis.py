import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from utils.model_client import (
    ModelProvider,
    ModelConfig,
    BedrockClient,
    OllamaClient,
    ModelClientFactory,
    LLMManager,
    get_llm_manager
)


class TestModelConfig:
    """Test ModelConfig dataclass"""
    
    def test_model_config_creation(self):
        """Test basic ModelConfig creation"""
        config = ModelConfig(
            provider=ModelProvider.BEDROCK,
            model_name="claude-3-sonnet"
        )
        
        assert config.provider == ModelProvider.BEDROCK
        assert config.model_name == "claude-3-sonnet"
        assert config.temperature == 0.7
        assert config.system_prompt == "You are a helpful AI assistant."
    
    def test_model_config_with_aws_fields(self):
        """Test ModelConfig with AWS-specific fields"""
        config = ModelConfig(
            provider=ModelProvider.BEDROCK,
            model_name="claude-3-sonnet",
            aws_region="us-west-2",
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret"
        )
        
        assert config.aws_region == "us-west-2"
        assert config.aws_access_key_id == "test_key"
        assert config.aws_secret_access_key == "test_secret"


class TestBedrockClient:
    """Test BedrockClient functionality"""
    
    @pytest.fixture
    def bedrock_config(self):
        return ModelConfig(
            provider=ModelProvider.BEDROCK,
            model_name="anthropic.claude-3-sonnet-20240229-v1:0",
            aws_region="us-east-1",
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret"
        )
    
    @patch('boto3.Session')
    def test_bedrock_client_initialization(self, mock_session, bedrock_config):
        """Test BedrockClient initialization"""
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        
        client = BedrockClient(bedrock_config)
        
        assert client.config == bedrock_config
        assert client.client == mock_client
        mock_session.assert_called_once()
    
    @patch('boto3.Session')
    def test_bedrock_client_initialization_failure(self, mock_session, bedrock_config):
        """Test BedrockClient initialization failure"""
        mock_session.side_effect = Exception("AWS connection failed")
        
        with pytest.raises(Exception, match="AWS connection failed"):
            BedrockClient(bedrock_config)
    
    @patch('boto3.Session')
    def test_generate_response_success(self, mock_session, bedrock_config):
        """Test successful response generation"""
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        
        # Mock successful API response
        mock_response = {
            'output': {
                'message': {
                    'content': [{'text': 'This is a test response'}]
                }
            }
        }
        mock_client.converse.return_value = mock_response
        
        client = BedrockClient(bedrock_config)
        response = client.generate_response("Test prompt")
        
        assert response == "This is a test response"
        mock_client.converse.assert_called_once()
    
    @patch('boto3.Session')
    def test_generate_response_with_kwargs(self, mock_session, bedrock_config):
        """Test response generation with additional parameters"""
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        
        mock_response = {
            'output': {
                'message': {
                    'content': [{'text': 'Response with custom params'}]
                }
            }
        }
        mock_client.converse.return_value = mock_response
        
        client = BedrockClient(bedrock_config)
        response = client.generate_response(
            "Test prompt",
            temperature=0.5,
            max_tokens=100,
            system_prompt="Custom system prompt"
        )
        
        assert response == "Response with custom params"
        
        # Verify the API was called with correct parameters
        call_args = mock_client.converse.call_args[1]
        assert call_args['inferenceConfig']['temperature'] == 0.5
        assert call_args['inferenceConfig']['maxTokens'] == 100
        assert call_args['system'] == [{'text': 'Custom system prompt'}]
    
    @patch('boto3.Session')
    def test_generate_response_client_error(self, mock_session, bedrock_config):
        """Test ClientError handling"""
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        
        # Mock ClientError
        error_response = {
            'Error': {
                'Code': 'ValidationException',
                'Message': 'Invalid model ID'
            }
        }
        mock_client.converse.side_effect = ClientError(error_response, 'converse')
        
        client = BedrockClient(bedrock_config)
        
        with pytest.raises(ClientError):
            client.generate_response("Test prompt")
    
    @patch('boto3.Session')
    def test_validate_connection_success(self, mock_session, bedrock_config):
        """Test successful connection validation"""
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        
        mock_response = {
            'output': {
                'message': {
                    'content': [{'text': 'Hello'}]
                }
            }
        }
        mock_client.converse.return_value = mock_response
        
        client = BedrockClient(bedrock_config)
        assert client.validate_connection() is True
    
    @patch('boto3.Session')
    def test_validate_connection_failure(self, mock_session, bedrock_config):
        """Test connection validation failure"""
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.converse.side_effect = Exception("Connection failed")
        
        client = BedrockClient(bedrock_config)
        assert client.validate_connection() is False


class TestOllamaClient:
    """Test OllamaClient functionality"""
    
    @pytest.fixture
    def ollama_config(self):
        return ModelConfig(
            provider=ModelProvider.OLLAMA,
            model_name="llama3.1-70b",
            api_key="test_api_key",
            base_url="https://api.llama-api.com"
        )
    
    @patch('utils.model_client.OpenAI')
    def test_ollama_client_initialization(self, mock_openai, ollama_config):
        """Test OllamaClient initialization"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        client = OllamaClient(ollama_config)
        
        assert client.config == ollama_config
        assert client.client == mock_client
        mock_openai.assert_called_once_with(
            api_key="test_api_key",
            base_url="https://api.llama-api.com"
        )
    
    @patch('utils.model_client.OpenAI')
    def test_generate_response_success(self, mock_openai, ollama_config):
        """Test successful response generation"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test response"
        mock_client.chat.completions.create.return_value = mock_response
        
        client = OllamaClient(ollama_config)
        response = client.generate_response("Test prompt")
        
        assert response == "This is a test response"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('utils.model_client.OpenAI')
    def test_validate_connection_success(self, mock_openai, ollama_config):
        """Test successful connection validation"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello"
        mock_client.chat.completions.create.return_value = mock_response
        
        client = OllamaClient(ollama_config)
        assert client.validate_connection() is True


class TestModelClientFactory:
    """Test ModelClientFactory"""
    
    def test_create_bedrock_client(self):
        """Test creating a Bedrock client"""
        config = ModelConfig(
            provider=ModelProvider.BEDROCK,
            model_name="claude-3-sonnet"
        )
        
        with patch('boto3.Session'):
            client = ModelClientFactory.create_client(config)
            assert isinstance(client, BedrockClient)
    
    def test_create_ollama_client(self):
        """Test creating an Ollama client"""
        config = ModelConfig(
            provider=ModelProvider.OLLAMA,
            model_name="llama3.1-70b",
            api_key="test_key"
        )
        
        with patch('utils.model_client.OpenAI'):
            client = ModelClientFactory.create_client(config)
            assert isinstance(client, OllamaClient)
    
    def test_unsupported_provider(self):
        """Test error for unsupported provider"""
        config = ModelConfig(
            provider=ModelProvider.OPENAI,  # Not implemented yet
            model_name="gpt-4"
        )
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            ModelClientFactory.create_client(config)


class TestLLMManager:
    """Test LLMManager functionality"""
    
    @pytest.fixture
    def llm_manager(self):
        return LLMManager()
    
    @patch('utils.model_client.ModelClientFactory.create_client')
    def test_add_client_success(self, mock_create_client, llm_manager):
        """Test successfully adding a client"""
        mock_client = Mock()
        mock_client.validate_connection.return_value = True
        mock_create_client.return_value = mock_client
        
        config = ModelConfig(
            provider=ModelProvider.OLLAMA,
            model_name="test-model"
        )
        
        llm_manager.add_client("test_client", config)
        
        assert "test_client" in llm_manager.clients
        assert llm_manager.clients["test_client"] == mock_client
        mock_client.validate_connection.assert_called_once()
    
    @patch('utils.model_client.ModelClientFactory.create_client')
    def test_add_client_validation_failure(self, mock_create_client, llm_manager):
        """Test adding a client with failed validation"""
        mock_client = Mock()
        mock_client.validate_connection.return_value = False
        mock_create_client.return_value = mock_client
        
        config = ModelConfig(
            provider=ModelProvider.OLLAMA,
            model_name="test-model"
        )
        
        with pytest.raises(ConnectionError, match="Failed to validate connection"):
            llm_manager.add_client("test_client", config)
    
    def test_generate_response_success(self, llm_manager):
        """Test successful response generation"""
        mock_client = Mock()
        mock_client.generate_response.return_value = "Test response"
        llm_manager.clients["test_client"] = mock_client
        
        response = llm_manager.generate_response("test_client", "Test prompt")
        
        assert response == "Test response"
        mock_client.generate_response.assert_called_once_with("Test prompt")
    
    def test_generate_response_client_not_found(self, llm_manager):
        """Test error when client is not found"""
        with pytest.raises(ValueError, match="Client 'nonexistent' not found"):
            llm_manager.generate_response("nonexistent", "Test prompt")
    
    def test_get_available_clients(self, llm_manager):
        """Test getting available clients"""
        mock_client1 = Mock()
        mock_client2 = Mock()
        llm_manager.clients["client1"] = mock_client1
        llm_manager.clients["client2"] = mock_client2
        
        clients = llm_manager.get_available_clients()
        
        assert sorted(clients) == ["client1", "client2"]


class TestGetLLMManager:
    """Test the singleton LLM manager"""
    
    @patch('utils.model_client._llm_manager', None)
    @patch('utils.model_client.LLMManager')
    def test_get_llm_manager_singleton(self, mock_llm_manager_class):
        """Test that get_llm_manager returns a singleton"""
        mock_manager = Mock()
        mock_llm_manager_class.return_value = mock_manager
        
        # First call should create the instance
        manager1 = get_llm_manager()
        
        # Second call should return the same instance
        manager2 = get_llm_manager()
        
        assert manager1 == manager2
        mock_llm_manager_class.assert_called_once()