from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Author(db.Model):
    """
    Represents an author within the library database.
    Attributes:
        id (int): Unique identifier and primary key for the author.
        name (str): The full name of the author. Cannot be null.
        birth_date (datetime.date): The birth date of the author. Optional.
        date_of_death (datetime.date): The date of death of the author. Optional.
        books (list): Dynamic back-reference list of Book objects written by this author.
    """
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    birth_date = db.Column(db.Date, nullable=True)
    date_of_death = db.Column(db.Date, nullable=True)

    def __repr__(self):
        """
        Return a string representation of the Author instance.

        Returns:
            str: A formatted string containing the author's name.
        """
        return f"<Author {self.name}>"


class Book(db.Model):
    """
    Represents a book within the library database.

    Attributes:
        id (int): Unique identifier and primary key for the book.
        isbn (str): Unique International Standard Book Number. Cannot be null.
        title (str): The title of the book. Cannot be null.
        publication_year (int): The year the book was published. Optional.
        author_id (int): Foreign key referencing the ID of the author who wrote the book.
        author (Author): Relationship object linking directly to the associated Author model.
    """
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    publication_year = db.Column(db.Integer, nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False)
    author = db.relationship('Author', backref='books')

    def __repr__(self):
        """
        Return a string representation of the Book instance.

        Returns:
            str: A formatted string containing the book's title.
        """
        return f"<Book {self.title}>"