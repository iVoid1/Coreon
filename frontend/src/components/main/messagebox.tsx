interface MessageBoxProps {
    message: { id: number; message: string; role: string };
}

function MessageBox({ message }: MessageBoxProps) {
    return (
        <div className="bg-gray-500 p-4 my-2">
            <h3>{message.message}</h3>
        </div>
    );
}

export default MessageBox;