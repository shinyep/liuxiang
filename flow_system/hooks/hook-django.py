# Custom Django hook - collect all Django files
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('django')
