import VectorSource from 'ol/source/Vector';
import VectorLayer from 'ol/layer/Vector';
import Map from 'ol/Map';
import View from 'ol/View';
import GeoJSON from 'ol/format/GeoJSON.js';
import data from '../static/map.json';
import gt from '../static/gt.json';
import DragRotateAndZoom from 'ol/interaction/DragRotateAndZoom.js';
import { defaults as defaultInteractions } from 'ol/interaction/defaults.js';
import Feature from 'ol/Feature.js';
import Point from 'ol/geom/Point.js';
import LineString from 'ol/geom/LineString.js';
import { Stroke, Style, Icon, Fill, Text } from 'ol/style';
import CircleStyle from 'ol/style/Circle.js';
import { getCenter } from 'ol/extent';
import Overlay from 'ol/Overlay.js';

let vectorSource;
let currentLocation = null;
let responses = {};
let lineData = [];
let count = 1;

const styleMap = {
    "room": new Style({
        stroke: new Stroke({
            color: 'black',    // Viền màu đen
            width: 2,          // Có thể điều chỉnh
            opacity: 0         // Opacity không được set ở đây trực tiếp
        }),
        fill: new Fill({
            color: 'rgba(255, 255, 255, 1)'  // màu trắng, độ trong suốt = 1
        })
    }),
    'door': new Style({
        stroke: new Stroke({ color: 'white', width: 3 }),
    }),
    'table': new Style({
        stroke: new Stroke({ color: 'gray', width: .5, opacity: 0.25 }),
    }),
    'default': new Style({
        stroke: new Stroke({ color: 'gray', width: 1 })
    })
};


async function loadMap() {
    const geojsonObject = await getMapData(); // Đảm bảo rằng bạn đã nhập đúng dữ liệu GeoJSON từ file JSON của bạn
    const mapFeatures = new GeoJSON().readFeatures(geojsonObject);
    const labelFeatures = [];

    mapFeatures.forEach(feature => {
        let className = feature.getProperties()['class'].split('-')[0];
        console.log(className)
        let style = styleMap[className || 'default'];
        feature.setStyle(style);

        // Tìm tâm của hình để đặt chữ
        const center = getCenter(feature.getGeometry().getExtent());

        // Tạo feature mới là điểm để hiển thị chữ
        const labelFeature = new Feature({
            geometry: new Point(center),
        });

        const labelStyle = new Style({
            text: new Text({
                text: className,
                font: '14px Arial',
                fill: new Fill({ color: '#000' }),
                stroke: new Stroke({ color: '#fff', width: 2 }),
            })
        });

        labelFeature.setStyle(labelStyle);

        labelFeatures.push(labelFeature);
    });

    // Tạo một layer vector sử dụng GeoJSON
    vectorSource = new VectorSource({
        features: [...mapFeatures, ...labelFeatures] // Kết hợp các feature từ mapFeatures và labelFeatures
    });

    const vectorLayer = new VectorLayer({
        source: vectorSource
    });


    const tooltipElement = document.getElementById('image-tooltip');
    const tooltipImage = tooltipElement.querySelector('img');

    const imageOverlay = new Overlay({
        element: tooltipElement,
        stopEvent: false,
        positioning: 'bottom-right',
        offset: [-400, 0],
    });

    // Tạo bản đồ
    const map = new Map({
        target: 'map',
        interactions: defaultInteractions().extend([new DragRotateAndZoom()]),
        layers: [vectorLayer],
        view: new View({
            center: [0, 0],
            // rotation: Math.PI / 2,
            zoom: 23.4,
        }),
    });

    map.addOverlay(imageOverlay);
    map.on('pointermove', function (evt) {
        const feature = map.forEachFeatureAtPixel(evt.pixel, function (feature) {
            return feature;
        });

        if (feature) {
            // Giả sử bạn lưu URL ảnh trong feature properties: feature.set('imageUrl', '...')
            const imageUrl = feature.get('imageUrl');
            if (imageUrl) {
                tooltipImage.src = imageUrl;
                tooltipElement.style.display = 'block';
                imageOverlay.setPosition(evt.coordinate);
            } else {
                tooltipElement.style.display = 'none';
            }
        } else {
            tooltipElement.style.display = 'none';
        }
    });
}

async function getMapData() {
    const mapData = data
    return mapData;
}

async function updatePosition(x, z, yaw, id) {
    let position = [x, z];
    if (currentLocation === null) {
        // Tạo một marker 
        currentLocation = new Feature({
            geometry: new Point([1.4697190474684183, 0.8879343993375413]),
        });
        // Phong cách marker
        currentLocation.setStyle(new Style({
            image: new Icon({
                crossOrigin: 'anonymous',
                anchor: [0.5, 0.5],
                src: 'static/current-location.png',
                scale: 0.4,
            }),
            zIndex: 2  // Ưu tiên cao
        }));
        vectorSource.addFeature(currentLocation);
    }
    currentLocation.getGeometry().setCoordinates(position);
    let style = currentLocation.getStyle();
    if (style && style.getImage) {
        let icon = style.getImage();
        icon.setRotation(yaw);
    }

    // Draw line from previous position to current position
    let dataLength = lineData.length;
    if (dataLength > 0) {
        drawLine(gt[dataLength - 1], gt[dataLength], 'red', 2, false); // Draw a point at the current position
        const lastPosition = lineData[dataLength - 1];
        drawLine(lastPosition, position);
    }
    lineData.push(position);

    // responses[id] = {
    //     x: x,
    //     z: z,
    //     yaw: yaw
    // }
}

function downloadResponses() {
    const jsonString = JSON.stringify(responses, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = "responses.json";
    a.click();

    URL.revokeObjectURL(url);
}

function drawLine(start, end, color = 'blue', width = 1, hasImage = true) {
    const line = new Feature({
        geometry: new LineString([start, end])
    });

    line.setStyle(new Style({
        stroke: new Stroke({
            color: color,
            width: width
        })
    }));

    vectorSource.addFeature(line);

    if (hasImage) {
        const point = new Feature({
            geometry: new Point(end)
        });

        // Gán style
        point.setStyle(
            new Style({
                image: new CircleStyle({
                    radius: 3, // 👈 nhỏ thôi
                    fill: new Fill({ color: 'blue' }), // 👈 màu fill
                    stroke: new Stroke({ color: 'white', width: 1 }), // 👈 viền trắng mỏng
                }),
            })
        );

        const formatted = `frame_${String(count).padStart(5, '0')}.jpg`;
        point.set('imageUrl', 'static/images/' + formatted);
        vectorSource.addFeature(point);
        count++;
    }
}
export { loadMap, updatePosition, downloadResponses }