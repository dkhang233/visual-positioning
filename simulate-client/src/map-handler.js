// OpenLayers Imports
import Map from 'ol/Map';
import View from 'ol/View';
import Feature from 'ol/Feature';
import VectorSource from 'ol/source/Vector';
import VectorLayer from 'ol/layer/Vector';
import { Stroke, Style, Icon, Fill, Text } from 'ol/style';
import { getCenter } from 'ol/extent';
import { defaults as defaultInteractions } from 'ol/interaction/defaults';
import DragRotateAndZoom from 'ol/interaction/DragRotateAndZoom';
import GeoJSON from 'ol/format/GeoJSON';
import Point from 'ol/geom/Point';
import Polygon from 'ol/geom/Polygon';
import LineString from 'ol/geom/LineString';

// Data Imports
import data from '../static/corridor-map.json';
import gt from '../static/corridor-gt.json';

const windowSize = 10;
let vectorSource;
let currentLocation = null;
let lineData = [];

const styleMap = {
    room: createFillStyle('rgba(255, 255, 255, 1)', 'black', 2),
    wall: createFillStyle('rgba(255, 255, 255, 1)', 'black', 2),
    door: createStrokeStyle('white', 3),
    table: createStrokeStyle('gray', 0.5),
    default: createStrokeStyle('gray', 1)
};

function createFillStyle(fillColor, strokeColor, strokeWidth) {
    return new Style({
        stroke: new Stroke({ color: strokeColor, width: strokeWidth }),
        fill: new Fill({ color: fillColor })
    });
}

function createStrokeStyle(strokeColor, strokeWidth) {
    return new Style({ stroke: new Stroke({ color: strokeColor, width: strokeWidth }) });
}

function createLabelStyle(className, displayName) {
    let iconSrc = null;
    if (className.startsWith("wc")) iconSrc = 'static/wc-icon.png';
    else if (className.startsWith("tech")) iconSrc = 'static/technical-icon.png';

    return new Style({
        image: iconSrc
            ? new Icon({
                crossOrigin: 'anonymous',
                anchor: [0.5, 1.2],
                src: iconSrc,
                scale: 1,
                rotateWithView: true
            })
            : undefined,
        text: new Text({
            text: displayName,
            font: '14px Arial',
            fill: new Fill({ color: '#000' }),
            stroke: new Stroke({ color: '#fff', width: 2 })
        })
    });
}

function createDisplayName(className) {
    if (className.startsWith("wc")) return "WC";
    if (className.startsWith("tech")) return "Kỹ Thuật";
    if (className.startsWith("lift")) return "Thang máy";
    if (className.startsWith("exit")) return "Thang bộ";
    if (className.startsWith("mechanic")) return "Trường cơ khí";
    return className.toUpperCase();
}

async function getMapData() {
    return data;
}

async function loadMap() {
    const geojsonObject = await getMapData();
    const mapFeatures = new GeoJSON().readFeatures(geojsonObject);
    const labelFeatures = [];

    mapFeatures.forEach(feature => {
        let className = feature.get('class');
        let style = styleMap[className?.split('-')[0]] || styleMap.default;
        let displayName = createDisplayName(className);

        let isDoor = className?.startsWith('door') || className?.startsWith('exit') || className?.startsWith('wc') || className?.startsWith('lift');
        if (isDoor) {
            style = styleMap.door;
        }

        feature.setStyle(style);
        if (className?.startsWith('wall')) return;

        const center = getCenter(feature.getGeometry().getExtent());
        const labelFeature = new Feature({ geometry: new Point(center) });
        labelFeature.setStyle(createLabelStyle(className, displayName));
        labelFeatures.push(labelFeature);
    });

    vectorSource = new VectorSource({ features: [...mapFeatures, ...labelFeatures] });

    const vectorLayer = new VectorLayer({
        source: vectorSource,
        updateWhileInteracting: true,
        updateWhileAnimating: true
    });

    const backgroundLayer = new VectorLayer({
        source: new VectorSource({
            features: [
                new Feature({
                    geometry: new Polygon([[[-180, -90], [180, -90], [180, 90], [-180, 90], [-180, -90]]])
                })
            ]
        }),
        style: new Style({ fill: new Fill({ color: '#cccccc' }) }),
        updateWhileInteracting: true,
        updateWhileAnimating: true
    });

    new Map({
        target: 'map',
        interactions: defaultInteractions().extend([new DragRotateAndZoom()]),
        layers: [backgroundLayer, vectorLayer],
        view: new View({ center: [0, 0], zoom: 23.4 })
    });
}

async function updatePosition(x, z, yaw, id) {
    let position = [x, z];

    if (!currentLocation) {
        currentLocation = new Feature({ geometry: new Point(position) });
        currentLocation.setStyle(
            new Style({
                image: new Icon({
                    crossOrigin: 'anonymous',
                    anchor: [0.5, 0.5],
                    src: 'static/current-location.png',
                    scale: 0.4,
                    rotateWithView: true
                }),
                zIndex: 2
            })
        );
        vectorSource.addFeature(currentLocation);
    }

    const dataLength = lineData.length;
    if (dataLength > 0) {
        drawLine([gt[dataLength - 1].x, gt[dataLength - 1].z], [gt[dataLength].x, gt[dataLength].z], 'red', 2);
        const [prevX, prevZ] = lineData[dataLength - 1];
        const distance = Math.hypot(position[0] - prevX, position[1] - prevZ);

        if (distance > 1) {
            let dx = 0, dz = 0;
            const maxIndex = Math.min(dataLength, windowSize);

            for (let i = 1; i < maxIndex; i++) {
                dx += Math.abs(lineData[i][0] - lineData[i - 1][0]);
                dz += Math.abs(lineData[i][1] - lineData[i - 1][1]);
            }

            position = [prevX + dx / maxIndex, prevZ + dz / maxIndex];
        }

        currentLocation.getGeometry().setCoordinates(position);
        const icon = currentLocation.getStyle().getImage();
        if (icon) icon.setRotation(yaw);

        drawLine(lineData[dataLength - 1], position);
    }

    lineData.push(position);
}

function drawLine(start, end, color = 'blue', width = 1) {
    const line = new Feature({ geometry: new LineString([start, end]) });
    line.setStyle(new Style({ stroke: new Stroke({ color, width }) }));
    vectorSource.addFeature(line);
}

export { loadMap, updatePosition };
