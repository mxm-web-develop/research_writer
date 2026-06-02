#!/usr/bin/env bash
# Install research_writer from GitHub into Cursor + Claude Code global skill paths.
# Do NOT rsync from a local dev checkout — develop in your fork, push to GitHub, then run this script.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/mxm-web-develop/research_writer.git}"
BRANCH="${BRANCH:-main}"
CANONICAL_DIR="${CANONICAL_DIR:-${HOME}/.agents/skills/research_writer}"
CURSOR_LINK="${CURSOR_LINK:-${HOME}/.cursor/skills/research_writer}"
CLAUDE_LINK="${CLAUDE_LINK:-${HOME}/.claude/skills/research_writer}"

echo "research_writer install"
echo "  repo:    ${REPO_URL}"
echo "  branch:  ${BRANCH}"
echo "  target:  ${CANONICAL_DIR}"
echo

if [[ -d "${CANONICAL_DIR}/.git" ]]; then
  echo "Updating existing clone..."
  git -C "${CANONICAL_DIR}" fetch origin
  git -C "${CANONICAL_DIR}" checkout "${BRANCH}"
  git -C "${CANONICAL_DIR}" reset --hard "origin/${BRANCH}"
  git -C "${CANONICAL_DIR}" clean -fd
else
  echo "Cloning fresh copy..."
  mkdir -p "$(dirname "${CANONICAL_DIR}")"
  rm -rf "${CANONICAL_DIR}"
  git clone --branch "${BRANCH}" --depth 1 "${REPO_URL}" "${CANONICAL_DIR}"
fi

mkdir -p "$(dirname "${CURSOR_LINK}")" "$(dirname "${CLAUDE_LINK}")"
ln -sfn "${CANONICAL_DIR}" "${CURSOR_LINK}"
ln -sfn "${CANONICAL_DIR}" "${CLAUDE_LINK}"

echo
echo "Linked:"
echo "  Cursor:      ${CURSOR_LINK} -> ${CANONICAL_DIR}"
echo "  Claude Code: ${CLAUDE_LINK} -> ${CANONICAL_DIR}"
echo

python3 "${CANONICAL_DIR}/scripts/bootstrap.py" --install
python3 "${CANONICAL_DIR}/scripts/doctor.py"

echo
echo "Installed version:"
grep '^version:' "${CANONICAL_DIR}/SKILL.md" || true
echo
echo "Done. Use scripts from:"
echo "  python3 ${CANONICAL_DIR}/scripts/build_bundle.py --input report.md --outdir output --sources sources.md"
