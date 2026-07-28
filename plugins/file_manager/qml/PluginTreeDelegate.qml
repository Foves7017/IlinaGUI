import QtQuick
import QtQuick.Controls

TreeViewDelegate {
    id: innerDelegate

    MouseArea {
        anchors.fill: parent
        propagateComposedEvents: true
        acceptedButtons: Qt.LeftButton

        onClicked: function(mouse) {
            innerDelegate.treeView.toggleExpanded(row)
            mouse.accepted = true
        }
        onDoubleClicked: function(mouse) {
            backend.double_click_item(model.plugname, model.filePath)
            mouse.accepted = true
        }
    }

    implicitWidth: treeView.width
    implicitHeight: dele_label.implicitHeight + 8

    indicator: Item {
        width: 18; height: 18
        x: innerDelegate.leftMargin + innerDelegate.depth * innerDelegate.indentation
        anchors.verticalCenter: parent.verticalCenter
        visible: innerDelegate.isTreeNode && innerDelegate.hasChildren

        Label {
            anchors.centerIn: parent
            text: "▶"
            font.pixelSize: 18
            color: formatter.get('tree_view_expand_arrow_color')
            rotation: innerDelegate.expanded ? 90 : 0
            Behavior on rotation { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
        }

        MouseArea {
            anchors.fill: parent
            onClicked: innerDelegate.treeView.toggleExpanded(row)
        }
    }

    background: Rectangle {
        color: {
            if (innerDelegate.hovered) return formatter.get('tree_view_current_background_color')
            return 'transparent'
        }
    }

    contentItem: Label {
        id: dele_label
        text: model.display
    }
}
