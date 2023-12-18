from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from dotenv import dotenv_values

# secrets
secrets = dotenv_values(".env")

MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"


# Movie rating form
class EditMovieRating(FlaskForm):
    rating = StringField(label="Your rating out of 10 e.g. 7.5")
    review = StringField(label="Your review")
    submit = SubmitField(label="Done")


# Add movie form
class AddMovie(FlaskForm):
    movie_title = StringField(label="Movie title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


app = Flask(__name__)
app.config["SECRET_KEY"] = secrets["SECRET_KEY"]
Bootstrap5(app)

# Movie Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fav-movies.db"

db = SQLAlchemy()
db.init_app(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    image_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f"<Movie {self.title}>"


# with app.app_context():
#     db.create_all()


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    # all() converts ScalarResult to lists
    all_movies = result.scalars().all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit_rating():
    form = EditMovieRating()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=form, movie=movie)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    movie_form = AddMovie()
    if movie_form.validate_on_submit():
        tmdb_url = f"https://api.themoviedb.org/3/search/movie?query={movie_form.movie_title.data}&include_adult=true&language=en-US&page=1"
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJmMTY2YWY2ZmJjODEyMjQ2N2Q2NDA0MTMwNDdjMmViMyIsInN1YiI6IjY1NWEwNGI0YjU0MDAyMTRkMDcwNDNlNCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.jlbFq1jktUGaMHLpsZwxXLva2YhUgZAp3yaRgoZcyHw",
        }
        response = requests.get(tmdb_url, headers=headers)
        response.raise_for_status()
        movies = response.json()["results"]
        return render_template("select.html", movies=movies)
    return render_template("add.html", form=movie_form)


@app.route("/find")
def find_movie():
    movie_id = request.args.get("id")
    if movie_id:
        id_url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJmMTY2YWY2ZmJjODEyMjQ2N2Q2NDA0MTMwNDdjMmViMyIsInN1YiI6IjY1NWEwNGI0YjU0MDAyMTRkMDcwNDNlNCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.jlbFq1jktUGaMHLpsZwxXLva2YhUgZAp3yaRgoZcyHw",
        }
        response = requests.get(id_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            image_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"],
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit_rating", id=new_movie.id))
    return render_template(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
