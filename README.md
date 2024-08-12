# PostGIS H3 Data

## Create virtual environment using poetry as below:
### Start fresh
poetry new postgis-h3<br>
poetry add geopandas psycopg2 sqlalchemy geoalchemy2 shapely osmnx ipykernel tqdm

### Using pyproject.toml
poetry install

### Open Shell with this environment
poetry shell

## Crate PostGIS and PGAdmin dockers using docker compose file
### Start Dockers
docker compose up -d

### End Dockers
docker compose down

## Create PostGIS Docker with H3 Extension
### Pull any postgis docker image
docker pull postgis/postgis:15-master

### Let's run a demo container where we can install h3 extension
docker run -it --name postgis-h3 -e POSTGRES_PASSWORD=postgres postgis/postgis:15-master

### shell access into the docker
docker exec -it -u root postgis-h3 bash

### Install the dependencies
apt update<br>
apt install -y pip libpq-dev postgresql-server-dev-15<br>
pip install pgxnclient cmake

### Install the extension
pgxn install h3

### Remove the dev dependencies
pip uninstall pgxnclient cmake<br>
apt purge -y libpq-dev postgresql-server-dev-15 pip<br>
exit

### Commit container changes to image, stop container and delete it
docker commit postgis-h3 postgis-h3<br>
docker stop postgis-h3<br>
docker rm postgis-h3<br>
