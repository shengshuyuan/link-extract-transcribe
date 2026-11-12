"""Build the WorkBuddy skill archive using an explicit allowlist."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
FILES = ["SKILL.md", "README.md", "requirements-web.txt",
         "references/wechat.md", "references/media.md", "references/note-workflow.md",
         "scripts/wxfetch.py", "scripts/transcript.py", "scripts/doctor.py",
         "scripts/setup_web.py", "scripts/web_runtime.py"]

def main():
    target = ROOT / "dist/link-extract-transcribe-workbuddy.zip"
    target.parent.mkdir(exist_ok=True)
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for name in FILES:
            path = ROOT / name
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"Expected regular file: {name}")
            archive.write(path, "link-extract-transcribe/" + name)
    print(target)

if __name__ == "__main__":
    main()
