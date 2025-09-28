
// src/components/Sidebar.tsx
import { useState, useEffect } from 'react';
import api from '../api'; // Make sure you have this axios instance

interface SidebarProps {
    setSelectedChat: (id: number) => void;
}

function Sidebar({ setSelectedChat }: SidebarProps) {
        const [chats, setChats] = useState([]);
        const [refresh, setRefresh] = useState(false);

        useEffect(() => {
            const fetchChats = async () => {
                try {
                    const response = await api.get('/chats');
                    setChats(response.data);
                console.log('Fetched chats:', response.data);
                } 
                catch (error) {
                    console.error('Error fetching chats:', error);
                }
            };
            fetchChats();
        }, [refresh]);

        const createChat = async () => {
            try {
                const response = await api.post('/chats', { title: "New Chat" });
                console.log('Created chat:', response.data);
                console.log('Response data ID:', response.data.id);
                console.log("Response data:", chats);
                setSelectedChat(response.data.id);
                setRefresh(!refresh);
            } catch (error) {
                console.error('Error creating chat:', error);
            }
        }
        const deleteChat = async (id: number) => {
            try {
                await api.delete(`/chats/${id}`);
                console.log('Deleted chat with ID:', id);
                setRefresh(!refresh);
            } catch (error) {
                console.error('Error deleting chat:', error);
            }
        }
        return (
          <div className='flex flex-col w-64 bg-neutral-600 border-r'>
            <div className='flex items-center justify-between p-4 border-b'>
              <h2 className='font-bold'>Sidebar</h2>
                <button className='bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded' onClick={() => setRefresh(!refresh)}>Refresh</button>
              </div>
            <div className=''>
              <ul>
                {chats.map((chat: {id: number; title:string}) => (
                  <li key={chat.id}>
                    <button className='bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded' onClick={() => {console.log('Selected chat:', chat.id);setSelectedChat(chat.id)}}>{chat.title}</button>
                    <button className='bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded' onClick={() => {deleteChat(chat.id)}}>Delete</button>
                  </li>
                  
                ))}
              </ul>
            </div>
            <button className='bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded' onClick={() => createChat()}>Create Chat</button>
        </div>			
        );
};

export default Sidebar;