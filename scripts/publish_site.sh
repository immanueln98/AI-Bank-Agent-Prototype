#!/usr/bin/env bash
# Publish the pitch site to GitHub Pages.
#
# Builds docs/index.html and docs/pricing.html from their local-only sources
# (docs/pitch-site.html, docs/pricing-site.html — gitignored, never on main),
# then commits BOTH pages to the gh-pages branch and pushes. Always publish
# through this script: hand-copying a single file onto gh-pages drops the
# other page from the site.
#
#   bash scripts/publish_site.sh ["commit message"]
set -euo pipefail

msg="${1:-Publish pitch site}"
root=$(git rev-parse --show-toplevel)
docs="$root/docs"

for src in pitch-site.html pricing-site.html; do
  if [[ ! -f "$docs/$src" ]]; then
    echo "error: $docs/$src not found (pitch sources are local-only; see .gitignore)" >&2
    exit 1
  fi
done

# The sources are written without a document skeleton; wrap them for hosting.
wrap() {
  {
    printf '<!doctype html>\n<html lang="en">\n<head><meta charset="utf-8"></head>\n<body>\n'
    cat "$1"
    printf '\n</body>\n</html>\n'
  } >"$2"
}
wrap "$docs/pitch-site.html" "$docs/index.html"
wrap "$docs/pricing-site.html" "$docs/pricing.html"

tmp=$(mktemp -d)
ghp="$tmp/gh-pages"
cleanup() {
  git -C "$root" worktree remove --force "$ghp" 2>/dev/null || true
  rm -rf "$tmp"
}
trap cleanup EXIT

git -C "$root" fetch origin gh-pages
git -C "$root" worktree add "$ghp" origin/gh-pages >/dev/null
cp "$docs/index.html" "$docs/pricing.html" "$ghp/"

cd "$ghp"
git add index.html pricing.html
if git diff --cached --quiet; then
  echo "gh-pages already up to date — nothing to publish"
  exit 0
fi
git -c core.hooksPath=/dev/null commit -m "$msg"
git push origin HEAD:gh-pages
echo "published: https://immanueln98.github.io/AI-Bank-Agent-Prototype/"
