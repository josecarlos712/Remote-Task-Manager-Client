# -*- coding: utf-8 -*-
"""Build config/programs.json from Desktop .lnk shortcuts."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "config" / "programs.json"

PS = r"""
$sh = New-Object -ComObject WScript.Shell
$paths = @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('CommonDesktopDirectory'))
$results = New-Object System.Collections.Generic.List[object]
foreach ($dir in $paths) {
  Get-ChildItem -LiteralPath $dir -Filter *.lnk -ErrorAction SilentlyContinue | ForEach-Object {
    $sc = $sh.CreateShortcut($_.FullName)
    $results.Add([pscustomobject]@{
      Name = $_.BaseName
      Target = $sc.TargetPath
      Args = $sc.Arguments
      WorkDir = $sc.WorkingDirectory
    }) | Out-Null
  }
}
$results | ConvertTo-Json -Depth 3 -Compress
"""


def slug(name: str) -> str:
    name = name.replace("\ufffd", "u").replace("\u00b5", "u").replace("\u03bc", "u")
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip()).strip("_").lower()
    return s or "program"


def main() -> None:
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; " + PS,
        ],
        capture_output=True,
        check=True,
    )
    raw = completed.stdout.decode("utf-8", errors="replace")
    items = json.loads(raw)
    if isinstance(items, dict):
        items = [items]

    used = set()
    programs = []
    for it in items:
        target = (it.get("Target") or "").strip()
        if not target:
            continue
        title = it.get("Name") or Path(target).stem
        if "Torrent" in title and not title[0].isalnum():
            title = "uTorrent"
        name = slug(title)
        base = name
        i = 2
        while name in used:
            name = f"{base}_{i}"
            i += 1
        used.add(name)
        ext = Path(target).suffix.lower()
        exists = Path(target).exists()
        available = exists and ext in (".exe", ".bat", ".cmd")
        programs.append(
            {
                "name": name,
                "title": title,
                "description": "Acceso directo: " + Path(target).name,
                "path": target,
                "args": (it.get("Args") or "").strip(),
                "work_dir": (it.get("WorkDir") or "").strip(),
                "available": available,
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(programs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote %s programs to %s" % (len(programs), OUT))
    for p in programs:
        flag = "OK" if p["available"] else "MISS"
        print("  [%s] %s -> %s" % (flag, p["title"], p["path"]))


if __name__ == "__main__":
    main()
