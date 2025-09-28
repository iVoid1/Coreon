// src/components/App.tsx
import { useState } from 'react';
import Navbar from './components/navbar';
import Sidebar from './components/sidebar';
import MainPage from './components/mainpage';

function App() {
    const [selectedChat, setSelectedChat] = useState<number | null>(0);

    return (
        <div className="flex flex-col h-screen">
            <Navbar />
            <div className="flex flex-1">
                <Sidebar setSelectedChat={setSelectedChat} />
                <main className="flex-1 bg-gray-900">
                    <MainPage selectedChat={selectedChat} setSelectedChat={setSelectedChat} />
                </main>
            </div>
        </div>
    );
};

export default App;