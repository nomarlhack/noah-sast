#!/usr/bin/env python3
"""cache_manager.py — noah-sast grep 인덱스 캐시 관리.

프로젝트 루트의 .noah-sast-cache/ 디렉토리에 grep 인덱스를 영속화하여,
코드 변경이 없을 때 grep 전체 재실행을 건너뛸 수 있도록 한다.

Usage:
    # 캐시 상태 확인 (증분 가능 여부)
    python3 cache_manager.py status <PROJECT_ROOT>

    # 증분 대상 파일 목록 산출
    python3 cache_manager.py diff <PROJECT_ROOT>

    # 증분 결과를 기존 캐시에 병합
    python3 cache_manager.py merge <PROJECT_ROOT> <INCREMENTAL_INDEX_DIR>

    # 전체 인덱스를 캐시에 저장 (초기 또는 풀 스캔 후)
    python3 cache_manager.py save <PROJECT_ROOT> <FULL_INDEX_DIR>

Exit codes:
    status: 0=캐시 유효(증분 가능), 1=캐시 없음/무효(풀 스캔 필요)
    diff:   0=변경 파일 있음(stdout 출력), 1=변경 없음(인덱스 재사용)
    merge:  0=성공
    save:   0=성공
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

CACHE_DIR_NAME = ".noah-sast-cache"
MANIFEST_NAME = "manifest.json"
INDEX_SUBDIR = "grep-index"


def get_cache_dir(project_root):
    return Path(project_root) / CACHE_DIR_NAME


def get_manifest_path(project_root):
    return get_cache_dir(project_root) / MANIFEST_NAME


def get_cached_index_dir(project_root):
    return get_cache_dir(project_root) / INDEX_SUBDIR


def get_git_head_commit(project_root):
    """현재 HEAD의 commit hash를 반환."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root, capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def get_changed_files(project_root, since_commit):
    """since_commit 이후 변경된 파일 목록을 반환."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", since_commit, "HEAD"],
            cwd=project_root, capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
            return files
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def cmd_status(project_root):
    """캐시 상태를 확인한다. 0=증분 가능, 1=풀 스캔 필요."""
    manifest_path = get_manifest_path(project_root)
    if not manifest_path.exists():
        print("CACHE_MISS: manifest 없음 — 풀 스캔 필요")
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cached_commit = manifest.get("commit")
    if not cached_commit:
        print("CACHE_MISS: commit hash 없음 — 풀 스캔 필요")
        return 1

    current_commit = get_git_head_commit(project_root)
    if not current_commit:
        print("CACHE_MISS: git repo 아님 — 풀 스캔 필요")
        return 1

    if cached_commit == current_commit:
        print(f"CACHE_HIT: 변경 없음 (commit {cached_commit[:8]})")
        # 인덱스 디렉토리 경로 출력 (메인 에이전트가 사용)
        print(f"INDEX_DIR: {get_cached_index_dir(project_root)}")
        return 0

    # 변경이 있지만 캐시는 유효 → 증분 가능
    changed = get_changed_files(project_root, cached_commit)
    if changed is None:
        print("CACHE_MISS: git diff 실패 — 풀 스캔 필요")
        return 1

    if not changed:
        # commit은 다르지만 파일 변경 없음 (merge commit 등)
        print(f"CACHE_HIT: 파일 변경 없음 (commit {cached_commit[:8]} → {current_commit[:8]})")
        print(f"INDEX_DIR: {get_cached_index_dir(project_root)}")
        return 0

    print(f"CACHE_STALE: {len(changed)}개 파일 변경 — 증분 가능")
    print(f"INDEX_DIR: {get_cached_index_dir(project_root)}")
    return 0


def cmd_diff(project_root):
    """증분 대상 파일 목록을 stdout에 출력. 1=변경 없음."""
    manifest_path = get_manifest_path(project_root)
    if not manifest_path.exists():
        print("ERROR: manifest 없음", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cached_commit = manifest.get("commit")
    if not cached_commit:
        return 1

    changed = get_changed_files(project_root, cached_commit)
    if changed is None or not changed:
        return 1

    for f in changed:
        print(f)
    return 0


def cmd_merge(project_root, incremental_dir):
    """증분 인덱스를 기존 캐시에 병합."""
    cache_index = get_cached_index_dir(project_root)
    inc_path = Path(incremental_dir)

    if not cache_index.exists() or not inc_path.exists():
        print("ERROR: 캐시 또는 증분 디렉토리 없음", file=sys.stderr)
        return 1

    merged_count = 0
    for inc_file in inc_path.glob("*.json"):
        scanner_name = inc_file.stem
        cache_file = cache_index / inc_file.name

        # 증분 인덱스 읽기
        inc_data = json.loads(inc_file.read_text(encoding="utf-8"))

        if cache_file.exists():
            # 기존 캐시 읽기
            cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
            # 패턴별 병합 (증분이 우선, 중복 제거)
            for pattern, locations in inc_data.items():
                existing = set(cache_data.get(pattern, []))
                existing.update(locations)
                cache_data[pattern] = sorted(existing)
            merged = cache_data
        else:
            merged = inc_data

        cache_file.write_text(
            json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        merged_count += 1

    # manifest 업데이트
    current_commit = get_git_head_commit(project_root)
    manifest = {
        "commit": current_commit,
        "scanner_count": merged_count,
    }
    get_manifest_path(project_root).write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    print(f"MERGE_OK: {merged_count}개 스캐너 인덱스 병합 완료 (commit {current_commit[:8] if current_commit else 'unknown'})")
    return 0


def cmd_save(project_root, full_index_dir):
    """풀 스캔 인덱스를 캐시에 저장."""
    cache_dir = get_cache_dir(project_root)
    cache_index = get_cached_index_dir(project_root)

    # 캐시 디렉토리 초기화
    cache_dir.mkdir(parents=True, exist_ok=True)
    if cache_index.exists():
        shutil.rmtree(cache_index)
    cache_index.mkdir(parents=True, exist_ok=True)

    # 인덱스 파일 복사
    src = Path(full_index_dir)
    copied = 0
    for f in src.glob("*.json"):
        shutil.copy2(f, cache_index / f.name)
        copied += 1

    # manifest 생성
    current_commit = get_git_head_commit(project_root)
    manifest = {
        "commit": current_commit,
        "scanner_count": copied,
    }
    get_manifest_path(project_root).write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    print(f"SAVE_OK: {copied}개 스캐너 인덱스 저장 (commit {current_commit[:8] if current_commit else 'unknown'})")
    print(f"INDEX_DIR: {cache_index}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: cache_manager.py <status|diff|merge|save> <PROJECT_ROOT> [INDEX_DIR]")
        sys.exit(1)

    cmd = sys.argv[1]
    project_root = sys.argv[2]

    if cmd == "status":
        sys.exit(cmd_status(project_root))
    elif cmd == "diff":
        sys.exit(cmd_diff(project_root))
    elif cmd == "merge":
        if len(sys.argv) < 4:
            print("Usage: cache_manager.py merge <PROJECT_ROOT> <INCREMENTAL_INDEX_DIR>")
            sys.exit(1)
        sys.exit(cmd_merge(project_root, sys.argv[3]))
    elif cmd == "save":
        if len(sys.argv) < 4:
            print("Usage: cache_manager.py save <PROJECT_ROOT> <FULL_INDEX_DIR>")
            sys.exit(1)
        sys.exit(cmd_save(project_root, sys.argv[3]))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
