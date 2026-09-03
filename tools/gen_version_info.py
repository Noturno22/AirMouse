import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

import appinfo as ai

VER = tuple(int(x) for x in ai.APP_VERSION.split(".")) + (0,)

v = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=VER,
        prodvers=VER,
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040904B0",
                    [
                        StringStruct("CompanyName", ai.APP_COMPANY),
                        StringStruct("FileDescription", ai.APP_DESCRIPTION),
                        StringStruct("FileVersion", ai.APP_VERSION),
                        StringStruct("InternalName", ai.APP_EXE_NAME),
                        StringStruct("LegalCopyright", ai.APP_COPYRIGHT),
                        StringStruct("OriginalFilename", ai.APP_EXE_NAME + ".exe"),
                        StringStruct("ProductName", ai.APP_NAME),
                        StringStruct("ProductVersion", ai.APP_VERSION),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [1033, 1200])]),
    ],
)

with open("version_info.txt", "w", encoding="utf-8") as fh:
    fh.write(str(v))

print("version_info.txt written")
