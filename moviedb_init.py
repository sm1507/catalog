from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Movie

# Connect & Bind to DB with sqlite
engine = create_engine('sqlite:///movie.db')
Base.metadata.bind = engine

# Create DBSession instance with database
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Delete all old data before reinitializing with new data
session.query(Category).delete()
session.query(Movie).delete()
session.query(User).delete()

# Create users
user1 = User(name="Steve McCallum",
             email="stephenmccallum@gmail.com",
             picture="http://blah.com")

session.add(user1)
session.commit()

user2 = User(name="George Washington",
             email="Georgie@gmail.com",
             picture="http://blahblah.com")

session.add(user2)
session.commit()

user3 = User(name="Martha Washington",
             email="Martha@gmail.com",
             picture="http://blahblah.com")

session.add(user3)
session.commit()

user4 = User(name="James Bond",
             email="James@gmail.com",
             picture="http://bond007.com")

session.add(user4)
session.commit()

# Create Movie categories
category1 = Category(name="Action")

session.add(category1)
session.commit()

category2 = Category(name="Comedy")

session.add(category2)
session.commit()

category3 = Category(name="Drama")

session.add(category3)
session.commit()

category4 = Category(name="Romance")

session.add(category4)
session.commit()


# Add movies for each category
movie1 = Movie(title="Casino Royale",
                  description="IMDB: Armed with a license to kill, Secret Agent James Bond sets out on his first mission as 007, and must defeat a private banker to terrorists in a high stakes game of poker at Casino Royale, Montenegro, but things are not what they seem. ",  # noqa
                  category=category1,
                  user=user1)

session.add(movie1)
session.commit()

movie2 = Movie(title="Skyfall",
                  description="Bond's loyalty to M is tested when her past comes back to haunt her. When MI6 comes under attack, 007 must track down and destroy the threat, no matter how personal the cost. ",  # noqa
                  category=category1,
                  user=user1)

session.add(movie2)
session.commit()

movie3 = Movie(title="Gone with the Wind",
                  description="A manipulative woman and a roguish man conduct a turbulent romance during the American Civil War and Reconstruction periods.",  # noqa
                  category=category4,
                  user=user3)

session.add(movie3)
session.commit()

movie4 = Movie(title="Airplane",
                  description="A man afraid to fly must ensure that a plane lands safely after the pilots become sick.",  # noqa
                  category=category2,
                  user=user2)

session.add(movie4)
session.commit()

movie5 = Movie(title="Mad, Mad, Mad World",
                  description="The dying words of a thief spark a madcap cross-country rush to find some treasure. ",  # noqa
                  category=category2,
                  user=user1)

session.add(movie5)
session.commit()

movie6 = Movie(title="12 Angry Men",
                  description="A jury holdout attempts to prevent a miscarriage of justice by forcing his colleagues to reconsider the evidence. ",  # noqa
                  category=category3,
                  user=user1)

session.add(movie6)
session.commit()
