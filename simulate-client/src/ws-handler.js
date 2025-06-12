import { updatePosition } from "./map-handler";
import estimateData from '../static/estimate.json';
import { showNotification } from "./ui-handler";


// const WEB_SOCKET_URL = "wss://honestly-becoming-octopus.ngrok-free.app/localize";
const WEB_SOCKET_URL = "ws://slam:8000/localize";
// let ws = new WebSocket(WEB_SOCKET_URL);
let reconnectInterval = null;

function initWebSocket() {
    // Khi kết nối thành công
    ws.onopen = () => {
        showNotification("✅ Kết nối WebSocket thành công");
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
    };

    ws.onmessage = (msg) => {
        console.log("📥 Server response:", msg.data);
        const data = JSON.parse(msg.data);
        const pose = data.pose;
        const id = data.id;
        updatePosition(pose.x, pose.z, pose.yaw, id);
    };

    ws.onclose = () => {
        showNotification("❌ Kết nối WebSocket đã đóng");
        reconnectInterval = setInterval(() => {
            showNotification("🔄 Attempting to reconnect...");
            ws = new WebSocket(WEB_SOCKET_URL);
            initWebSocket(); // Reinitialize the WebSocket connection
        }, 10000); // Thử kết nối lại sau 5 giây
    };

    ws.onerror = (err) => {
        showNotification("❌ Lỗi kết nối WebSocket: " + err.message);
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
    let pose = estimateData[id];
    updatePosition(pose.x, pose.z, pose.yaw, id);
}



export { initWebSocket, sendMessage, simulateSendMessage };
