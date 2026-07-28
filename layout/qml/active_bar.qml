import QtQuick
import QtQuick.Controls

Item {
    id: root
    anchors.fill: parent

    Column {
        id: buttonColumn
        anchors.fill: parent
        anchors.topMargin: 8
        anchors.bottomMargin: 8
        anchors.leftMargin: 10
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
                    buttonText: formatter.get('general_splitter_color') 
                }
                onClicked: backend.trigger_clicked(modelData)
            }
        }
    }
}
