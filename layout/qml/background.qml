import QtQuick

Item {
    anchors.fill: parent

    // --- 分支一：有背景图时 ---
    Image {
        id: _bg_source
        anchors.fill: parent
        source: formatter.background_images !== undefined
            ? "file:///" + formatter.background_images
            : ""
        visible: formatter.background_images !== undefined
        fillMode: Image.PreserveAspectCrop
    }

    // 径向渐变遮罩：中心透明 → 边缘黑色
    Canvas {
        id: radialVignette
        anchors.fill: parent
        visible: formatter.background_images !== undefined
        onPaint: {
            var ctx = getContext("2d")
            var cx = width / 2
            var cy = height / 2
            var radius = Math.max(width, height) / 2
            var gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius)
            gradient.addColorStop(0, formatter.background_filter_color)
            gradient.addColorStop(1, formatter.window_background_color)
            ctx.fillStyle = gradient
            ctx.fillRect(0, 0, width, height)
        }
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
    }

    // --- 分支二：无背景图时 ---
    Rectangle {
        anchors.fill: parent
        color: formatter.window_background_color
        visible: formatter.background_images === undefined
    }
}
