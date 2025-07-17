from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from utils.logger import logger
from utils.common import Env
from openai import OpenAI
import boto3
from botocore.exceptions import ClientError


class ModelProvider(Enum):
    """Supported model providers"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"


@dataclass
class ModelConfig:
    """Configuration for LLM models"""
    provider: ModelProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    system_prompt: str = "You are a helpful AI assistant."
    # AWS Bedrock specific fields
    aws_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.logger = logger
    
    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response from the model"""
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate the connection to the model provider"""
        pass


class BedrockClient(BaseLLMClient):
    """Client for AWS Bedrock using Converse API"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Bedrock runtime client"""
        try:
            # Configure AWS credentials
            session_kwargs = {
                'region_name': self.config.aws_region or 'us-east-1'
            }
            
            if self.config.aws_access_key_id and self.config.aws_secret_access_key:
                session_kwargs.update({
                    'aws_access_key_id': self.config.aws_access_key_id,
                    'aws_secret_access_key': self.config.aws_secret_access_key
                })
                if self.config.aws_session_token:
                    session_kwargs['aws_session_token'] = self.config.aws_session_token
            
            session = boto3.Session(**session_kwargs)
            return session.client('bedrock-runtime')
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Bedrock client: {e}")
            raise
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response using AWS Bedrock Converse API"""
        try:
            # Build the conversation
            messages = self._build_messages(prompt, kwargs.get('system_prompt'))
            
            # Prepare the request
            converse_params = {
                'modelId': self.config.model_name,
                'messages': messages,
                'inferenceConfig': {
                    'temperature': kwargs.get('temperature', self.config.temperature),
                }
            }
            
            # Add max tokens if specified
            max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
            if max_tokens:
                converse_params['inferenceConfig']['maxTokens'] = max_tokens
            
            # Add system prompt if provided
            system_prompt = kwargs.get('system_prompt') or self.config.system_prompt
            if system_prompt and system_prompt != "You are a helpful AI assistant.":
                converse_params['system'] = [{'text': system_prompt}]
            
            # Make the API call
            response = self.client.converse(**converse_params)
            
            # Extract the response text
            content = response['output']['message']['content'][0]['text']
            
            self.logger.info(f"Successfully generated response using {self.config.model_name}")
            return content
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"Bedrock API error {error_code}: {error_message}")
            raise
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            raise

    def _build_messages(self, prompt: str, system_prompt: Optional[str] = None) -> List[Dict[str, Any]]:
        """Build the messages array for the Converse API"""
        # Bedrock Converse API format
        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ]
        return messages

    def validate_connection(self) -> bool:
        """Validate connection to Bedrock"""
        try:
            # Test with a simple prompt
            test_response = self.generate_response("Hello", max_tokens=10)
            return bool(test_response)
        except Exception as e:
            self.logger.error(f"Bedrock connection validation failed: {e}")
            return False


class OllamaClient(BaseLLMClient):
    """Client for Ollama/Llama API models"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = self._initialize_client()
    
    def _initialize_client(self) -> OpenAI:
        """Initialize the OpenAI client for Ollama"""
        try:
            return OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url or "https://api.llama-api.com"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Ollama client: {e}")
            raise
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response from the Ollama model"""
        try:
            messages = self._build_messages(prompt, kwargs.get('system_prompt'))
            
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=kwargs.get('temperature', self.config.temperature),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            )
            
            content = response.choices[0].message.content
            self.logger.info(f"Successfully generated response using {self.config.model_name}")
            return content
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            raise
    
    def _build_messages(self, prompt: str, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """Build the messages array for the API call"""
        messages = [
            {
                "role": "system", 
                "content": system_prompt or self.config.system_prompt
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        return messages
    
    def validate_connection(self) -> bool:
        """Validate connection to Ollama API"""
        try:
            test_response = self.generate_response("Hello")
            return bool(test_response)
        except Exception as e:
            self.logger.error(f"Connection validation failed: {e}")
            return False


class ModelClientFactory:
    """Factory class for creating model clients"""
    
    _clients = {
        ModelProvider.OLLAMA: OllamaClient,
        ModelProvider.BEDROCK: BedrockClient,
        # Add other providers here
        # ModelProvider.OPENAI: OpenAIClient,
        # ModelProvider.ANTHROPIC: AnthropicClient,
    }
    
    @classmethod
    def create_client(cls, config: ModelConfig) -> BaseLLMClient:
        """Create a client based on the provider"""
        client_class = cls._clients.get(config.provider)
        if not client_class:
            raise ValueError(f"Unsupported provider: {config.provider}")
        
        return client_class(config)


class LLMManager:
    """High-level manager for LLM operations"""
    
    def __init__(self):
        self.clients: Dict[str, BaseLLMClient] = {}
        self.logger = logger
    
    def add_client(self, name: str, config: ModelConfig) -> None:
        """Add a new LLM client"""
        try:
            client = ModelClientFactory.create_client(config)
            if client.validate_connection():
                self.clients[name] = client
                self.logger.info(f"Successfully added client: {name}")
            else:
                raise ConnectionError(f"Failed to validate connection for {name}")
        except Exception as e:
            self.logger.error(f"Failed to add client {name}: {e}")
            raise
    
    def generate_response(self, client_name: str, prompt: str, **kwargs) -> str:
        """Generate response using specified client"""
        if client_name not in self.clients:
            raise ValueError(f"Client '{client_name}' not found")
        
        return self.clients[client_name].generate_response(prompt, **kwargs)
    
    def get_available_clients(self) -> List[str]:
        """Get list of available client names"""
        return list(self.clients.keys())

# Singleton instance for easy access
_llm_manager = None

def get_llm_manager() -> LLMManager:
    """Get singleton LLM manager instance"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
        
        # Add default clients based on available environment variables
        try:
            # Try to add Bedrock client first (if AWS credentials are available)
            if hasattr(Env, 'AWS_ACCESS_KEY_ID') and Env.AWS_ACCESS_KEY_ID:
                bedrock_config = ModelConfig(
                    provider=ModelProvider.BEDROCK,
                    model_name="anthropic.claude-3-sonnet-20240229-v1:0",
                    aws_region=getattr(Env, 'AWS_REGION', 'us-east-1'),
                    aws_access_key_id=Env.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=Env.AWS_SECRET_ACCESS_KEY,
                    system_prompt="You are a professional trading assistant."
                )
                _llm_manager.add_client("default_bedrock", bedrock_config)
        except Exception as e:
            logger.warning(f"Could not add Bedrock client: {e}")
        
        try:
            # Fallback to Ollama if available
            if hasattr(Env, 'OLLAMA_API_KEY') and Env.OLLAMA_API_KEY:
                ollama_config = ModelConfig(
                    provider=ModelProvider.OLLAMA,
                    model_name="llama3.1-70b",
                    api_key=Env.OLLAMA_API_KEY,
                    base_url="https://api.llama-api.com",
                    system_prompt="You are a professional trading assistant."
                )
                _llm_manager.add_client("default_ollama", ollama_config)
        except Exception as e:
            logger.warning(f"Could not add Ollama client: {e}")
    
    return _llm_manager