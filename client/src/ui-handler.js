import { sendMessage } from "./ws-handler";
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

    const overlay = document.getElementById('overlay-upload');
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.style.display = 'none'; // ẩn lớp overlay khi click ra ngoài
        }
    });

    document.getElementById("upload-form").addEventListener("submit", function (e) {
        e.preventDefault(); // Ngăn form gửi đi
        const fileInput = this.querySelector('input[type="file"]');
        const file = fileInput.files[0];

        if (!file) {
            alert("Vui lòng chọn một ảnh!");
            return;
        }

        // Truyền trực tiếp `File` vào EXIF.getData
        EXIF.getData(file, function () {
            const allMetaData = EXIF.getAllTags(this);
            console.log("EXIF data:", allMetaData);

            // const lat = EXIF.getTag(this, "GPSLatitude");
            // const lon = EXIF.getTag(this, "GPSLongitude");
            // const orientation = EXIF.getTag(this, "Orientation");

            // console.log("Latitude:", lat);
            // console.log("Longitude:", lon);
            // console.log("Orientation:", orientation);
        });
    });


    const video = document.getElementById("camera-feed");

    navigator.mediaDevices.getUserMedia({
        video: { facingMode: { exact: "environment" } },
        audio: false
    }).then((stream) => {
        video.srcObject = stream;
        video.play();
    }).catch((err) => {
        console.error("Không thể truy cập camera:", err);
    });

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    // task = setInterval(() => {
    //     canvas.width = video.videoWidth;
    //     canvas.height = video.videoHeight;
    //     ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    //     canvas.toBlob(blob => sendMessage(blob), 'image/jpeg', 0.5);
    //     id++;
    // }, 500);
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


export { initUI, showNotification };



