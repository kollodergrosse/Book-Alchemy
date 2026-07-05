from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
from data_models import db, Author, Book
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

app = Flask(__name__)

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"

db.init_app(app)
app.secret_key = os.urandom(24)


with app.app_context():
    db.create_all()


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    """
    Handle the addition of a new author to the database.

    GET: Renders the form to add a new author.
    POST: Extracts and validates form data (name, birthdate, date of death).
          Attempts to save the new author to the database.

    Returns:
        str: Rendered HTML template or a redirect response.
    """
    if request.method == 'POST':
        name = request.form.get('name')
        birth_date_raw = request.form.get('birthdate')
        date_of_death_raw = request.form.get('date_of_death')

        if not name:
            flash('Name of the author is needed', 'danger')
            return render_template('add_author.html')

        birth_date = None
        if birth_date_raw:
            try:
                birth_date = datetime.strptime(birth_date_raw, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid birth date format. Please use YYYY-MM-DD.', 'danger')
                return render_template('add_author.html')

        date_of_death = None
        if date_of_death_raw:
            try:
                date_of_death = datetime.strptime(date_of_death_raw, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date of death format. Please use YYYY-MM-DD.', 'danger')
                return render_template('add_author.html')

        try:
            new_author = Author(
                name=name,
                birth_date=birth_date,
                date_of_death=date_of_death
            )
            db.session.add(new_author)
            db.session.commit()

            flash(f'Author "{name}" was added successfully!', 'success')
            return redirect(url_for('home'))

        except ValueError as e:
            db.session.rollback()
            flash(f'Validation Error: {str(e)}', 'danger')

        except IntegrityError:
            db.session.rollback()
            flash('Database integrity error. This author might already exist.', 'danger')

        except OperationalError:
            db.session.rollback()
            flash('Database operational error. Please try again later.', 'danger')

        except SQLAlchemyError:
            db.session.rollback()
            flash('A database error occurred while saving the author.', 'danger')

    return render_template('add_author.html')


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    """
    Handle the creation and storage of a new book.

    GET: Fetches all existing authors and renders the book creation form.
    POST: Processes form data (title, ISBN, publication year, author ID),
          validates required fields, and links the book to an author.

    Returns:
        str: Rendered HTML template or a redirect response to the home page.
    """
    if request.method == 'POST':
        title = request.form.get('title')
        isbn = request.form.get('isbn')
        publication_year = request.form.get('publication_year')
        author_id = request.form.get('author_id')

        if not title or not isbn or not author_id:
            flash('Title, ISBN and author needed!', 'danger')
            authors = Author.query.all()
            return render_template('add_book.html', authors=authors)

        publication_year = int(publication_year) if publication_year else None
        author_id = int(author_id)

        try:
            publication_year = int(publication_year) if publication_year else None
            author_id = int(author_id)

        except ValueError:
            flash('Invalid input: Publication year and Author must be numbers.', 'danger')

        try:
            new_book = Book(
                title=title,
                isbn=isbn,
                publication_year=publication_year,
                author_id=author_id
            )
            db.session.add(new_book)
            db.session.commit()

            flash(f'The book "{title}" has been added successfully!', 'success')
            return redirect(url_for('home'))

        except ValueError as e:
            db.session.rollback()
            flash(f'Validation Error: {str(e)}', 'danger')

        except IntegrityError:
            db.session.rollback()
            flash('Error: A book with this ISBN already exists in the database.', 'danger')

        except OperationalError:
            db.session.rollback()
            flash('Database is temporarily unavailable. Please try again.', 'danger')

        except SQLAlchemyError:
            db.session.rollback()
            flash('An unexpected database error occurred while saving the book.', 'danger')

    authors = Author.query.all()

    return render_template('add_book.html', authors=authors)


@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    """
    Delete a specific book from the database by its ID.

    If the deleted book was the only book associated with its author,
    the author is automatically removed from the database as well.

    Args:
        book_id (int): The unique identifier of the book to be deleted.
    Returns:
        A redirect to the home page.
    """
    book = Book.query.get_or_404(book_id)

    book_title = book.title
    author_id = book.author_id

    try:
        db.session.delete(book)
        other_books_count = Book.query.filter(Book.author_id == author_id, Book.id != book_id).count()

        author_info_msg = ""
        if other_books_count == 0:
            author = Author.query.get(author_id)
            if author:
                db.session.delete(author)
                author_info_msg = f"(The author {author.name} has been deleted as well.)"

        db.session.commit()
        flash(f'The book "{book_title}" was deleted successfully!{author_info_msg}', 'success')

    except IntegrityError:
        db.session.rollback()
        flash('Could not delete data due to dependency constraints in the database.', 'danger')
    except OperationalError:
        db.session.rollback()
        flash('Database connection error. Action aborted.', 'danger')
    except SQLAlchemyError:
        db.session.rollback()
        flash('An error occurred within the database layer during deletion.', 'danger')

    return redirect(url_for('home'))


@app.route('/')
def home():
    """
    Render the homepage containing the list of books.

    Supports optional query parameters for searching books by title and sorting
    the list by title, author name, or publication year.

    Query Parameters:
        sort (str): Field to sort by ('title', 'author', 'year'). Defaults to 'title'.
        search (str): Substring to filter book titles. Defaults to ''.

    Returns:
        str: Rendered HTML template with filtered and sorted book objects.
    """
    sort_by = request.args.get('sort', 'title')
    search_query = request.args.get('search', '').strip()
    query = Book.query.options(db.joinedload(Book.author))

    if search_query:
        query = query.filter(Book.title.ilike(f'%{search_query}%'))

    if sort_by == 'author':
        all_books = query.join(Author).order_by(Author.name.asc()).all()

    elif sort_by == 'year':
        all_books = query.order_by(Book.publication_year.desc()).all()

    else:
        all_books = query.order_by(Book.title.asc()).all()
        sort_by = 'title'

    return render_template('home.html', books=all_books, current_sort=sort_by, search_query=search_query)


if __name__ == '__main__':
    app.run(port=5002, debug=True)