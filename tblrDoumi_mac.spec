# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['tblrDoumi/main.py'],
    pathex=[],
    binaries=[],
    datas=[('btnicon.png', '.'), ('templates', 'templates')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='tblrDoumi',  # 'main' 대신 앱 이름으로 변경
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,     # GUI 앱이므로 콘솔 창 끔
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # EXE 단의 icon은 생략하거나 문자열로 지정 (BUNDLE 단에서 처리되므로 생략 가능)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='tblrDoumi', # 'main' 대신 앱 이름으로 변경
)

app = BUNDLE(
    coll,
    name='tblrDoumi.app',
    icon='tblrdoumi.icns', # macOS 앱 번들 아이콘 유효성 보장
    bundle_identifier='org.ktug.tblrDoumi', # 식별자 등록 (권장)
    info_plist={
        'CFBundleDevelopmentRegion': 'ko_KR',
        'CFBundleLocalizations': ['ko', 'en'],
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': '3.9.10', # 앱 버전 추가 (선택)
    },
)