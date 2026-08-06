import QtQuick
import QtQuick.Controls

Item {
    anchors.fill: parent


    ListView {
        id: message_list

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: input_area.top

        model: ilina_message_list_model
        spacing: formatter.get('message_list_spacing')


        delegate: Item {
            width: ListView.view.width

            property bool reasoningExpanded: false
            property bool contentExpanded: false

            property bool reasoningNeedCollapse:
                reasoningText.implicitHeight > formatter.get('max_content_height')

            property bool contentNeedCollapse:
                contentText.implicitHeight > formatter.get('max_content_height')


            implicitHeight: messageRow.implicitHeight + 24


            Row {
                id: messageRow

                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 12

                spacing: 16


                Text {
                    id: roleText

                    width: formatter.get('role_column_width')

                    text: model.role
                    wrapMode: Text.Wrap

                    font.family: "Maple Mono NF CN"
                    font.pixelSize: contentText.font.pixelSize * 1.2
                    font.bold: true

                    color: model.role_normal_color

                    textFormat: Text.PlainText
                    horizontalAlignment: Text.AlignRight
                }


                Column {

                    width: parent.width - roleText.width - messageRow.spacing

                    spacing: 8


                    Item {

                        width: parent.width
                        height: buttonRow.height

                        visible: reasoningNeedCollapse || contentNeedCollapse


                        Row {

                            id: buttonRow

                            spacing: 8


                            Button {

                                visible: reasoningNeedCollapse

                                text: reasoningExpanded
                                      ? "折叠思维链"
                                      : "展开思维链"


                                padding: 0

                                background: Rectangle {
                                    radius: 4
                                    color: parent.hovered
                                           ? formatter.get('titlebar_button_hover_color')
                                           : "transparent"
                                }


                                contentItem: Text {

                                    text: parent.text

                                    color: "#88FFFFFF"

                                }


                                onClicked: {
                                    reasoningExpanded = !reasoningExpanded
                                }
                            }



                            Button {

                                visible: contentNeedCollapse
                                         && model.role !== "assistant"


                                text: contentExpanded
                                      ? "折叠正文"
                                      : "展开正文"


                                padding: 0


                                background: Rectangle {
                                    radius: 4
                                    color: parent.hovered
                                           ? formatter.get('titlebar_button_hover_color')
                                           : "transparent"
                                }


                                contentItem: Text {

                                    text: parent.text

                                    color: "#88FFFFFF"

                                }


                                onClicked: {
                                    contentExpanded = !contentExpanded
                                }
                            }
                        }
                    }



                    Text {

                        id: reasoningText

                        width: parent.width

                        text: model.reasoning_content

                        wrapMode: Text.Wrap

                        color: "#AAAAAA"

                        font.pixelSize: contentText.font.pixelSize * 0.85

                        textFormat: Text.PlainText


                        visible: text.length > 0


                        height:
                            reasoningExpanded || !reasoningNeedCollapse
                            ? implicitHeight
                            : formatter.get('max_content_height')


                        clip: true
                    }



                    Text {

                        id: contentText

                        width: parent.width

                        text: model.content

                        wrapMode: Text.Wrap

                        color: "#FFFFFF"

                        textFormat: Text.MarkdownText


                        visible: text.length > 0


                        height:
                            model.role === "assistant"
                            || contentExpanded
                            || !contentNeedCollapse
                            ? implicitHeight
                            : formatter.get('max_content_height')


                        clip: true
                    }
                }
            }
        }
    }



    // 输入区域

    Item {

    id: input_area

    height: 170   // 120输入区 + 50提示区


    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: parent.bottom



    Rectangle {

        anchors.fill: parent

        color: "#202020"

    }



    TextArea {

        id: input_text


        anchors.left: parent.left
        anchors.right: send_button.left
        anchors.top: parent.top

        height: 120


        anchors.margins: 8


        placeholderText: "输入消息..."


        wrapMode: TextArea.Wrap


        background: Rectangle {

            radius: 6

            color: "#303030"

        }



        Keys.onPressed: function(event) {

            if(event.key === Qt.Key_Return
                    && event.modifiers &
                    Qt.ControlModifier
                    && event.modifiers &
                    Qt.ShiftModifier)
            {
                send_button.clicked()
                event.accepted = true
            }

            else if(event.key === Qt.Key_Return
                    && event.modifiers &
                    Qt.ShiftModifier)
            {
                insertPlainText("\n")
                event.accepted = true
            }

            else if(event.key === Qt.Key_Return
                    && event.modifiers &
                    Qt.ControlModifier)
            {
                insertPlainText("\n")
                event.accepted = true
            }

            else if(event.key === Qt.Key_Return)
            {
                send_button.clicked()
                event.accepted = true
            }
        }
    }



    Button {

        id: send_button


        width: 80
        height: 120


        anchors.right: parent.right
        anchors.top: parent.top

        anchors.margins: 8


        text: "发送"


        onClicked: backend.send_button_pressed(input_text.text)
    }



    // 底部提示区域

    Item {

        anchors.left: parent.left
        anchors.right: parent.right

        anchors.top: input_text.bottom

        height: 50



        Label {

            anchors.centerIn: parent


            text: "Ilina 也会犯错，请核查重要信息"


            color: "#888888"


            font.pixelSize: 13


        }
    }
}
}