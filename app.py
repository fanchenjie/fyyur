#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import traceback
import dateutil.parser
import babel
import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import distinct
from sqlalchemy.sql.expression import *
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable = False)
    genres = db.Column(db.String(120), nullable = True)
    city = db.Column(db.String(120), nullable = False)
    state = db.Column(db.String(120), nullable = False)
    address = db.Column(db.String(120), nullable = False)
    phone = db.Column(db.String(120), nullable = False)
    image_link = db.Column(db.String(500), nullable = True)
    facebook_link = db.Column(db.String(120), nullable = True)
    website_link = db.Column(db.String(120), nullable = True)
    seeking_talent = db.Column(db.Boolean, nullable = True)
    seeking_description = db.Column(db.String(120), nullable = True)
    shows = db.relationship('Show', backref = 'venue', cascade='all,delete', lazy = True)
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable = False)
    city = db.Column(db.String(120), nullable = False)
    state = db.Column(db.String(120), nullable = False)
    phone = db.Column(db.String(120), nullable = False)
    genres = db.Column(db.String(120), nullable = True)
    image_link = db.Column(db.String(500), nullable = True)
    facebook_link = db.Column(db.String(120), nullable = True)
    website_link = db.Column(db.String(120), nullable = True)
    seeking_venue = db.Column(db.Boolean, nullable = True)
    seeking_description = db.Column(db.String(120), nullable = True)
    shows = db.relationship('Show', backref = 'artist', lazy = True)
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
   __tablename__ = 'Show'

   id = db.Column(db.Integer, primary_key=True)
   start_time = db.Column(db.DateTime, nullable = False)
   venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable = False)
   artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable =False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[]
  cities = db.session.query(distinct(tuple_(Venue.city, Venue.state))).all()

  for c in cities:
    city,state = c[0][1:-1].split(',')
    
    if city[0] == '"':
      city = city[1:-1]
         
    city_dict = {}
    city_dict['city'] = city
    city_dict['state'] = state
    venues = []
    query = Venue.query.filter_by(state = state, city = city).all()
    for q in query:
      v_dict = {}
      v_dict['id'] = q.id
      v_dict['name'] = q.name
      v_dict['num_upcoming_shows'] = Show.query.filter_by(venue_id = q.id).count()
      venues.append(v_dict)
    city_dict['venues'] = venues
    data.append(city_dict)

  
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response = {}
  search_term = request.form.get('search_term','')
  search = '%{}%'.format(search_term)
  query = Venue.query.filter(Venue.name.ilike(search)).all()
  response['count'] = Venue.query.filter(Venue.name.ilike(search)).count()
  data=[]
  for q in query:
    result = {}
    result['id'] = q.id
    result['name'] = q.name
    result['num_upcoming_shows'] = Show.query.filter_by(venue_id = q.id).filter(Show.start_time > datetime.now()).count()
    data.append(result)
  response['data'] = data
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  data = {}
  query = Venue.query.get(venue_id)
  data['id'] = query.id
  data['name'] = query.name
  data['genres'] = query.genres[1:-1].split(',')
  data['address'] = query.address
  data['city'] = query.city
  data['state'] = query.state
  data['phone'] = query.phone
  data['website'] = query.website_link
  data['facebook_link'] = query.facebook_link
  data['seeking_talent'] = query.seeking_talent
  data['seeking_description'] = query.seeking_description
  data['image_link'] = query.image_link
  data['past_shows_count'] = Show.query.filter_by(venue_id = venue_id).filter( Show.start_time < datetime.now()).count()
  data['upcoming_shows_count'] = Show.query.filter_by(venue_id = venue_id).filter(Show.start_time > datetime.now()).count()

  data['past_shows'] = []
  data['upcoming_shows'] = []
  past_shows = Show.query.filter_by(venue_id = venue_id).filter(Show.start_time < datetime.now()).all()
  for s in past_shows:
    show_dict = {}
    show_dict['artist_id'] = s.artist_id
    show_dict['artist_name'] = Artist.query.get(s.artist_id).name
    show_dict['artist_image_link'] = Artist.query.get(s.artist_id).image_link
    show_dict['start_time'] = s.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    data['past_shows'].append(show_dict)
  upcoming_shows = Show.query.filter_by(venue_id = venue_id).filter(Show.start_time > datetime.now()).all()
  for s in upcoming_shows:
    show_dict = {}
    show_dict['artist_id'] = s.artist_id
    show_dict['artist_name'] = Artist.query.get(s.artist_id).name
    show_dict['artist_image_link'] = Artist.query.get(s.artist_id).image_link
    show_dict['start_time'] = s.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    data['upcoming_shows'].append(show_dict)


  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  
  try:
    name = request.form['name']
    address = request.form['address']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    venue = Venue(name = name, address = address, city = city, state = state, phone = phone, genres = genres, facebook_link = facebook_link )
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('Error! Venue ' + request.form['name'] + ' could not be listed!')
  finally:
    db.session.close()

  # on successful db insert, flash success
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  try:
    venue = Venue.query.filter_by(id=venue_id).first()
    name = venue.name
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + name +' was successfully deleted!')
  except:
    db.session.rollback()
    traceback.print_exc()
    flash('Error! Venue could not be deleted!')
    return jsonify({'success': False})
  finally:
    db.session.close()
  return jsonify({ 'success': True })

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data=Artist.query.all()

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response = {}
  search_term = request.form.get('search_term','')
  search = '%{}%'.format(search_term)
  query = Artist.query.filter(Artist.name.ilike(search)).all()
  response['count'] = Artist.query.filter(Artist.name.ilike(search)).count()
  data=[]
  for q in query:
    result = {}
    result['id'] = q.id
    result['name'] = q.name
    result['num_upcoming_shows'] = Show.query.filter_by(artist_id = q.id).filter(Show.start_time > datetime.now()).count()
    data.append(result)
  response['data'] = data


  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  data = {}
  query = Artist.query.get(artist_id)
  data['id'] = query.id
  data['name'] = query.name
  genres = []
  genres = query.genres[1:-1].split(',')
  data['genres'] = genres
  data['city'] = query.city
  data['state'] = query.state
  data['phone'] = query.phone
  data['website'] = query.website_link
  data['facebook_link'] = query.facebook_link
  data['seeking_venue'] = query.seeking_venue
  data['seeking_description'] = query.seeking_description
  data['image_link'] = query.image_link
  data['past_shows_count'] = Show.query.filter_by(artist_id = artist_id).filter( Show.start_time < datetime.now()).count()
  data['upcoming_shows_count'] = Show.query.filter_by(artist_id= artist_id).filter(Show.start_time > datetime.now()).count()

  data['past_shows'] = []
  data['upcoming_shows'] = []
  past_shows = Show.query.filter_by(artist_id = artist_id).filter(Show.start_time < datetime.now()).all()
  for s in past_shows:
    show_dict = {}
    show_dict['venue_id'] = s.venue_id
    show_dict['venue_name'] = Venue.query.get(s.venue_id).name
    show_dict['venue_image_link'] = Venue.query.get(s.venue_id).image_link
    show_dict['start_time'] = s.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    data['past_shows'].append(show_dict)
  upcoming_shows = Show.query.filter_by(artist_id = artist_id).filter(Show.start_time > datetime.now()).all()
  for s in upcoming_shows:
    show_dict = {}
    show_dict['venue_id'] = s.venue_id
    show_dict['venue_name'] = Venue.query.get(s.venue_id).name
    show_dict['venue_image_link'] = Venue.query.get(s.venue_id).image_link
    show_dict['start_time'] = s.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    data['upcoming_shows'].append(show_dict)

  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    artist = Artist.query.get(artist_id)
    artist.name = name
    artist.city = city
    artist.state = state
    artist.phone = phone
    artist.genres = genres
    artist.facebook_link = facebook_link
    db.session.commit()
    flash('artist ' + request.form['name'] + ' are successfully edited!')
  except:
    db.session.rollback()
    flash('Error! artist ' + request.form['name'] + ' could not be edited!')
  finally:
    db.session.close()
  
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    venue = Venue.query.get(venue_id)
    venue.name = name
    venue.city = city
    venue.state = state
    venue.phone = phone
    venue.genres = genres
    venue.facebook_link = facebook_link
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' are successfully edited!')
  except:
    db.session.rollback()
    flash('Error! Venue ' + request.form['name'] + ' could not be edited!')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    artist = Artist(name = name, city = city, state = state, phone = phone, genres = genres, facebook_link = facebook_link)
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('Error! Artist ' + request.form['name'] + ' could not be listed!')
  finally:
    db.session.close()

  # on successful db insert, flash success
  #flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  query = Show.query.all()
  for q in query:
    show_dict = {}
    show_dict['venue_id'] = q.venue_id
    show_dict['venue_name'] = Venue.query.get(q.venue_id).name
    show_dict['artist_id'] = q.artist_id
    show_dict['artist_name'] = Artist.query.get(q.artist_id).name
    show_dict['artist_image_link'] = Artist.query.get(q.artist_id).image_link
    show_dict['start_time'] = q.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    data.append(show_dict)

  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    show = Show(artist_id = artist_id, venue_id = venue_id, start_time = start_time)
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('Show could not be successfully listed!')
  finally:
    db.session.close()
  # on successful db insert, flash success
  #flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
