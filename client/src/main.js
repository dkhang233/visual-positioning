import { loadMap } from './load-map.js';

loadMap();


const popup = document.getElementById("camera-popup");
let isDragging = false;
let offset = { x: 0, y: 0 };

// Mouse (desktop)
popup.addEventListener("mousedown", (e) => {
    isDragging = true;
    offset.x = e.clientX - popup.offsetLeft;
    offset.y = e.clientY - popup.offsetTop;
});

document.addEventListener("mousemove", (e) => {
    if (isDragging) {
        popup.style.left = `${e.clientX - offset.x}px`;
        popup.style.top = `${e.clientY - offset.y}px`;
        popup.style.right = "auto";
        popup.style.bottom = "auto";
    }
});

document.addEventListener("mouseup", () => isDragging = false);

// Touch (mobile)
popup.addEventListener("touchstart", (e) => {
    const touch = e.touches[0];
    isDragging = true;
    offset.x = touch.clientX - popup.offsetLeft;
    offset.y = touch.clientY - popup.offsetTop;
});

document.addEventListener("touchmove", (e) => {
    if (isDragging) {
        const touch = e.touches[0];
        popup.style.left = `${touch.clientX - offset.x}px`;
        popup.style.top = `${touch.clientY - offset.y}px`;
        popup.style.right = "auto";
        popup.style.bottom = "auto";
    }
});

document.addEventListener("touchend", () => isDragging = false);


const video = document.getElementById('camera-feed');

// navigator.mediaDevices.getUserMedia({ video: true, audio: false })
//     .then((stream) => {
//         video.srcObject = stream;
//     })
//     .catch((err) => {
//         console.error("Không thể truy cập camera:", err);
//         alert("Không thể mở camera. Hãy kiểm tra quyền truy cập!");
//     });







