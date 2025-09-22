import { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [chat, setChat] = useState({title:""});
  let chat_id = "";

  useEffect(() => {
    axios.get(`http://localhost:8000/chat/${chat_id}`)
      .then(response => {
        setChat(response.data);
      })
      .catch(error => {
        console.error('Error fetching chat:', error);
      });
  }, [chat_id]);

  return (
    <>
      <div className='bg-gray-900 text-white min-h-screen flex flex-col items-center justify-center'>
        <h1 className='text-4xl font-bold m-4'>Coreon Chat</h1>
        <input type="text" className='p-2 m-4 rounded-md bg-gray-800' onChange={(e) => {chat_id = e.target.value}}/>
        <h1 className='text-2xl font-bold m-4'>{chat.title}</h1>
      </div>
    </>
  );
}

export default App;