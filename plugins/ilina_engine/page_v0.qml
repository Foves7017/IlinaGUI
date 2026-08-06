import QtQuick
import QtQuick.Controls

ListView {
    anchors.fill: parent
    model: ilina_message_list_model

    delegate: Item {
        width: ListView.view.width
        implicitHeight: roleLabel.implicitHeight
                      + reasoningLabel.implicitHeight
                      + contentLabel.implicitHeight

        Label {
            id: roleLabel
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            text: model.role
        }
        Label {
            id: reasoningLabel
            anchors.top: roleLabel.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            text: model.reasoning_content
        }
        Label {
            id: contentLabel
            anchors.top: reasoningLabel.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            text: model.content
        }
    }
}
