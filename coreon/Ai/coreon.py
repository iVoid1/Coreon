from ollama import Client
from coreon.utils.utils import response_error
from coreon.utils.logger import Logger
from ollama import ChatResponse
from typing import Iterator


logger = Logger(__name__)

class Coreon:
    def __init__(self, model="llama3.1", host="http://localhost:11434"):
        self.client = Client(host=host)
        self.model = model
        self.host = host
        logger.info(f"Initialized Coreon with model '{self.model}' at host '{host}'")
        
    # @response_error
    def _chat(self, messages: str |list[dict], stream: bool = False, **kwargs) -> ChatResponse | Iterator[ChatResponse]:
        """
        Core communication method with Ollama.

        Sends a list of messages to the model and handles both streaming and non-streaming responses.

        Args:
            messages (list[dict]): A list of message dictionaries, following Ollama's expected format.
            stream (bool, optional): Whether to stream the response. Defaults to False.
            **kwargs: Additional parameters passed directly to `client.chat`, such as:
                - tools: Sequence[Mapping[str, Any] | Tool | ((...) -> Any)] | None = None,
                - stream: Literal[False] = False,
                - think: bool | None = None,
                - format: JsonSchemaValue | Literal['', 'json'] | None = None,
                - options: Mapping[str, Any] | Options | None = None,
                - keep_alive: float | str | None = None

        Returns:
            ChatResponse or Iterator[ChatResponse]: The model's response (streamed or not).
        """

        messages = self.ensure_message_format(messages)
        logger.debug(f"Sending chat request - Stream: {stream}")
        response = self.client.chat(model=self.model, 
                                    messages=messages, 
                                    stream=stream,
                                    **kwargs)
        return response
    
    def format_message(self, message: str, role: str = "user") -> list[dict[str, str]]:
        return [{"role": role, "content": message}]
    
    def ensure_message_format(self, message: str | list[dict[str, str]], role: str = "user") -> list[dict[str, str]]:
        if isinstance(message, str):
            return self.format_message(message, role)

        elif isinstance(message, list) and all(
            isinstance(m, dict) and "role" in m and "content" in m for m in message
        ):
            return message

        else:
            raise ValueError("Invalid message format. Expected a string or list of dicts with 'role' and 'content'.")

    def __repr__(self):
        return f"<Coreon(model='{self.model}', host='{self.host}')>"


