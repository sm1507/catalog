# Catalog project
Build a movie catalog with a sqlite database using the flask web frame, sqlalchemy to access the database, and Google login API for authenication to the application.  

This is the start of a movie catalog, listing movie categories on the left (ie. Romance, Action, Comedy Movies) where you filter all movies within each category by clicking on the Category name. Screen shot examples are below.

## Setup of the Vagrant and execute of the database initialization.
The Catalog application is ran within an Ubuntu virtual server.  Procedures below require the setup of Vagrant first, load of the sqlite database, and execute of the
setup of Vagrant first, load of the PSQL database, and then execute the `movie_catalog.py` script to start the Movie application & webserver.

### Setup Vagrant
1. Download Vagrant and install
2. Download Virtual Box and install
3. Execute `vagrant up` to start the virtual server
4. Execute `vagrant ssh` to login to the virtual instance

### Setup sqlite database with initial movie data
1. Execute `moviedb_init.py` to create and initialize the moviedb database with a few initial movies.  Additional movies can be added once the application is running.

2. 'moviedb_init.py' will destroy any previously created movie tables so run only once to create the movie database.

### Execute application and webserver startup
1. Login to vagrant server

2. Execute `movie_catalog.py`

3. Open web browser to `http://localhost:5000` to access the Movie Catalog application.

4. JSON objects are presented at `http://localhost:5000/category/JSON` and `http://localhost:5000/movies/JSON`

## Expected Output

<object data="examplepictures.pdf" type="application/pdf" width="700px" height="700px">
    <embed src="examplepictures.pdf">
        <p>This browser does not support PDFs. Please download the PDF to view it: <a href="examplepictures.pdf">Download PDF</a>.</p>
    </embed>
</object>
