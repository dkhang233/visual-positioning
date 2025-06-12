import { downloadResponses } from "./map-handler";
import { sendMessage, simulateSendMessage } from "./ws-handler";
import EXIF from "exif-js";

function initUI() {
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

    let ended = false;
    const video = document.getElementById("camera-feed");

    let exif_data;
    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        .then((stream) => {
            video.srcObject = stream;
            const track = stream.getVideoTracks()[0];
            let imageCapture = new ImageCapture(track);
            imageCapture.takePhoto().then((blob) => {
                const newFile = new File([blob], "MyJPEG.jpg", { type: "image/jpeg" });
                EXIF.getData(newFile, function () {
                    exif_data = EXIF.getAllTags(this);
                    showData(JSON.stringify(exif_data))
                    sendMessage(exif_data)
                });
            });
        })
        .catch((err) => {
            showNotification("❌ Lỗi truy cập camera: " + err.message);
        });



    const overlay = document.getElementById('overlay-upload');
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.style.display = 'none'; // ẩn lớp overlay khi click ra ngoài
        }
    });
    video.addEventListener('ended', () => {
        ended = true;
    });

    const button = document.getElementById("toggle-btn");

    let task;
    let id = 0;
    button.addEventListener("click", () => {
        if (video.paused) {
            video.play();
            button.textContent = "Dừng";

            // Tạo canvas để lấy frame
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            task = setInterval(() => {
                if (ended) {
                    console.log("Video ended");
                    clearInterval(task);
                    return;
                }
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                canvas.toBlob(blob => sendMessage(blob), 'image/jpeg', 0.5);
                id++;
            }, 500);
        } else {
            video.pause();
            button.textContent = "Phát";
            clearInterval(task);
        }
    });
}


function showNotification(message, duration = 3000) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.classList.remove('hidden');
    notification.classList.add('show');

    setTimeout(() => {
        notification.classList.remove('show');
        notification.classList.add('hidden');
    }, duration);
}

function showData(data) {
    const dataContainer = document.getElementById('info');
    dataContainer.innerHTML = data; // Xóa nội dung cũ
}


export { initUI, showNotification };



