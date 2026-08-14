import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    anchors.fill: parent

    color: formatter.get('surface_color')

    Column {
        id: buttonColumn
        anchors.fill: parent
        anchors.topMargin: 8
        anchors.bottomMargin: 8
        spacing: 8

        Repeater {
            model: backend.icon_keys

            delegate: Button {
                width: parent.width
                height: width

                flat: true

                text: backend.icons[modelData]
                font.family: "FluentSystemIcons-Regular"
                font.pixelSize: 32
                palette {
                    buttonText: formatter.get('text_color') 
                }
                onClicked: backend.button_clicked(modelData)
            }
        }
    }
}
