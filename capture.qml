import QtQuick
import QtQuick.Window
import Quickshell

ShellRoot {
    id: root
    property var times: JSON.parse(Quickshell.env("SPACETIME_TIMES") || "[0,18,36,46,57,63,68,72,78,84,89.999,90,126,147,216,237,306,327,396,417,449.999,450]")
    property int index: 0
    Window {
        visible: true
        width: 960; height: 540
        title: "Spacetime — checking camera paths"
        color: "black"
        // Keep exports at the desktop's 16:9 aspect even when the window
        // manager tiles this temporary verification window into a narrow area.
        Spacetime {
            id: effect
            width: Number(Quickshell.env("SPACETIME_WIDTH") || "960")
            height: width * 9 / 16
            anchors.centerIn: parent
            phase: root.times[root.index]
        }
        Timer {
            id: captureTimer
            interval: Number(Quickshell.env("SPACETIME_INTERVAL") || "500"); running: true
            onTriggered: effect.grabToImage(function(result) {
                let filename = Quickshell.env("SPACETIME_DIR") + "/check-" + String(root.index).padStart(2,"0") + ".png"
                if (!result.saveToFile(filename)) console.error("Capture failed: " + filename)
                console.log("FRAME " + root.index + " TIME " + root.times[root.index])
                if (root.index + 1 >= root.times.length) Qt.quit()
                else { root.index++; captureTimer.restart() }
            })
        }
    }
}
