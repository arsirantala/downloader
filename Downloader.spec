# -*- mode: python -*-

block_cipher = None


a = Analysis(['DLer.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=['Tkinter', 'configparser', 'requests', 'pkgutil'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries + [('Highwind.ico', 'Highwind.ico', 'DATA')],
          a.zipfiles,
          a.datas,
          name='Downloader',
          debug=False,
          strip=False,
          upx=False,
          console=False , version='version.txt', icon='Highwind.ico')
