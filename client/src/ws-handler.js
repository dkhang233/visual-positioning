import { updatePosition } from "./map-handler";
import responsesData from '../static/responses.json';
import { showNotification } from "./ui-handler";


const WEB_SOCKET_URL = "wss://honestly-becoming-octopus.ngrok-free.app/test";
let ws = new WebSocket(WEB_SOCKET_URL);


function initWebSocket() {
    // Khi kết nối thành công
    ws.onopen = () => {
        showNotification("✅ Kết nối WebSocket thành công");
    };

    ws.onerror = (err) => {
        showNotification("✅ Lỗi kết nối WebSocket: " + err.message);
        setInterval(() => {
            ws = new WebSocket(WEB_SOCKET_URL);
            initWebSocket();
        }, 5000);
    };

    ws.onmessage = (msg) => {
        console.log("📥 Server response:", msg.data);
        // const data = JSON.parse(msg.data);
        // const pose = data.pose;
        // const id = data.id;
        // updatePosition(pose.x, pose.z, pose.yaw, id);
    };
}

function sendMessage(data) {
    if (ws.readyState === WebSocket.OPEN) {
        // Kiểm tra nếu data là một đối tượng Blob (ví dụ: ảnh)
        if (data instanceof Blob) {
            // Chuyển đổi Blob thành ArrayBuffer
            const reader = new FileReader();
            reader.onload = function (event) {
                const arrayBuffer = event.target.result;
                ws.send(arrayBuffer);
                console.log("📤 Image sent as ArrayBuffer");
            };
            reader.readAsArrayBuffer(data);
            return;
        } else {
            // Nếu data không phải là Blob, gửi trực tiếp
            ws.send(JSON.stringify(data));
            console.log("📤 Data sent:", data);
        }
    } else {
        console.error("❌ WebSocket is not open");
    }
}

function simulateSendMessage(id) {
    let pose = responsesData[id];
    updatePosition(pose.x, pose.z, pose.yaw, id);
}



export { initWebSocket, sendMessage, simulateSendMessage };
