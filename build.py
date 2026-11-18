#!/usr/bin/env python3
"""Copia padrao/ para dentro de cada skill e gera os .zip para o app do Claude.

Uso:
  python3 build.py           sincroniza skills/*/padrao/ e gera dist/<skill>.zip
  python3 build.py --check   só verifica se as cópias estão iguais à fonte (sai com 1 se não estiverem)

padrao/ é a fonte única. As cópias em skills/*/padrao/ são geradas e versionadas,
porque o plugin do Claude Code instala direto do GitHub. Nunca edite as cópias.
"""
import argparse
import shutil
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PADRAO = RAIZ / "padrao"
SKILLS = RAIZ / "skills"
DIST = RAIZ / "dist"
MARCADOR = "GERADO-NAO-EDITE.md"
LIXO = {"__pycache__", ".DS_Store"}


def ignorado(caminho: Path) -> bool:
    return any(parte in LIXO for parte in caminho.parts) or caminho.suffix == ".pyc"


def arquivos(base: Path) -> dict[str, bytes]:
    return {
        p.relative_to(base).as_posix(): p.read_bytes()
        for p in sorted(base.rglob("*"))
        if p.is_file() and not ignorado(p.relative_to(base)) and p.name != MARCADOR
    }


def skills() -> list[Path]:
    return sorted(p for p in SKILLS.iterdir() if (p / "SKILL.md").is_file())


def sincronizar(skill: Path) -> None:
    destino = skill / "padrao"
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(PADRAO, destino, ignore=shutil.ignore_patterns(*LIXO, "*.pyc"))
    (destino / MARCADOR).write_text(
        "# Cópia gerada\n\nEsta pasta é gerada por `build.py` a partir de `padrao/` na raiz do repositório.\n"
        "Não edite aqui: edite `padrao/` e rode `python3 build.py`.\n",
        encoding="utf-8",
    )


def empacotar(skill: Path) -> Path:
    DIST.mkdir(exist_ok=True)
    zip_path = DIST / f"{skill.name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(skill.rglob("*")):
            if p.is_file() and not ignorado(p.relative_to(skill)):
                z.write(p, Path(skill.name) / p.relative_to(skill))
    return zip_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="só verifica, não altera nada")
    args = parser.parse_args()

    fonte = arquivos(PADRAO)
    if args.check:
        divergentes = [s.name for s in skills() if not (s / "padrao").is_dir() or arquivos(s / "padrao") != fonte]
        if divergentes:
            print(f"Cópias desatualizadas em: {', '.join(divergentes)}. Rode: python3 build.py")
            return 1
        print(f"OK: {len(skills())} skills com padrao/ igual à fonte ({len(fonte)} arquivos).")
        return 0

    for skill in skills():
        sincronizar(skill)
        print(f"{skill.name}: padrao/ sincronizado, {empacotar(skill).relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
