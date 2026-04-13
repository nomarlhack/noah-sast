#!/usr/bin/env bash
# Noah SAST — 제거 스크립트

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

INSTALL_DIR="$HOME/.claude/skills/noah-8719"

echo ""
printf "${BOLD}${CYAN}Noah SAST 제거${NC}\n"
echo ""

if [ ! -d "$INSTALL_DIR" ]; then
  printf "${YELLOW}[WARN]${NC}  설치된 Noah SAST를 찾을 수 없습니다: $INSTALL_DIR\n"
  exit 0
fi

SCANNER_COUNT=$(ls -d "$INSTALL_DIR/skills/scan/scanners"/*-scanner 2>/dev/null | wc -l | tr -d ' ')
printf "  설치 경로: ${BOLD}$INSTALL_DIR${NC}\n"
printf "  스캐너 수: ${BOLD}${SCANNER_COUNT}개${NC}\n"
echo ""
printf "${RED}정말 제거하시겠습니까? 이 작업은 되돌릴 수 없습니다.${NC} [y/N] "
read -r answer

case "$answer" in
  [yY]|[yY][eE][sS])
    rm -rf "$INSTALL_DIR"
    # 백업도 제거할지 확인
    BACKUPS=$(ls -d "${INSTALL_DIR}.backup."* 2>/dev/null || true)
    if [ -n "$BACKUPS" ]; then
      echo ""
      printf "${YELLOW}백업 디렉토리가 있습니다:${NC}\n"
      echo "$BACKUPS"
      printf "백업도 함께 제거하시겠습니까? [y/N] "
      read -r answer2
      case "$answer2" in
        [yY]|[yY][eE][sS])
          rm -rf "${INSTALL_DIR}.backup."*
          printf "${GREEN}[OK]${NC}    백업 제거 완료\n"
          ;;
        *)
          printf "${CYAN}[INFO]${NC}  백업을 유지합니다.\n"
          ;;
      esac
    fi
    echo ""
    printf "${GREEN}[OK]${NC}    Noah SAST가 제거되었습니다.\n"
    echo ""
    ;;
  *)
    printf "${CYAN}[INFO]${NC}  제거를 취소합니다.\n"
    ;;
esac
