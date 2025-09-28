// src/pages/MainPage.tsx
import { useState, useEffect } from 'react';
import api from '../api';
import MessageBox from '../components/main/messagebox';

interface Message {
    id: number;
    message: string;
    role: string;
}

interface MainPageProps {
    setSelectedChat: (id: number) => void;
    selectedChat: number | null;
}

function MainPage({ selectedChat }: MainPageProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    // Fetch existing messages when chat is selected
    useEffect(() => {
        const fetchMessages = async () => {
            if (selectedChat === null) {
                setMessages([]);
                return;
            }
            
            try {
                const response = await api.get(`/chats/${selectedChat}/messages`);
                setMessages(response.data);
                console.log('Fetched messages:', response.data);
            } catch (error) {
                console.error('Error fetching messages:', error);
            }
        };
        
        fetchMessages();
    }, [selectedChat]);

    const sendMessage = async () => {
        if (!inputValue.trim() || selectedChat === null || isLoading) return;

        setIsLoading(true);
        const messageToSend = inputValue;
        setInputValue(""); // Clear input immediately

        try {
            const response = await fetch(
                `${api.defaults.baseURL}/chats/${selectedChat}/response`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        content: messageToSend,
                        role: "user"
                    }),
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body?.getReader();
            if (!reader) {
                throw new Error('Response body is not readable');
            }

            let aiMessageAdded = false;
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = new TextDecoder().decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    try {
                        const data = JSON.parse(line);

                        if (data.type === 'user_message') {
                            // Add user message
                            const userMessage: Message = {
                                id: Date.now(), // Better ID generation
                                message: data.content,
                                role: data.role
                            };
                            setMessages(prev => [...prev, userMessage]);
                            
                        } else if (data.type === 'ai_chunk') {
                            // Handle AI streaming
                            if (!aiMessageAdded) {
                                // Add initial AI message
                                const aiMessage: Message = {
                                    id: Date.now() + 1,
                                    message: data.content,
                                    role: "assistant"
                                };
                                setMessages(prev => [...prev, aiMessage]);
                                aiMessageAdded = true;
                            } else {
                                // Update existing AI message
                                setMessages(prev => 
                                    prev.map(msg => 
                                        msg.role === "assistant" && msg.id === prev[prev.length - 1]?.id
                                            ? { ...msg, message: msg.message + data.content }
                                            : msg
                                    )
                                );
                            }
                            
                        } else if (data.type === 'done') {
                            console.log('Stream completed');
                            break;
                        }
                    } catch (parseError) {
                        console.warn('Failed to parse JSON:', line, parseError);
                    }
                    
                }
            }

        } catch (error) {
            console.error('Error sending message:', error);
            // Optionally show error to user
            alert('Failed to send message. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (event: React.KeyboardEvent) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    };

    return (
        <div className='flex flex-col h-screen'>
            {/* Chat messages area */}
            <div className='flex-1 overflow-y-auto p-4'>
                {selectedChat === null ? (
                    <div className='flex items-center justify-center h-full'>
                        <p className='text-gray-500'>Please select a chat from the sidebar.</p>
                    </div>
                ) : (
                    <div className='space-y-4'>
                        {messages.map((message) => (
                            <MessageBox key={message.id} message={message} />
                        ))}
                        {isLoading && (
                            <div className='flex justify-start'>
                                <div className='bg-gray-200 rounded-lg px-4 py-2'>
                                    <span className='text-gray-500'>AI is typing...</span>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Input area */}
            {selectedChat !== null && (
                <div className='border-t bg-white p-4'>
                    <div className='flex gap-2'>
                        <input 
                            type="text" 
                            value={inputValue}
                            onChange={(event) => setInputValue(event.target.value)}
                            onKeyDown={handleKeyPress}
                            placeholder="Type your message..." 
                            className='flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
                            disabled={isLoading}
                        />
                        <button 
                            onClick={sendMessage}
                            disabled={isLoading || !inputValue.trim()}
                            className='bg-blue-500 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-6 rounded-lg'
                        >
                            {isLoading ? 'Sending...' : 'Send'}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

export default MainPage;