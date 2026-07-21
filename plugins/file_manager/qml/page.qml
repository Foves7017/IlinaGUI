import QtQuick
import QtQuick.Controls

Item {
    id: root
    anchors.fill: parent

    Item {
        id: titlebar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        implicitHeight: Math.max(pathdisplay.implicitHeight, styleSwitch.implicitHeight) + 8

        Label {
            id: pathdisplay
            anchors.left: parent.left
            anchors.margins: 4
            anchors.verticalCenter: styleSwitch.verticalCenter
            text: backend.workspace

            color: formatter.get('title_path_text_color')
        }

        Switch {
            id: styleSwitch

            anchors.top: parent.top
            anchors.right: parent.right
            anchors.margins: 4

            checked: backend.view_content
            onToggled: {
                backend.view_content = checked
                switchLabelAnim.restart()
            }

            palette.highlight: "transparent"

            Label {
                id: switchLabel
                anchors.right: parent.indicator.left
                anchors.rightMargin: 6
                anchors.verticalCenter: parent.verticalCenter

                text: styleSwitch.checked ? "文件列表" : "插件视图"
                color: formatter.get('title_path_text_color')
            }
        }

        SequentialAnimation {
            id: switchLabelAnim

            PropertyAction { target: switchLabel; property: "opacity"; value: 1 }
            NumberAnimation { target: switchLabel; property: "opacity"; to: 0.25; duration: 120 }
            ScriptAction { script: switchLabel.text = styleSwitch.checked ? "文件列表" : "插件视图" }
            NumberAnimation { target: switchLabel; property: "opacity"; to: 1; duration: 120 }
        }
    }
    // 文件列表
    TreeView {
        id: file_view

        anchors.top: titlebar.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right

        model: backend.file_model
        selectionModel: ItemSelectionModel { model: backend.file_model }
        
        delegate: PluginTreeDelegate { }

        visible: styleSwitch.checked
    }
    
    // 插件视图
    TreeView {
        id: plugin_view

        anchors.top: titlebar.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right

        model: backend.plug_model
        selectionModel: ItemSelectionModel { model: backend.plug_model }

        delegate: PluginTreeDelegate { }

        visible: !styleSwitch.checked
    }
}
