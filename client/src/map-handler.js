import VectorSource from 'ol/source/Vector';
import VectorLayer from 'ol/layer/Vector';
import Map from 'ol/Map';
import View from 'ol/View';
import GeoJSON from 'ol/format/GeoJSON.js';
import data from '../static/map.json';
import DragRotateAndZoom from 'ol/interaction/DragRotateAndZoom.js';
import { defaults as defaultInteractions } from 'ol/interaction/defaults.js';
import Feature from 'ol/Feature.js';
import Point from 'ol/geom/Point.js';
import LineString from 'ol/geom/LineString.js';
import { Stroke, Style, Icon } from 'ol/style';

let currentLocation;
let responses = {};

const styleMap = {
    'room': new Style({
        fill: new Fill({ color: 'rgba(0, 0, 255, 0.1)' }),
        stroke: new Stroke({ color: 'blue', width: 2 })
    }),
    'door': new Style({
        stroke: new Stroke({ color: 'brown', width: 3 })
    }),
    'window': new Style({
        stroke: new Stroke({ color: 'cyan', width: 2, lineDash: [4, 4] })
    }),
    'default': new Style({
        stroke: new Stroke({ color: 'gray', width: 1 })
    })
};

async function loadMap() {
    const geojsonObject = await getMapData(); // Đảm bảo rằng bạn đã nhập đúng dữ liệu GeoJSON từ file JSON của bạn
    const mapFeatures = new GeoJSON().readFeatures(geojsonObject)

    console.log("Map features loaded:", mapFeatures.length);
    mapFeatures.forEach(feature => {
        console.log(feature.getGeometry().getType());
        console.log(feature.hasProperties());
    });

    // Current location marker
    currentLocation = new Feature({
        geometry: new Point([1.4697190474684183, 0.8879343993375413]),
    });

    // Current location style
    currentLocation.setStyle(new Style({
        image: new Icon({
            crossOrigin: 'anonymous',
            anchor: [0.5, 0.5],
            src: 'static/current-location.png',
            scale: 0.5,
        })
    }));

    // Tạo một layer vector sử dụng GeoJSON
    const vectorSource = new VectorSource({
        features: [...mapFeatures, currentLocation],
    });

    const vectorLayer = new VectorLayer({
        source: vectorSource
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
        })
    });
}

async function getMapData() {
    const mapData = data
    return mapData;
}

function updatePosition(x, z, yaw, id) {
    const scale = 1.0; // Scale factor for the map
    // [ 0.73272944 -0.03975946  1.56008534]
    let position = [x * scale, z * scale];
    if (currentLocation) {
        currentLocation.getGeometry().setCoordinates(position);
        let style = currentLocation.getStyle();
        if (style && style.getImage) {
            let icon = style.getImage();
            icon.setRotation(yaw);
        }
    }

    responses[id] = {
        x: x,
        z: z,
        yaw: yaw
    }
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


export { loadMap, updatePosition, downloadResponses }