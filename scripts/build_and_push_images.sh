VERSION=$(poetry version -s)
echo "Current version: $VERSION"

docker build -t clementcome/velib_base:v$VERSION -t clementcome/velib_base:latest  -f docker/Dockerfile.base .
docker build -t clementcome/velib:v$VERSION -t clementcome/velib:latest -f docker/Dockerfile .


docker image push --all-tags clementcome/velib_base
docker image push --all-tags clementcome/velib
