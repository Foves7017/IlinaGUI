import QtQuick
import QtQuick.Shapes 1.15

Item {
    id: root
    anchors.fill: parent

    Shape {
        id: shape
        anchors.fill: parent

        ShapePath {
            strokeWidth: 1
            strokeColor: formatter.general_splitter_color
            fillColor: "transparent"
            startX: shape.width; startY: 0
            PathLine { x: shape.width; y: shape.height }
        }
    }
}
