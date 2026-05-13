# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
mutagen_imports = collect_submodules('mutagen')

a = Analysis(
    [os.path.expanduser('~/Documents/Tagr/src/tagr.py')],
    pathex=[os.path.expanduser('~/Documents/Tagr/src')],
    binaries=[
        # ffmpeg statique embarqué
        (os.path.expanduser('~/Documents/Tagr/assets/ffmpeg'), '.'),
    ],
    datas=[],
    hiddenimports=[
        'mutagen','mutagen.mp3','mutagen.flac','mutagen.mp4',
        'mutagen.id3','mutagen.oggvorbis','mutagen._util',
        'PIL','PIL.Image','PIL.ImageOps','PIL.ImageFilter',
        'PyQt6','PyQt6.QtWidgets','PyQt6.QtCore','PyQt6.QtGui','PyQt6.sip',
        'urllib','urllib.request','urllib.parse',
        'json','threading','subprocess','struct','wave','shutil','csv','pathlib',
        'yt_dlp',
    ] + mutagen_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter','matplotlib','numpy','scipy','pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='Tagr',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False, upx_exclude=[], name='Tagr',
)

app = BUNDLE(
    coll,
    name='Tagr.app',
    icon=os.path.expanduser('~/Documents/Tagr/assets/Tagr.icns'),
    bundle_identifier='com.tagr.app',
    version='1.3.1',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleName': 'Tagr',
        'CFBundleDisplayName': 'Tagr',
        'CFBundleVersion': '1.3.1',
        'CFBundleShortVersionString': '1.3.1',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '12.0',
        'NSRequiresAquaSystemAppearance': False,
        'NSMicrophoneUsageDescription': 'Tagr ne necessite pas le micro.',
        'com.apple.security.app-sandbox': False,
    },
)
