import { updatePosition } from "./map-handler";
import responsesData from '../static/responses.json';


const WEB_SOCKET_URL = "ws://slam:8000/localize";
const ws = new WebSocket(WEB_SOCKET_URL);


function initWebSocket() {
    // Khi kết nối thành công
    ws.onopen = () => {
        console.log("✅ WebSocket connected");
    };

    ws.onerror = (err) => {
        console.error("❌ WebSocket error", err);
    };

    ws.onmessage = (msg) => {
        console.log("📥 Server response:", msg.data);
        const data = JSON.parse(msg.data);
        const pose = data.pose;
        const id = data.id;
        updatePosition(pose.x, pose.z, pose.yaw, id);
    };
}

function sendMessage(data) {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
        console.log("📤 Data sent");
    } else {
        console.error("❌ WebSocket is not open");
    }
}

function simulateSendMessage(id) {
    let pose = responsesData[id];
    updatePosition(pose.x, pose.z, pose.yaw, id);
}



export { initWebSocket, sendMessage, simulateSendMessage };
