import { downloadResponses } from "./map-handler";
import { sendMessage, simulateSendMessage } from "./ws-handler";

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

            // Chụp ảnh định kỳ mỗi 3 giây
            task = setInterval(() => {
                if (ended) {
                    console.log("Video ended");
                    clearInterval(task);
                    return;
                }
                // canvas.width = video.videoWidth;
                // canvas.height = video.videoHeight;
                // ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                // // Convert ảnh sang base64 (PNG)
                // const imageURL = canvas.toDataURL('image/png');

                // let data = {
                //     "image": imageURL,
                //     "id": id
                // };

                // // Gửi qua WebSocket
                // sendMessage(data);
                simulateSendMessage(id);
                id++;
            }, 1000); // mỗi 1 giây
        } else {
            video.pause();
            button.textContent = "Phát";
            clearInterval(task);
        }
    });

    const downloadBtn = document.getElementById("download-btn");
    downloadBtn.addEventListener("click", () => {
        const filename = "responses.json";
        downloadResponses(filename);
    });

}

export { initUI };



// navigator.mediaDevices.getUserMedia({ video: true, audio: false })
//     .then((stream) => {
//         video.srcObject = stream;
//         const track = stream.getVideoTracks()[0];
//         let imageCapture = new ImageCapture(track);
//         imageCapture.takePhoto().then((blob) => {
//             const newFile = new File([blob], "MyJPEG.jpg", { type: "image/jpeg" });
//             EXIF.getData(newFile, function () {
//                 var allMetaData = EXIF.getAllTags(this);
//                 console.log(JSON.stringify(allMetaData, null, "\t"));
//             });
//         });
//     })
//     .catch((err) => {
//         console.error("Không thể truy cập camera:", err);
//         alert("Không thể mở camera. Hãy kiểm tra quyền truy cập!");
//     });
