# Pull any postgis docker image
FROM postgis/postgis:15-master

# Update
RUN apt-get update

# Install the dependencies
RUN apt install -y pip libpq-dev postgresql-server-dev-15
RUN pip install pgxnclient cmake

# Install the extension
RUN pgxn install h3

# Remove the dev dependencies
RUN pip uninstall -y pgxnclient cmake
RUN apt purge -y libpq-dev postgresql-server-dev-15 pip

# Clean up
RUN apt-get -y autoremove && apt-get -y clean

# Update the PATH variable
ENV PATH="${PATH}:/usr/lib/postgresql/15/bin"
