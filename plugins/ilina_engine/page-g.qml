import QtQuick
import QtQuick.Controls

Item {
    anchors.fill: parent

    ListView {
        anchors.fill: parent
        model: ilina_message_list_model
        spacing: 4
        clip: true

        delegate: Item {
            width: ListView.view.width
            property bool reasoningExpanded: false
            property bool contentExpanded: false
            property bool reasoningNeedCollapse: reasoningText.implicitHeight > 400
            property bool contentNeedCollapse: contentText.implicitHeight > 600

            implicitHeight: messageContainer.height + 24

            Rectangle {
                id: messageContainer

                width: parent.width - 48
                x: 24

                height: messageColumn.implicitHeight + 32

                radius: 18

                color: model.role === "assistant"
                       ? "#18FFFFFF"
                       : "#10182030"

                border.width: 1
                border.color: "#20FFFFFF"

                Column {
                    id: messageColumn

                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top

                    anchors.margins: 16

                    spacing: 12

                    Row {
                        width: parent.width
                        height: roleText.height

                        spacing: 12

                        Rectangle {
                            height: roleText.height + 8
                            width: roleText.width + 20
                            radius: 12

                            color: model.role === "assistant"
                                   ? "#406080FF"
                                   : "#30404040"

                            Text {
                                id: roleText

                                anchors.centerIn: parent

                                text: model.role

                                font.family: "Maple Mono NF CN"
                                font.pixelSize: 12
                                font.bold: true

                                color: model.role_normal_color

                                textFormat: Text.PlainText
                            }
                        }

                        Row {
                            spacing: 8

                            visible: reasoningNeedCollapse || (contentNeedCollapse && model.role !== "assistant")

                            Button {
                                visible: reasoningNeedCollapse

                                text: reasoningExpanded
                                      ? "收起思维"
                                      : "展开思维"

                                padding: 6

                                background: Rectangle {
                                    radius: 10
                                    color: parent.hovered
                                           ? "#30FFFFFF"
                                           : "transparent"
                                }

                                contentItem: Text {
                                    text: parent.text

                                    color: "#BFFFFFFF"

                                    font.pixelSize: 13
                                }

                                onClicked: reasoningExpanded = !reasoningExpanded
                            }

                            Button {
                                visible: contentNeedCollapse && model.role !== "assistant"

                                text: contentExpanded
                                      ? "收起正文"
                                      : "展开正文"

                                padding: 6

                                background: Rectangle {
                                    radius: 10
                                    color: parent.hovered
                                           ? "#30FFFFFF"
                                           : "transparent"
                                }

                                contentItem: Text {
                                    text: parent.text

                                    color: "#BFFFFFFF"

                                    font.pixelSize: 13
                                }

                                onClicked: contentExpanded = !contentExpanded
                            }
                        }
                    }

                    Rectangle {
                        width: parent.width
                        height: 1
                        color: "#20FFFFFF"
                    }

                    Text {
                        id: reasoningText

                        width: parent.width

                        text: model.reasoning_content

                        wrapMode: Text.Wrap

                        visible: text.length > 0

                        color: "#A0FFFFFF"

                        font.pixelSize: contentText.font.pixelSize * 0.85

                        textFormat: Text.PlainText

                        height: reasoningExpanded || !reasoningNeedCollapse
                                ? implicitHeight
                                : 160

                        clip: true
                    }

                    Text {
                        id: contentText

                        width: parent.width

                        text: model.content

                        wrapMode: Text.Wrap

                        color: "#FFFFFF"

                        font.pixelSize: 12

                        textFormat: Text.MarkdownText

                        height: model.role === "assistant"
                                || contentExpanded
                                || !contentNeedCollapse
                                ? implicitHeight
                                : 300

                        clip: true
                    }
                }
            }
        }
    }
}