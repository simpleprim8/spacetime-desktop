#!/usr/bin/env python3
"""Build a user-owned Omarchy background clone from the installed version."""
import json
import hashlib
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
SOURCE = Path(__import__('os').environ.get('OMARCHY_PATH', '/usr/share/omarchy')) / 'shell/plugins/background'
PAYLOAD = ROOT / 'plugin'

def main():
    if PAYLOAD.exists():
        shutil.rmtree(PAYLOAD)
    PAYLOAD.mkdir()
    subprocess.run(['/usr/lib/qt6/bin/qsb', '--qt6', '-o', str(ROOT / 'spacetime.frag.qsb'), str(ROOT / 'spacetime.frag')], check=True)
    subprocess.run(['/usr/lib/qt6/bin/qsb', '--qt6', '--batchable', '-o', str(ROOT / 'spacetime.vert.qsb'), str(ROOT / 'spacetime.vert')], check=True)
    text = (SOURCE / 'Background.qml').read_text()
    anchor = '  id: root\n'
    assert text.count(anchor) == 1
    text = text.replace(anchor, anchor + '''
  property bool spacetimeEnabled: true
  readonly property string spacetimeRevision: "4.0.0"
  property bool spacetimePaused: false
  property real spacetimeSeconds: 0
  property real spacetimeSpeed: 1
  property double spacetimeLastTick: Date.now()

  Timer {
    interval: 16
    running: root.spacetimeEnabled && !root.spacetimePaused
    repeat: true
    onTriggered: {
      let now = Date.now()
      root.spacetimeSeconds = (root.spacetimeSeconds + Math.min(0.25, (now-root.spacetimeLastTick)/1000)*root.spacetimeSpeed) % 450
      root.spacetimeLastTick = now
    }
  }

  IpcHandler {
    target: "spacetime"
    function pause(): void { root.spacetimePaused = true }
    function resume(): void {
      root.spacetimeLastTick = Date.now()
      root.spacetimeEnabled = true
      root.spacetimePaused = false
    }
    function stop(): void { root.spacetimeEnabled = false }
    function seek(seconds: real): void {
      root.spacetimeSeconds = ((seconds % 450) + 450) % 450
    }
    function speed(value: real): void { root.spacetimeSpeed = Math.max(0.1, Math.min(value, 30)) }
    function status(): string {
      return JSON.stringify({version: root.spacetimeRevision, enabled: root.spacetimeEnabled, paused: root.spacetimePaused,
        seconds: root.spacetimeSeconds, perspective: Math.floor(root.spacetimeSeconds/90)+1,
        speed: root.spacetimeSpeed, duration: 450})
    }
  }
''')
    anchor = '  function setBackground(path, instant) {\n'
    assert text.count(anchor) == 1
    text = text.replace(anchor, anchor + '    if (displayedBackground && path !== currentBackground) spacetimeEnabled = false\n')
    anchor = '      MouseArea {\n'
    assert text.count(anchor) == 1
    text = text.replace(anchor, '''      Spacetime {
        anchors.fill: parent
        visible: root.spacetimeEnabled
        phase: root.spacetimeSeconds
      }

''' + anchor)
    (PAYLOAD / 'Background.qml').write_text(text)
    manifest = json.loads((SOURCE / 'manifest.json').read_text())
    manifest.update(id='spacetime.background', name='Spacetime Desktop', author='simpleprim8',
                    description='Single transparent point vortex with five cinematic camera routes.', version='4.0.0')
    manifest['omarchy'] = {'clonedFrom': 'omarchy.background'}
    (PAYLOAD / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    for name in ['Spacetime.qml', 'spacetime.frag', 'spacetime.frag.qsb', 'spacetime.vert', 'spacetime.vert.qsb']:
        shutil.copy2(ROOT / name, PAYLOAD / name)
    # A new URL for new shader bytes prevents the running Qt renderer from
    # retaining an earlier shader when this plugin is updated in place.
    effect = (PAYLOAD / 'Spacetime.qml').read_text()
    for stage in ['vert', 'frag']:
        shader = ROOT / ('spacetime.' + stage + '.qsb')
        shader_name = 'spacetime-' + hashlib.sha256(shader.read_bytes()).hexdigest()[:12] + '.' + stage + '.qsb'
        shutil.copy2(shader, PAYLOAD / shader_name)
        effect = effect.replace(shader.name, shader_name)
    (PAYLOAD / 'Spacetime.qml').write_text(effect)
    print(PAYLOAD)

if __name__ == '__main__':
    main()
