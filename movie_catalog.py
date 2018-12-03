from flask import Flask, render_template, request, redirect, jsonify, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Movie
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import random
import string

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Movie Catalog"


engine = create_engine('sqlite:///movie.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    """Webpage for Google login"""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Google login API"""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Get authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '  # noqa
    print "done!"
    return output


def createUser(login_session):
    """Add Google user to User table in moviedb"""
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserID(email):
    """Get userid for Google API"""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    """Logout with Google API"""
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Execute HTTP GET request to revoke current token.
    url = "https://accounts.google.com/o/oauth2/revoke?token={}".format(access_token)  # noqa
    h = httplib2.Http()
    result = h.request(url, "GET")[0]

    if result["status"] == '200':
        del login_session["username"]
        del login_session["access_token"]
        del login_session["email"]
        del login_session["picture"]
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
                    json.dumps(' Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# All movies
@app.route('/')
@app.route('/category/')
def showCategory():
    """Main page with Categories and Top 5 Movies"""
    category = session.query(Category).all()
    movies = session.query(Movie).order_by('id desc').limit(5)
    return render_template('home.html', category=category, movies=movies)


@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    """Edit Category name and update in database"""
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedCategory.user_id != login_session['user_id']:
        return "<script>function alertFunction() {alert('You are not authorized to edit this Category');}</script><body onload='alertFunction()'>"  # noqa
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            session.commit()
            return redirect(url_for('showCategory'))
    else:
        return render_template('editCategory.html', category=editedCategory)


@app.route('/category/add/', methods=['GET', 'POST'])
def addCategory():
    """Add a new Movie Category"""
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        addCategory = Category(
                name=request.form['name'], user_id=login_session['user_id'])
        session.add(addCategory)
        session.commit()
        return redirect(url_for('showCategory'))
    else:
        return render_template('addCategory.html')


@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    """Delete a Movie Category"""
    deletedCategory = session.query(Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if deletedCategory.user_id != login_session['user_id']:
        return "<script>function alertFunction() {alert('You are not authorized to edit this Category');}</script><body onload='alertFunction()'>"  # noqa
    if request.method == 'POST':
        session.delete(deletedCategory)
        session.commit()
        return redirect(url_for('showCategory'))    # recheck
    else:
        return render_template('deleteCategory.html', category=deletedCategory)


@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/movies/')
def showMovies(category_id):
    """Movie webpage listing all movies within the Category"""
    category = session.query(Category).filter_by(id=category_id).one()
    movies = session.query(Movie).filter_by(category_id=category_id).all()
    return render_template('showMovies.html', movies=movies, category=category)


@app.route('/category/<int:category_id>/movies/add', methods=['GET', 'POST'])
def addMovie(category_id):
    """Add Movie to database under the Category"""
    category = session.query(Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if category.user_id != login_session['user_id']:
        return "<script>function alertFunction() {alert('You are not authorized to edit this Category');}</script><body onload='alertFunction()'>"  # noqa
    if request.method == 'POST':
        addMovie = Movie(title=request.form['title'],
                         description=request.form['description'],
                         category_id=category_id)
        session.add(addMovie)
        session.commit()

        return redirect(url_for('showMovies', category_id=category_id))
    else:
        return render_template('addMovie.html', category=category,
                               user=login_session['username'])


@app.route('/category/<int:category_id>/movies/<int:movie_id>/edit',
           methods=['GET', 'POST'])
def editMovie(category_id, movie_id):
    """Edit Movie name and movie description"""
    category = session.query(Category).filter_by(id=category_id).one()
    editedMovie = session.query(Movie).filter_by(id=movie_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if category.user_id != login_session['user_id']:
        return "<script>function alertFunction() {alert('You are not authorized to edit this Category');}</script><body onload='alertFunction()'>"  # noqa
    if request.method == 'POST':
        if request.form['title']:
            editedMovie.title = request.form['title']
        if request.form['description']:
            editedMovie.description = request.form['description']
        session.add(editedMovie)
        session.commit()
        return redirect(url_for('showMovies', category_id=category_id))
    else:
        return render_template('editMovie.html',
                               category=category, movie=editedMovie)


@app.route('/category/<int:category_id>/movies/<int:movie_id>/delete',
           methods=['GET', 'POST'])
def deleteMovie(category_id, movie_id):
    """Delete Movie from database"""
    category = session.query(Category).filter_by(id=category_id).one()
    deletedMovie = session.query(Movie).filter_by(id=movie_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if category.user_id != login_session['user_id']:
        return "<script>function alertFunction() {alert('You are not authorized to edit this Category');}</script><body onload='alertFunction()'>"  # noqa
    if request.method == 'POST':
        session.delete(deletedMovie)
        session.commit()
        return redirect(url_for('showMovies', category_id=category_id))
    else:
        return render_template('deleteMovie.html', category=category,
                               movie=deletedMovie)


# JSONify
@app.route('/category/JSON')
def showCategoryJSON():
    """JSON for Category table top level"""
    category = session.query(Category).all()
    return jsonify(category=[i.serialize for i in category])


@app.route('/movies/JSON')
def showMoviesJSON():
    """JSON for Movies table"""
    movies = session.query(Movie).all()
    return jsonify(movies=[i.serialize for i in movies])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
