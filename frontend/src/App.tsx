// src/App.tsx

import React, { useState, useEffect, useCallback, useRef } from 'react';
import type { Optional } from 'typescript/lib/lib.es2021.string';

// =================================================================
// 1. ⚙️ تعريف الأنواع (Types)
// =================================================================

type ChatId = number | null; // null يعني وضع RAM أو محادثة جديدة غير محفوظة

interface Chat {
    id: number;
    title: string;
    created_at: string;
}

interface Message {
    id: number | string; 
    content: string;
    role: 'user' | 'assistant' | 'system';
    isStreaming?: boolean;
    isUpdate?: boolean; // للإشارة إلى تحديث رسالة جارية
}


// =================================================================
// 2. 🔌 منطق الاتصال بالخادم (API Logic)
// =================================================================

const API_BASE_URL = 'http://127.0.0.1:8000';

/**
 * دالة بث استجابة الذكاء الاصطناعي
 */
async function streamChatResponse(
    chatId: ChatId,
    content: string,
    onChunk: (chunk: string) => void,
    onComplete: () => void,
    onError: (errorMsg: string) => void
) {
    // 💡 تحديد نقطة الاتصال:
    // إذا كان chatId موجودًا (رقم)، نستخدم مسار الـ Persistent: /chats/{id}/response
    // إذا كان chatId هو null (دردشة مؤقتة)، نستخدم مسار الـ Volatile: /chat/response
    const endpoint = chatId !== null && chatId !== -1 // -1 رمز للمحادثة الجديدة التي تم إنشاؤها للتو
        ? `${API_BASE_URL}/chats/${chatId}/response` 
        : `${API_BASE_URL}/chat/response`;        
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content, role: 'user' }), 
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
        }

        const reader = response.body!.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            
            const parts = buffer.split('\n');
            buffer = parts.pop() || '';

            for (const part of parts) {
                if (part) {
                    try {
                        const data = JSON.parse(part);
                        if (data.type === 'ai_chunk') {
                            onChunk(data.content);
                        } else if (data.type === 'done') {
                            onComplete();
                            return;
                        } else if (data.type === 'error') {
                            onError(data.content || "حدث خطأ في الـ API.");
                            return;
                        }
                    } catch (e) {
                        console.error("خطأ في تحليل مقطع JSON:", e);
                    }
                }
            }
        }
        onComplete();
    } catch (error: any) {
        console.error("خطأ في الاتصال بالبث:", error);
        onError(`خطأ في الاتصال: ${error.message}`);
    }
}

/**
 * جلب قائمة المحادثات المحفوظة
 */
async function fetchChats(): Promise<Chat[]> {
    const response = await fetch(`${API_BASE_URL}/chats`);
    if (!response.ok) throw new Error("فشل في جلب المحادثات");
    return response.json();
}

/**
 * جلب رسائل محادثة محددة
 */
async function fetchMessages(chatId: number): Promise<any[]> {
    if (!chatId) return [];
    const response = await fetch(`${API_BASE_URL}/chats/${chatId}/messages`);
    if (!response.ok) throw new Error("فشل في جلب الرسائل");
    return response.json();
}

/**
 * إنشاء محادثة جديدة في قاعدة البيانات
 */
async function createChat(title: string): Promise<Chat> {
    const response = await fetch(`${API_BASE_URL}/chats`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title }),
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "فشل في إنشاء المحادثة");
    }
    return response.json();
}


// =================================================================
// 3. 🖼️ المكونات الفرعية (Components)
// =================================================================

// 3.1. Navbar
const Navbar: React.FC = () => {
    return (
        <nav className="flex items-center justify-center bg-gray-900 p-3 text-white shadow-lg z-10">
            <h1 className="font-extrabold text-lg text-indigo-400">COREON AI SYSTEM</h1>
        </nav>
    );
};

// 3.2. Message
interface MessageProps {
    message: Message;
}

const MessageComponent: React.FC<MessageProps> = ({ message }) => {
    const isUser = message.role === 'user';
    const isError = message.role === 'system';

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-xl p-4 shadow-md text-right ${
                isUser ? 
                    'bg-indigo-600 text-white rounded-t-xl rounded-bl-xl' :
                isError ? 
                    'bg-red-100 text-red-800 border border-red-300 rounded-xl' :
                    'bg-white border border-gray-200 text-gray-800 rounded-t-xl rounded-br-xl'
            }`}>
                <p className="whitespace-pre-wrap leading-relaxed">
                    {message.content || (message.isStreaming ? 'جاري الكتابة...' : '')}
                </p>
                {message.isStreaming && (
                    <div className="flex items-center space-x-1 mt-2">
                        <div className={`h-2 w-2 rounded-full animate-pulse ${isUser ? 'bg-indigo-300' : 'bg-gray-400'}`}></div>
                        <div className={`h-2 w-2 rounded-full animate-pulse delay-150 ${isUser ? 'bg-indigo-300' : 'bg-gray-400'}`}></div>
                        <div className={`h-2 w-2 rounded-full animate-pulse delay-300 ${isUser ? 'bg-indigo-300' : 'bg-gray-400'}`}></div>
                    </div>
                )}
            </div>
        </div>
    );
};

// 3.3. Sidebar
interface SidebarProps {
    chats: Chat[];
    loading: boolean;
    currentChatId: ChatId;
    onSelectChat: (id: number) => void;
    onStartTempChat: () => void;
    onStartNewChat: () => void; // 💡 تمت الإضافة: لمعالجة إنشاء محادثة جديدة (DB)
}

const Sidebar: React.FC<SidebarProps> = ({ chats, loading, onSelectChat, onStartTempChat, onStartNewChat, currentChatId }) => {
    
    // 💡 نحدد إذا كانت المحادثة الحالية هي محادثة مؤقتة (RAM) أو تم إنشاؤها للتو (null)
    const isTempChat = currentChatId === null; 

    return (
        <div className="w-80 flex-shrink-0 bg-white border-l border-gray-200 flex flex-col p-4 shadow-2xl">
            <h2 className="text-2xl font-bold text-indigo-700 mb-4 border-b pb-2">Coreon Chats</h2>

            {/* 💡 الزر الجديد: بدء محادثة جديدة (DB) */}
            <button 
                onClick={onStartNewChat}
                className={`w-full py-3 mb-2 font-semibold rounded-xl transition duration-200 text-lg shadow-md bg-green-600 text-white hover:bg-green-700`}
            >
                ➕ محادثة جديدة (DB)
            </button>
            
            {/* زر الدردشة المؤقتة (RAM) */}
            <button 
                onClick={onStartTempChat}
                className={`w-full py-3 mb-4 font-semibold rounded-xl transition duration-200 text-lg shadow-md ${
                            isTempChat ? 'bg-indigo-700 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            >
                💾 دردشة مؤقتة (RAM)
            </button>

            <div className="overflow-y-auto flex-grow space-y-2">
                <p className="text-sm font-semibold text-gray-500 uppercase mb-2">المحادثات المحفوظة</p>
                {loading && <p className="text-gray-500 text-center">جاري التحميل...</p>}
                
                {chats.map((chat) => (
                    <div 
                        key={chat.id}
                        onClick={() => onSelectChat(chat.id)}
                        className={`p-3 rounded-lg cursor-pointer transition duration-150 text-right truncate ${
                                    currentChatId === chat.id ? 'bg-indigo-100 border-r-4 border-indigo-600 font-medium' : 'hover:bg-gray-100 bg-white'}`}
                    >
                        {chat.title}
                    </div>
                ))}
            </div>
        </div>
    );
};

// 3.4. ChatArea
interface ChatAreaProps {
    chatId: ChatId;
    title: string;
    messages: Message[];
    onAddMessage: (message: Message) => void;
}

const ChatArea: React.FC<ChatAreaProps> = ({ chatId, title, messages, onAddMessage }) => {
    const [input, setInput] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    useEffect(() => { scrollToBottom(); }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isStreaming) return;

        const userContent = input.trim();
        setInput('');
        setIsStreaming(true);

        const userMessageId = Date.now();
        onAddMessage({ role: 'user', content: userContent, id: userMessageId });

        const aiMessageId = userMessageId + 1;
        let fullAiResponse = '';
        onAddMessage({ role: 'assistant', content: '', id: aiMessageId, isStreaming: true });

        await streamChatResponse(
            chatId, 
            userContent, 
            (chunk) => { // onChunk
                fullAiResponse += chunk;
                onAddMessage({ 
                    role: 'assistant', 
                    content: fullAiResponse, 
                    id: aiMessageId, 
                    isStreaming: true, 
                    isUpdate: true 
                });
            }, 
            () => { // onComplete
                setIsStreaming(false);
                // إرسال الرسالة النهائية بدون علامة streaming
                onAddMessage({ role: 'assistant', content: fullAiResponse, id: aiMessageId, isStreaming: false, isUpdate: true });
            },
            (errorMsg) => { // onError
                setIsStreaming(false);
                onAddMessage({ role: 'system', content: `خطأ: ${errorMsg}`, id: Date.now() });
            }
        );
    };

    return (
        <div className="flex flex-col flex-grow bg-gray-50">
            <header className="p-4 border-b border-gray-200 bg-white shadow-md">
                <h1 className="text-xl font-bold text-gray-700">{title}</h1>
            </header>
            
            <div className="messages-area flex-grow overflow-y-auto p-6 space-y-6">
                {messages.map((msg) => (
                    <MessageComponent key={msg.id} message={msg} />
                ))}
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 bg-white shadow-lg">
                <div className="flex space-x-2 space-x-reverse">
                    <input 
                        type="text" 
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder={isStreaming ? "جاري انتظار الرد..." : "اكتب رسالتك..."}
                        className="flex-grow p-4 border border-gray-300 rounded-xl focus:ring-indigo-500 focus:border-indigo-500 outline-none transition duration-150 text-right"
                        disabled={isStreaming}
                        dir="rtl"
                    />
                    <button 
                        type="submit"
                        className={`px-6 py-3 font-semibold rounded-xl text-white transition duration-200 ${
                            (isStreaming || !input.trim()) ? 'bg-indigo-300 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'
                        }`}
                        disabled={isStreaming || !input.trim()}
                    >
                        {isStreaming ? '...' : 'إرسال'}
                    </button>
                </div>
            </form>
        </div>
    );
};


// =================================================================
// 4. 🚀 المكون الرئيسي (App)
// * يجمع كل شيء ويحتوي على منطق الحالة
// =================================================================

function App() {
    const [chats, setChats] = useState<Chat[]>([]);
    const [currentChatId, setCurrentChatId] = useState<ChatId>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [loadingChats, setLoadingChats] = useState(true);

    // تحميل قائمة المحادثات
    const loadChats = useCallback(async () => {
        setLoadingChats(true);
        try {
            const data = await fetchChats();
            setChats(data);
        } catch (error) {
            console.error("Failed to load chats:", error);
        } finally {
            setLoadingChats(false);
        }
    }, []);

    useEffect(() => { loadChats(); }, [loadChats]);

    // تحميل الرسائل عند تغيير المحادثة
    useEffect(() => {
        const loadMessages = async () => {
            // محادثة مؤقتة (null) أو محادثة جديدة لم يتم حفظها بعد
            if (currentChatId === null) {
                setMessages([]);
                return;
            }
            try {
                // chatId هو رقم محادثة محفوظة في DB
                const data = await fetchMessages(currentChatId as number);
                const formattedMessages: Message[] = data.map((msg: any) => ({
                    role: msg.role,
                    content: msg.content,
                    id: msg.id
                }));
                setMessages(formattedMessages);
            } catch (error) {
                console.error("Failed to load messages:", error);
                setMessages([{ role: 'system', content: 'خطأ في تحميل رسائل المحادثة!', id: Date.now() }]);
            }
        };
        loadMessages();
    }, [currentChatId]);

    // وظيفة الإضافة/التحديث الذكية (مفتاح الـ Streaming)
    const handleAddMessage = useCallback((message: Message) => {
        setMessages(prev => {
            if (message.isUpdate) {
                // تحديث رسالة سابقة (رسالة الـ AI الجارية)
                const lastMessageIndex = prev.findIndex(m => m.id === message.id);
                
                if (lastMessageIndex !== -1) {
                    const updatedMessages = [...prev];
                    updatedMessages[lastMessageIndex] = message; 
                    return updatedMessages;
                }
            }
            // إضافة رسالة جديدة (رسالة المستخدم أو رسالة AI جديدة)
            return [...prev, message];
        });
    }, []);

    const handleSelectChat = (id: number) => {
        setCurrentChatId(id);
        setMessages([]);
    };
    
    // وضع RAM (null) - تبدأ فارغة
    const handleStartTempChat = () => {
        setCurrentChatId(null);
        setMessages([]);
    }

    // 💡 وظيفة بدء محادثة جديدة (DB)
    const handleStartNewChat = async () => {
        // 1. نبدأ محادثة فارغة في الواجهة بينما ننتظر الـ API
        setCurrentChatId(null); // نستخدم null مؤقتًا
        setMessages([{ role: 'system', content: 'جاري إنشاء محادثة جديدة في قاعدة البيانات...', id: Date.now() }]);

        try {
            // نستخدم عنوان مؤقت، أو يمكن أن تطلب من المستخدم إدخاله
            const newChat = await createChat("محادثة جديدة بدون عنوان"); 
            
            // 2. نعيد تحميل قائمة المحادثات (لتظهر المحادثة الجديدة في الشريط الجانبي)
            await loadChats();
            
            // 3. ننتقل مباشرة للمحادثة الجديدة التي تم إنشاؤها
            setCurrentChatId(newChat.id); 
            setMessages([]); // مسح رسالة "جاري الإنشاء"
        } catch (error: any) {
            console.error("خطأ في إنشاء محادثة جديدة:", error);
            setMessages([{ role: 'system', content: `خطأ: ${error.message}. يرجى التحقق من اتصال الخادم.`, id: Date.now() }]);
        }
    }

    const currentChatTitle = currentChatId === null 
        ? "دردشة مؤقتة (RAM 💾)" 
        : chats.find(c => c.id === currentChatId)?.title || "محادثة غير مسماة";

    return (
        <div className="flex flex-col h-screen bg-gray-50 text-gray-800" dir="rtl">
            <Navbar />
            <div className="flex flex-grow overflow-hidden">
                <Sidebar 
                    chats={chats}
                    loading={loadingChats}
                    onSelectChat={handleSelectChat}
                    onStartTempChat={handleStartTempChat}
                    onStartNewChat={handleStartNewChat}
                    currentChatId={currentChatId}
                />
                <ChatArea 
                    chatId={currentChatId}
                    title={currentChatTitle}
                    messages={messages}
                    onAddMessage={handleAddMessage}
                />
            </div>
        </div>
    );
}

export default App;