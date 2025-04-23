import VectorSource from 'ol/source/Vector';
import VectorLayer from 'ol/layer/Vector';
import Map from 'ol/Map';
import View from 'ol/View';
import GeoJSON from 'ol/format/GeoJSON.js';
import data from '../map.json';
import DragRotateAndZoom from 'ol/interaction/DragRotateAndZoom.js';
import { defaults as defaultInteractions } from 'ol/interaction/defaults.js';
import Feature from 'ol/Feature.js';
import LineString from 'ol/geom/LineString.js';
import { Stroke, Style } from 'ol/style';

async function loadMap() {
    const geojsonObject = await getMapData(); // Đảm bảo rằng bạn đã nhập đúng dữ liệu GeoJSON từ file JSON của bạn

    // Tạo một layer vector sử dụng GeoJSON
    const vectorSource = new VectorSource({
        features: new GeoJSON().readFeatures(geojsonObject),
    });

    const vectorLayer = new VectorLayer({
        source: vectorSource
    });


    // Trục X: đường ngang
    const xAxis = new Feature(new LineString([
        [0, 0], [200, 0]
    ]));

    // Trục Y: đường dọc
    const yAxis = new Feature(new LineString([
        [0, 0], [0, 200]
    ]));

    xAxis.setStyle(new Style({
        stroke: new Stroke({
            color: 'red',
            width: 2
        })
    }));

    yAxis.setStyle(new Style({
        stroke: new Stroke({
            color: 'blue',
            width: 2
        })
    }));

    const axisLayer = new VectorLayer({
        source: new VectorSource({
            features: [xAxis, yAxis]
        })
    });


    // Tạo bản đồ
    const map = new Map({
        target: 'map',
        interactions: defaultInteractions().extend([new DragRotateAndZoom()]),
        layers: [vectorLayer, axisLayer],
        view: new View({
            center: [0, 0],
            rotation: Math.PI / 2,
            zoom: 17.5,
        })
    });
}

async function getMapData() {
    const mapData = data
    return mapData;
}

export { loadMap }