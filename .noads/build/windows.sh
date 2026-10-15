#!/usr/bin/env bash
set -euo pipefail
export PATH="/c/hostedtoolcache/windows/go/$(ls /c/hostedtoolcache/windows/go | sort -V | tail -n1)/x64/bin:$PATH"

export CGO_ENABLED=1
export GOOS=windows
export GOARCH=amd64
export CC=x86_64-w64-mingw32-gcc

which go
go version
gcc --version

# Version info + manifest resource: a bare stripped Go exe scores high on AV heuristics.
PANEL_VERSION=$(tr -d '[:space:]' < internal/config/version)
go run github.com/tc-hib/go-winres@v0.3.3 make --arch amd64 \
  --product-version "$PANEL_VERSION" --file-version "$PANEL_VERSION"

# Stamp the commit into per-commit (dev channel) builds only.
LDFLAGS="-w -s"
if false; then
  LDFLAGS="$LDFLAGS -X github.com/mhsanaei/3x-ui/v3/internal/config.buildCommit=${GITHUB_SHA:0:8} -X github.com/mhsanaei/3x-ui/v3/internal/config.buildDate=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
fi
go build -buildvcs=true -ldflags "$LDFLAGS" -o xui-release.exe -v .
