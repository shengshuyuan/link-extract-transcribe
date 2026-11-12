"""Build the WorkBuddy skill archive using an explicit allowlist."""
from pathlib import Path
import re
from urllib.parse import quote
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/shengshuyuan/link-extract-transcribe"
FILES = ["SKILL.md", "README.md", "requirements-web.txt",
         "references/wechat.md", "references/media.md", "references/note-workflow.md",
         "scripts/wxfetch.py", "scripts/transcript.py", "scripts/doctor.py",
         "scripts/setup_web.py", "scripts/web_runtime.py"]


def package_readme(text):
    """Keep bundled references local; link repository-only resources to GitHub."""
    def replace(match):
        label, target = match.groups()
        if target.startswith(("https://", "http://", "#")) or target in FILES:
            return match.group(0)
        path = ROOT / target
        if not path.exists():
            raise ValueError(f"README link target missing: {target}")
        route = "tree" if path.is_dir() else "blob"
        if target.endswith(".zip"):
            return f"[{label}]({REPOSITORY}/raw/refs/heads/main/{quote(target)})"
        return f"[{label}]({REPOSITORY}/{route}/main/{quote(target)})"
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace, text)


def build_archive(target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Validate all inputs before opening the output archive.
    for name in FILES:
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Expected regular file: {name}")
    readme = package_readme((ROOT / "README.md").read_text(encoding="utf-8"))
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for name in FILES:
            if name == "README.md":
                archive.writestr("link-extract-transcribe/" + name, readme)
            else:
                archive.write(ROOT / name, "link-extract-transcribe/" + name)
    return target


def main():
    print(build_archive(ROOT / "dist/link-extract-transcribe-workbuddy.zip"))


if __name__ == "__main__":
    main()
